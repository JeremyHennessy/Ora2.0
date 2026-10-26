"""One-shot Windows Job containment for this isolated, trusted finite census only."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


class Basic(C.Structure):
    _fields_ = [('process_time', C.c_longlong), ('job_time', C.c_longlong),
                ('flags', W.DWORD), ('min_ws', C.c_size_t), ('max_ws', C.c_size_t),
                ('active', W.DWORD), ('affinity', C.c_size_t),
                ('priority', W.DWORD), ('scheduling', W.DWORD)]


class IO(C.Structure):
    _fields_ = [(name, C.c_ulonglong) for name in ('reads', 'writes', 'other', 'readbytes', 'writebytes', 'otherbytes')]


class Extended(C.Structure):
    _fields_ = [('basic', Basic), ('io', IO), ('process_memory', C.c_size_t),
                ('job_memory', C.c_size_t), ('peak_process', C.c_size_t), ('peak_job', C.c_size_t)]


class Accounting(C.Structure):
    _fields_ = [(name, C.c_longlong) for name in ('user', 'kernel', 'period_user', 'period_kernel')] + [
        (name, W.DWORD) for name in ('faults', 'total_processes', 'active_processes', 'terminated')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    args.directory.mkdir(exist_ok=False)
    receipt = {'status': 'INCOMPLETE', 'wall_limit_seconds': 300, 'cpu_user_job_seconds': 120,
               'memory_job_bytes': 256 * 1024 * 1024, 'active_process_limit': 1,
               'output_observed_limit_bytes': 32 * 1024 * 1024,
               'output_limit_kind': 'trusted finite output, parent polled every0.05s; not hard disk quota',
               'scientific_population': False}
    receipt['wall_bound_kind'] = '290s cooperative stop; cleanup reserved to300s; final filesystem IO cooperative, no hard parent-wall guarantee'
    receipt['pre_assignment_work'] = 'Trusted Python stdlib bootstrap waits for GO before census import; not Job-charged'
    script = Path(__file__).with_name('census.py').resolve()
    receipt['source_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
    receipt['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [C.c_void_p, W.LPCWSTR]
    kernel.CreateJobObjectW.restype = W.HANDLE
    kernel.SetInformationJobObject.argtypes = [W.HANDLE, C.c_int, C.c_void_p, W.DWORD]
    kernel.QueryInformationJobObject.argtypes = [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p]
    kernel.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]
    kernel.TerminateJobObject.argtypes = [W.HANDLE, W.UINT]
    kernel.CloseHandle.argtypes = [W.HANDLE]
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise C.WinError(C.get_last_error())
    child = None
    assigned = False
    primary_error = None
    cleanup_errors = []
    try:
        limit = Extended()
        limit.basic.flags = 0x4 | 0x8 | 0x200 | 0x2000
        limit.basic.job_time = 120 * 10_000_000
        limit.basic.active = 1
        limit.job_memory = receipt['memory_job_bytes']
        if not kernel.SetInformationJobObject(job, 9, C.byref(limit), C.sizeof(limit)):
            raise C.WinError(C.get_last_error())
        actual = Extended()
        if not kernel.QueryInformationJobObject(job, 9, C.byref(actual), C.sizeof(actual), None):
            raise C.WinError(C.get_last_error())
        assert actual.basic.flags == limit.basic.flags
        assert actual.basic.job_time == limit.basic.job_time and actual.basic.active == 1
        assert actual.job_memory == limit.job_memory
        receipt['limits_read_back_exact'] = True
        output = args.directory.resolve() / 'census.json'
        bootstrap = "import sys,runpy; assert sys.stdin.readline()=='GO\\n'; p=sys.argv[1]; sys.argv=[p,'--output',sys.argv[2]]; runpy.run_path(p,run_name='__main__')"
        with (args.directory/'stdout.txt').open('xb') as stdout, (args.directory/'stderr.txt').open('xb') as stderr:
            child = subprocess.Popen([sys.executable, '-I', '-B', '-c', bootstrap, str(script), str(output)],
                stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.DETACHED_PROCESS)
            receipt['pid'] = child.pid
            if not kernel.AssignProcessToJobObject(job, W.HANDLE(int(child._handle))):
                raise C.WinError(C.get_last_error())
            assigned = True
            receipt['assigned_before_census_import'] = True
            child.stdin.write(b'GO\n'); child.stdin.close()
            while child.poll() is None:
                if time.monotonic() - start > 290:
                    raise TimeoutError('Complete attempt wall limit')
                if sum(p.stat().st_size for p in args.directory.iterdir() if p.is_file()) > receipt['output_observed_limit_bytes']:
                    raise RuntimeError('Output budget exceeded')
                time.sleep(0.05)
            receipt['exit_code'] = child.returncode
            if child.returncode != 0:
                raise RuntimeError('Census child failed; no retry')
            if sum(p.stat().st_size for p in args.directory.iterdir() if p.is_file()) > receipt['output_observed_limit_bytes']:
                raise RuntimeError('Final output budget exceeded')
            receipt['status'] = 'COMPLETED_NOT_SCIENTIFIC_ACCEPTANCE'
    except BaseException as exc:
        receipt['exception'] = repr(exc)
        primary_error = exc
    finally:
        def cleanup(label, action):
            try:
                action()
            except BaseException as exc:
                cleanup_errors.append({'step': label, 'error': repr(exc)})
        def checked(result):
            if not result:
                raise C.WinError(C.get_last_error())
        cleanup('terminate_job', lambda: checked(kernel.TerminateJobObject(job, 99)))
        if child is not None:
            if not assigned and child.poll() is None:
                cleanup('terminate_unassigned_bootstrap', child.kill)
            def reap():
                child.wait(timeout=max(0.1, min(10, 300 - (time.monotonic()-start))))
                receipt['owned_child_reaped'] = True
            cleanup('reap_child', reap)
        def query_limits():
            actual = Extended()
            checked(kernel.QueryInformationJobObject(job, 9, C.byref(actual), C.sizeof(actual), None))
            receipt['peak_job_committed_bytes'] = actual.peak_job
        cleanup('query_limits', query_limits)
        def query_accounting():
            accounting = Accounting()
            checked(kernel.QueryInformationJobObject(job, 1, C.byref(accounting), C.sizeof(accounting), None))
            receipt.update(job_user_cpu_seconds=accounting.user/10_000_000,
                job_kernel_cpu_seconds=accounting.kernel/10_000_000,
                job_active_processes_after_wait=accounting.active_processes,
                job_total_processes=accounting.total_processes)
            if accounting.active_processes != 0:
                raise RuntimeError('Job not empty')
        cleanup('query_accounting', query_accounting)
        def close():
            checked(kernel.CloseHandle(job))
            receipt['job_handle_closed'] = True
        cleanup('close_job', close)
        receipt['elapsed_wall_seconds'] = time.monotonic() - start
        receipt['closure_observed_within_300seconds'] = receipt['elapsed_wall_seconds'] <= 300
        def hash_outputs():
            receipt['files'] = {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                                for p in args.directory.iterdir() if p.is_file()}
        cleanup('hash_outputs', hash_outputs)
        receipt['cleanup_errors'] = cleanup_errors
        if cleanup_errors or not receipt['closure_observed_within_300seconds']:
            receipt['status'] = 'FAILED_CLEANUP_OR_WALL'
        with (args.directory/'native-receipt.json').open('x') as target:
            json.dump(receipt, target, indent=2)
    if primary_error is not None:
        raise primary_error
    if cleanup_errors or not receipt['closure_observed_within_300seconds']:
        raise RuntimeError('Cleanup failed; receipt retained')


if __name__ == '__main__':
    main()
