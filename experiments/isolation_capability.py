"""ISOLATION-01 explicit disposable Windows capability panel. No service mode."""
import argparse
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid
import zipfile

from experiments.process_limits import Job, checked, process_exited

ROOT = Path(__file__).resolve().parents[1]
FILES = ('experiments/isolation_capability.py', 'experiments/isolation_worker.py',
         'experiments/isolation_capability_audit.py', 'experiments/process_limits.py',
         'docs/ISOLATION-01-CONTRACT.md')
DISK_LIMIT = 256*1024**2


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


class Startup(c.Structure):
    _fields_ = [('cb', w.DWORD), ('reserved', w.LPWSTR), ('desktop', w.LPWSTR),
               ('title', w.LPWSTR)] + [(key, w.DWORD) for key in
               ('x', 'y', 'xsize', 'ysize', 'xchars', 'ychars', 'fill', 'flags')] + [
               ('show', w.WORD), ('reserved_size', w.WORD), ('reserved_bytes', c.c_void_p),
               ('stdin', w.HANDLE), ('stdout', w.HANDLE), ('stderr', w.HANDLE)]


class StartupEx(c.Structure):
    _fields_ = [('startup', Startup), ('attributes', c.c_void_p)]


class Process(c.Structure):
    _fields_ = [('process', w.HANDLE), ('thread', w.HANDLE), ('pid', w.DWORD), ('tid', w.DWORD)]


class Capabilities(c.Structure):
    _fields_ = [('sid', c.c_void_p), ('capabilities', c.c_void_p),
               ('count', w.DWORD), ('reserved', w.DWORD)]


def libraries():
    if os.name != 'nt':
        raise OSError('Windows isolation only; no command started')
    kernel = c.WinDLL('kernel32', use_last_error=True)
    adv = c.WinDLL('advapi32', use_last_error=True)
    user = c.WinDLL('userenv', use_last_error=True)
    defs = {
        'InitializeProcThreadAttributeList': ([c.c_void_p, w.DWORD, w.DWORD, c.POINTER(c.c_size_t)], w.BOOL),
        'UpdateProcThreadAttribute': ([c.c_void_p, w.DWORD, c.c_size_t, c.c_void_p, c.c_size_t, c.c_void_p, c.c_void_p], w.BOOL),
        'DeleteProcThreadAttributeList': ([c.c_void_p], None),
        'CreateProcessW': ([w.LPCWSTR, w.LPWSTR, c.c_void_p, c.c_void_p, w.BOOL, w.DWORD,
                            c.c_void_p, w.LPCWSTR, c.c_void_p, c.POINTER(Process)], w.BOOL),
        'ResumeThread': ([w.HANDLE], w.DWORD), 'WaitForSingleObject': ([w.HANDLE, w.DWORD], w.DWORD),
        'GetExitCodeProcess': ([w.HANDLE, c.POINTER(w.DWORD)], w.BOOL),
        'TerminateProcess': ([w.HANDLE, w.UINT], w.BOOL),
        'CloseHandle': ([w.HANDLE], w.BOOL), 'LocalFree': ([c.c_void_p], c.c_void_p)}
    for name, (args, result) in defs.items():
        getattr(kernel, name).argtypes, getattr(kernel, name).restype = args, result
    for name, args, result in (
        ('OpenProcessToken', [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)], w.BOOL),
        ('GetTokenInformation', [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)], w.BOOL),
        ('ConvertSidToStringSidW', [c.c_void_p, c.POINTER(w.LPWSTR)], w.BOOL),
        ('FreeSid', [c.c_void_p], c.c_void_p)):
        getattr(adv, name).argtypes, getattr(adv, name).restype = args, result
    user.CreateAppContainerProfile.argtypes = [w.LPCWSTR, w.LPCWSTR, w.LPCWSTR, c.c_void_p, w.DWORD, c.POINTER(c.c_void_p)]
    user.CreateAppContainerProfile.restype = c.c_long
    user.DeleteAppContainerProfile.argtypes = [w.LPCWSTR]
    user.DeleteAppContainerProfile.restype = c.c_long
    return kernel, adv, user


def sid_text(pointer, kernel, adv):
    text = w.LPWSTR()
    checked(adv.ConvertSidToStringSidW(pointer, c.byref(text)))
    try:
        return text.value
    finally:
        kernel.LocalFree(c.cast(text, c.c_void_p))


def token_info(handle, kernel, adv):
    token = w.HANDLE()
    checked(adv.OpenProcessToken(handle, 8, c.byref(token)))
    def get(kind):
        size = w.DWORD()
        adv.GetTokenInformation(token, kind, None, 0, c.byref(size))
        if not size.value:
            raise c.WinError(c.get_last_error())
        buffer = c.create_string_buffer(size.value)
        checked(adv.GetTokenInformation(token, kind, buffer, size, c.byref(size)))
        return buffer
    try:
        is_app = c.cast(get(29), c.POINTER(w.DWORD))[0]  # TokenIsAppContainer
        count = c.cast(get(30), c.POINTER(w.DWORD))[0]   # TokenCapabilities / TOKEN_GROUPS
        package = get(31)  # TokenAppContainerSid / TOKEN_APPCONTAINER_INFORMATION
        pointer = c.cast(package, c.POINTER(c.c_void_p))[0]
        return dict(is_appcontainer=bool(is_app), capabilities=count,
                    package_sid=sid_text(pointer, kernel, adv) if pointer else None)
    finally:
        kernel.CloseHandle(token)


def launch(executable, worker, workspace, outside, port, sid, sid_string, confined, fault=None):
    kernel, adv, _ = libraries()
    started = time.monotonic()
    row = dict(confined=confined, fault=fault, resumed=False, pid=None)
    process, attributes, job = Process(), None, None
    try:
        startup = StartupEx()
        startup.startup.cb = c.sizeof(startup)
        flags = 0x4 | 0x08000000 | 0x400  # SUSPENDED | NO_WINDOW | UNICODE_ENVIRONMENT
        if confined:
            size = c.c_size_t()
            kernel.InitializeProcThreadAttributeList(None, 1, 0, c.byref(size))
            attributes = c.create_string_buffer(size.value)
            checked(kernel.InitializeProcThreadAttributeList(attributes, 1, 0, c.byref(size)))
            capabilities = Capabilities(sid, None, 0, 0)
            checked(kernel.UpdateProcThreadAttribute(attributes, 0, 0x20009, c.byref(capabilities), c.sizeof(capabilities), None, None))
            startup.attributes = c.cast(attributes, c.c_void_p)
            flags |= 0x80000  # EXTENDED_STARTUPINFO_PRESENT
        else:
            startup.startup.cb = c.sizeof(Startup)
        arguments = [str(executable), '-I', '-B', str(worker), str(workspace), str(outside), str(port), str(os.getpid())]
        environment = c.create_unicode_buffer('\0'.join(f'{key}={value}' for key, value in sorted({
            'SystemRoot': os.environ['SystemRoot'], 'TEMP': str(workspace), 'TMP': str(workspace),
            'LOCALAPPDATA': str(workspace)}.items()))+'\0\0')
        checked(kernel.CreateProcessW(str(executable), c.create_unicode_buffer(subprocess.list2cmdline(arguments)),
            None, None, False, flags, environment, str(workspace), c.byref(startup), c.byref(process)))
        row['pid'] = process.pid
        row['token'] = token_info(process.process, kernel, adv)
        expected = dict(is_appcontainer=True, capabilities=0, package_sid=sid_string) if confined else dict(is_appcontainer=False, capabilities=0, package_sid=None)
        if row['token'] != expected or fault == 'token':
            raise RuntimeError('Token gate rejected before resume')
        job = Job(SimpleNamespace(memory_bytes=128*1024**2, cpu_seconds=5, processes=1 if confined else 2))
        if fault == 'job':
            raise RuntimeError('Injected assignment gate failure before resume')
        job.assign(SimpleNamespace(_handle=process.process))
        row['job_before'] = job.usage()
        if kernel.ResumeThread(process.thread) != 1:
            raise RuntimeError('Unexpected primary-thread suspension count')
        row['resumed'] = True
        while kernel.WaitForSingleObject(process.process, 10) == 258:
            if time.monotonic()-started > 10 or job.usage()['user_cpu_seconds'] >= 5:
                job.terminate()
                raise RuntimeError('Capability worker exceeded time cap')
        code = w.DWORD()
        checked(kernel.GetExitCodeProcess(process.process, c.byref(code)))
        row['exit_code'] = code.value
        row['job_after'] = job.usage()
    except (OSError, RuntimeError) as error:
        row.update(error=str(error), winerror=getattr(error, 'winerror', None))
    finally:
        if process.process:
            if kernel.WaitForSingleObject(process.process, 0) == 258:
                checked(kernel.TerminateProcess(process.process, 125))
                checked(kernel.WaitForSingleObject(process.process, 2000) == 0)
            if 'exit_code' not in row:
                code = w.DWORD()
                checked(kernel.GetExitCodeProcess(process.process, c.byref(code)))
                row['exit_code'] = code.value
        if job:
            job.close()
        for handle in (process.thread, process.process):
            if handle:
                checked(kernel.CloseHandle(handle))
        if attributes is not None:
            kernel.DeleteProcThreadAttributeList(attributes)
        row['stopped'] = process_exited(row['pid']) if row['pid'] else True
        row['elapsed_seconds'] = time.monotonic()-started
    return row


def command_log(log, args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    log.append(dict(command=args, stdout=result.stdout, stderr=result.stderr, exit_code=result.returncode))
    result.check_returncode()


def copy_runtime(destination):
    base = Path(getattr(sys, '_base_executable', sys.executable)).parent
    destination.mkdir()
    for name in ('python.exe', 'python312.dll', 'python3.dll', 'vcruntime140.dll', 'vcruntime140_1.dll'):
        shutil.copy2(base/name, destination/name)
    shutil.copytree(base/'DLLs', destination/'DLLs')
    with zipfile.ZipFile(destination/'python312.zip', 'w', zipfile.ZIP_DEFLATED) as bundle:
        for file in sorted((base/'Lib').rglob('*.py')):
            relative = file.relative_to(base/'Lib')
            if not set(relative.parts) & {'site-packages', '__pycache__', 'test', 'tests', 'idlelib', 'tkinter', 'ensurepip', 'turtledemo'}:
                bundle.write(file, relative.as_posix())
    (destination/'python312._pth').write_text('python312.zip\nDLLs\n.\n', encoding='utf-8')
    shutil.copy2(ROOT/'experiments/isolation_worker.py', destination/'worker.py')
    return {file.relative_to(destination).as_posix(): sha(file) for file in sorted(destination.rglob('*')) if file.is_file()}


def run_panel(output, revision):
    kernel, adv, user = libraries()
    if len(revision) != 40 or any(char not in '0123456789abcdef' for char in revision):
        raise ValueError('Exact reviewed revision required')
    output = Path(output).resolve()
    if output.drive.upper() != 'D:' or output.exists():
        raise ValueError('Fresh D: output required')
    if shutil.disk_usage(output.parent).free < 5*1024**3:
        raise OSError('5 GB floor rejected')
    output.mkdir()
    data = dict(schema='isolation01-v1', revision=revision,
                source_sha256={name: sha(ROOT/name) for name in FILES},
                profile='OraLab.Isolation.'+uuid.uuid4().hex, rows=[], acl=[], cleanup=False)
    sid = c.c_void_p()
    created = False
    started = time.monotonic()
    try:
        result = user.CreateAppContainerProfile(data['profile'], data['profile'], 'Disposable bounded Ora capability test', None, 0, c.byref(sid))
        if result != 0:
            raise OSError(f'CreateAppContainerProfile HRESULT {result & 0xffffffff:08x}')
        created = True
        data['package_sid'] = sid_text(sid, kernel, adv)
        save(output/'evidence.json', data)
        runtime = output/'runtime'
        data['runtime_sha256'] = copy_runtime(runtime)
        outside = output/'outside'
        outside.mkdir()
        # Protect only new canary directory; no existing ACL is changed.
        account = subprocess.run(['whoami'], check=True, capture_output=True, text=True, timeout=10).stdout.strip()
        command_log(data['acl'], ['icacls', str(outside), '/inheritance:r', '/grant:r', f'{account}:(OI)(CI)F', '*S-1-5-18:(OI)(CI)F', '*S-1-5-32-544:(OI)(CI)F'])
        command_log(data['acl'], ['icacls', str(runtime), '/grant', f'*{data["package_sid"]}:(OI)(CI)RX', '/T'])
        for trial in range(2):
            for case in ('control', 'confined', 'missing', 'job', 'token'):
                if time.monotonic()-started > 280:
                    raise RuntimeError('Panel deadline reached')
                if sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) > DISK_LIMIT:
                    raise OSError('Panel disk ceiling reached')
                workspace = output/f'{trial}-{case}'
                workspace.mkdir()
                # Explicit owner WRITE_OWNER is needed to lower the new folder's
                # mandatory label; inherited Modify rights alone do not include it.
                command_log(data['acl'], ['icacls', str(workspace), '/grant',
                    f'{account}:(OI)(CI)F', f'*{data["package_sid"]}:(OI)(CI)M'])
                command_log(data['acl'], ['icacls', str(workspace), '/setintegritylevel', '(OI)(CI)L'])
                canary = outside/'canary.txt'
                canary.write_text('outside-canary-'+str(trial), encoding='utf-8')
                before = sha(canary)
                with socket.socket() as listener:
                    listener.bind(('127.0.0.1', 0))
                    listener.listen(4)
                    listener.settimeout(0.1)
                    row = launch(runtime/('absent.exe' if case == 'missing' else 'python.exe'),
                        runtime/'worker.py', workspace, canary, listener.getsockname()[1], sid,
                        data['package_sid'], case != 'control', case if case in ('job', 'token') else None)
                    connections = []
                    while True:
                        try:
                            stream, address = listener.accept()
                        except socket.timeout:
                            break
                        with stream:
                            stream.settimeout(1)
                            connections.append(dict(address=address, payload=stream.recv(32).hex()))
                row.update(trial=trial, case=case, canary_before=before, canary_after=sha(canary),
                    connections=connections, marker=(workspace/'started').exists(),
                    worker_sha256=sha(workspace/'worker.json') if (workspace/'worker.json').exists() else None)
                data['rows'].append(row)
                save(output/'evidence.json', data)
    finally:
        if created:
            result = user.DeleteAppContainerProfile(data['profile'])
            data['cleanup_hresult'] = result & 0xffffffff
            data['cleanup'] = result == 0
        if sid:
            adv.FreeSid(sid)
        data['elapsed_seconds'] = time.monotonic()-started
        save(output/'evidence.json', data)
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    run_panel(args.output_dir, args.source_revision)
