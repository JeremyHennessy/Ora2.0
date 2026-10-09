"""ISOLATION-01 inert capability attempts; no world, network beyond loopback."""
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import socket
import subprocess
import sys


def attempt(action):
    try:
        value = action()
        return dict(ok=True, value=value)
    except OSError as error:
        return dict(ok=False, winerror=getattr(error, 'winerror', None),
                    errno=error.errno, error=str(error))


def run(work, outside, port, parent):
    work, outside = Path(work), Path(outside)
    (work/'started').write_text('inert-worker', encoding='utf-8')
    report = dict(pid=os.getpid(), executable=sys.executable)
    report['workspace_write'] = attempt(lambda: (work/'allowed').write_text('allowed', encoding='utf-8'))
    report['workspace_read'] = attempt(lambda: (work/'allowed').read_text(encoding='utf-8'))
    report['outside_read'] = attempt(lambda: outside.read_text(encoding='utf-8'))
    report['outside_write'] = attempt(lambda: outside.write_text('control-write', encoding='utf-8'))
    def connect():
        with socket.create_connection(('127.0.0.1', int(port)), timeout=1) as stream:
            stream.sendall(b'inert-probe')
        return True
    report['network'] = attempt(connect)
    def parent_handle():
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        kernel.OpenProcess.restype = w.HANDLE
        kernel.CloseHandle.argtypes = [w.HANDLE]
        handle = kernel.OpenProcess(0x20, False, int(parent))  # VM_WRITE; never write.
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        kernel.CloseHandle(handle)
        return True
    report['parent_handle'] = attempt(parent_handle)
    report['child'] = attempt(lambda: subprocess.run(
        [sys.executable, '-I', '-c', 'raise SystemExit(0)'],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=3, close_fds=True).returncode)
    (work/'worker.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    run(*sys.argv[1:])
