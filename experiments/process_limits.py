"""RESOURCE-01 manual Windows process-tree caps; no simulation or service."""
import argparse
import ctypes
from ctypes import wintypes as wt
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

OUTPUT_LIMIT = 1024 * 1024


@dataclass(frozen=True)
class Limits:
    memory_bytes: int = 128 * 1024**2
    cpu_seconds: float = 5
    processes: int = 3
    wall_seconds: float = 5

    def validate(self):
        if type(self.memory_bytes) is not int or self.memory_bytes < 32 * 1024**2:
            raise ValueError('Memory cap must be an integer of at least 32 MiB')
        if type(self.processes) is not int or not 2 <= self.processes <= 64:
            raise ValueError('Process cap must include bootstrap and worker (2..64)')
        for value in (self.cpu_seconds, self.wall_seconds):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('Finite positive CPU and wall caps required')
        if self.cpu_seconds * 10_000_000 < 1 or self.cpu_seconds * 10_000_000 >= 2**63:
            raise ValueError('CPU cap outside Windows timer range')
        if self.memory_bytes > sys.maxsize:
            raise ValueError('Memory cap outside native size range')


class BasicLimits(ctypes.Structure):
    _fields_ = [('process_cpu', ctypes.c_longlong), ('job_cpu', ctypes.c_longlong),
                ('flags', wt.DWORD), ('min_working_set', ctypes.c_size_t),
                ('max_working_set', ctypes.c_size_t), ('active_processes', wt.DWORD),
                ('affinity', ctypes.c_size_t), ('priority', wt.DWORD), ('scheduling', wt.DWORD)]


class IOCounts(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in
                ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic', BasicLimits), ('io', IOCounts),
                ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                ('peak_process_memory', ctypes.c_size_t), ('peak_job_memory', ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_longlong) for name in ('user', 'kernel', 'period_user', 'period_kernel')] + [
        (name, wt.DWORD) for name in ('page_faults', 'total_processes', 'active_processes', 'terminated_processes')]


def kernel():
    if os.name != 'nt':
        raise OSError('Windows Job Object enforcement only; no portable fallback')
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    definitions = {
        'CreateJobObjectW': ([ctypes.c_void_p, wt.LPCWSTR], wt.HANDLE),
        'SetInformationJobObject': ([wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD], wt.BOOL),
        'QueryInformationJobObject': ([wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.c_void_p], wt.BOOL),
        'AssignProcessToJobObject': ([wt.HANDLE, wt.HANDLE], wt.BOOL),
        'TerminateJobObject': ([wt.HANDLE, wt.UINT], wt.BOOL),
        'CloseHandle': ([wt.HANDLE], wt.BOOL),
        'OpenProcess': ([wt.DWORD, wt.BOOL, wt.DWORD], wt.HANDLE),
        'WaitForSingleObject': ([wt.HANDLE, wt.DWORD], wt.DWORD)}
    for name, (args, result) in definitions.items():
        fn = getattr(k, name)
        fn.argtypes, fn.restype = args, result
    return k


def checked(ok):
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())


class Job:
    def __init__(self, limits):
        self.k = kernel()
        self.handle = self.k.CreateJobObjectW(None, None)
        checked(self.handle)
        try:
            setting = ExtendedLimits()
            # JOB_TIME | ACTIVE_PROCESS | JOB_MEMORY | KILL_ON_JOB_CLOSE.
            setting.basic.flags = 0x4 | 0x8 | 0x200 | 0x2000
            setting.basic.job_cpu = int(limits.cpu_seconds * 10_000_000)
            setting.basic.active_processes = limits.processes
            setting.job_memory = limits.memory_bytes
            checked(self.k.SetInformationJobObject(self.handle, 9, ctypes.byref(setting), ctypes.sizeof(setting)))
            action = wt.DWORD(0)  # JOB_OBJECT_TERMINATE_AT_END_OF_JOB.
            checked(self.k.SetInformationJobObject(self.handle, 6, ctypes.byref(action), ctypes.sizeof(action)))
            readback = self.usage()
            if (readback['configured_memory_bytes'] != limits.memory_bytes or
                    readback['configured_processes'] != limits.processes or
                    readback['configured_cpu_ticks'] != setting.basic.job_cpu or
                    readback['flags'] & setting.basic.flags != setting.basic.flags):
                raise RuntimeError('Job limit readback differs; refuse command')
        except BaseException:
            self.close()
            raise

    def assign(self, process):
        checked(self.k.AssignProcessToJobObject(self.handle, wt.HANDLE(int(process._handle))))

    def usage(self):
        accounting, limits = Accounting(), ExtendedLimits()
        checked(self.k.QueryInformationJobObject(self.handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None))
        checked(self.k.QueryInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits), None))
        return dict(user_cpu_seconds=accounting.user / 10_000_000,
                    windows_reported_peak_job_memory_bytes=limits.peak_job_memory,
                    configured_memory_bytes=limits.job_memory,
                    configured_processes=limits.basic.active_processes,
                    configured_cpu_ticks=limits.basic.job_cpu, flags=limits.basic.flags,
                    started_processes=accounting.total_processes,
                    active_before_close=accounting.active_processes)

    def terminate(self):
        checked(self.k.TerminateJobObject(self.handle, 124))

    def close(self):
        if self.handle:
            checked(self.k.CloseHandle(self.handle))
            self.handle = None


def process_exited(pid, timeout_ms=2000):
    """Independent OS check: a signaled handle or already absent process."""
    k = kernel()
    handle = k.OpenProcess(0x100000, False, pid)  # SYNCHRONIZE.
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER: PID no longer exists.
            return True
        raise ctypes.WinError(error)
    try:
        return k.WaitForSingleObject(handle, timeout_ms) == 0
    finally:
        checked(k.CloseHandle(handle))


def run(command, limits=Limits(), cwd=None):
    limits.validate()
    if not isinstance(command, (list, tuple)) or not command or any(not isinstance(s, str) or not s or '\x00' in s for s in command):
        raise ValueError('Explicit nonempty argument vector required')
    if os.name != 'nt':
        raise OSError('Windows only; command was not started')
    job, process, reader = Job(limits), None, None
    kept, counts = bytearray(), {'bytes': 0}
    def drain():
        while True:
            block = process.stdout.read(65536)
            if not block:
                return
            counts['bytes'] += len(block)
            kept.extend(block[:max(0, OUTPUT_LIMIT - len(kept))])
    started = time.monotonic()
    timed_out = False
    supervisor_cpu_stop = False
    try:
        # The known stdlib bootstrap uses the existing base interpreter directly.
        # Windows venv redirectors consume additional job process slots.
        bootstrap_python = getattr(sys, '_base_executable', sys.executable)
        bootstrap = [bootstrap_python, '-m', 'experiments.process_limits', '--bootstrap', json.dumps(list(command))]
        process = subprocess.Popen(bootstrap, cwd=cwd or Path(__file__).resolve().parents[1],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   close_fds=True, shell=False)
        # Known bootstrap cannot start command before this assignment succeeds.
        job.assign(process)
        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        process.stdin.write(b'go\n')
        process.stdin.close()
        while process.poll() is None:
            if job.usage()['user_cpu_seconds'] >= limits.cpu_seconds:
                supervisor_cpu_stop = True
                job.terminate()
                process.wait(timeout=5)
                break
            remaining = limits.wall_seconds - (time.monotonic() - started)
            if remaining <= 0:
                timed_out = True
                job.terminate()
                process.wait(timeout=5)
                break
            try:
                process.wait(timeout=min(0.01, remaining))
            except subprocess.TimeoutExpired:
                pass
        usage = job.usage()
        job.close()  # Kill residual descendants on normal exits too.
        reader.join(timeout=5)
        if reader.is_alive():
            raise RuntimeError('Output pipe stayed open after whole-job closure')
        return dict(schema='resource01-result-v1', platform='Windows', command=list(command),
                    bootstrap_python=bootstrap_python,
                    limits=vars(limits), exit_code=process.returncode, timed_out=timed_out,
                    supervisor_cpu_stop=supervisor_cpu_stop,
                    elapsed_seconds=time.monotonic()-started, usage=usage,
                    output=kept.decode('utf-8', errors='replace'),
                    output_bytes=counts['bytes'], retained_bytes=len(kept),
                    output_truncated=counts['bytes'] > len(kept), isolation_verified=False)
    finally:
        job.close()
        if process is not None:
            if process.poll() is None:
                process.terminate()  # Also covers an unassigned waiting bootstrap.
                process.wait(timeout=5)
            if reader is not None:
                reader.join(timeout=5)
            for stream in (process.stdin, process.stdout):
                if stream is not None:
                    stream.close()


def bootstrap(command):
    if sys.stdin.buffer.readline(8) != b'go\n':
        return 125
    return subprocess.call(command, stdin=subprocess.DEVNULL, shell=False, close_fds=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.bootstrap is None:
        parser.error('Import run() for an explicit manual bounded command; no service mode')
    raise SystemExit(bootstrap(json.loads(args.bootstrap)))
