"""Explicit Windows Job-at-creation launcher for bounded local service slices.

No World imports, shell, task interpretation, startup installation or admission.
The caller owns source/config review. Never treats a leader exit as tree closure.
"""
import ctypes
from ctypes import wintypes as wt
import msvcrt
import os
from pathlib import Path
import struct
import subprocess
import threading
import time
from experiments.process_limits import Job, Limits


class START(ctypes.Structure):
    _fields_ = [('cb',wt.DWORD),('reserved',wt.LPWSTR),('desktop',wt.LPWSTR),('title',wt.LPWSTR),
        ('x',wt.DWORD),('y',wt.DWORD),('xs',wt.DWORD),('ys',wt.DWORD),('xc',wt.DWORD),('yc',wt.DWORD),
        ('fill',wt.DWORD),('flags',wt.DWORD),('show',wt.WORD),('reserved_n',wt.WORD),
        ('reserved_ptr',ctypes.c_void_p),('input',wt.HANDLE),('output',wt.HANDLE),('error',wt.HANDLE)]


class STARTEX(ctypes.Structure):
    _fields_ = [('startup', START), ('attributes', ctypes.c_void_p)]


class PI(ctypes.Structure):
    _fields_ = [('process',wt.HANDLE),('thread',wt.HANDLE),('pid',wt.DWORD),('tid',wt.DWORD)]


def run_slice(command_builder, cwd, limits, stop_path=None, birth_handoff=False, on_start=None):
    """Builder receives owned Job, GetTickCount64 and optional birth-read handle.

    Wall and STOP supervision are outside the child. Capture retains at most
    1 MiB combined; excess terminates the Job. Output draining continues to EOF.
    """
    limits.validate()
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateProcessW': ([wt.LPCWSTR,wt.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,wt.BOOL,wt.DWORD,ctypes.c_void_p,wt.LPCWSTR,ctypes.c_void_p,ctypes.POINTER(PI)],wt.BOOL),
        'InitializeProcThreadAttributeList': ([ctypes.c_void_p,wt.DWORD,wt.DWORD,ctypes.POINTER(ctypes.c_size_t)],wt.BOOL),
        'UpdateProcThreadAttribute': ([ctypes.c_void_p,wt.DWORD,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p],wt.BOOL),
        'DeleteProcThreadAttributeList': ([ctypes.c_void_p],None),
        'CloseHandle': ([wt.HANDLE],wt.BOOL), 'GetTickCount64': ([],ctypes.c_ulonglong),
        'GetProcessTimes': ([wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p],wt.BOOL),
        'WaitForSingleObject': ([wt.HANDLE,wt.DWORD],wt.DWORD),
        'GetExitCodeProcess': ([wt.HANDLE,ctypes.POINTER(wt.DWORD)],wt.BOOL),
        'ResumeThread': ([wt.HANDLE],wt.DWORD)}
    for name,(args,result) in signatures.items():
        getattr(k,name).argtypes=args; getattr(k,name).restype=result
    def check(ok):
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
    job = Job(limits)
    pi = PI(); initialized = False; threads = []; files = []; descriptors = []
    capture = bytearray(); received = 0; errors = []; guard = threading.Lock()
    excess = threading.Event(); ended = threading.Event()
    start_time = time.monotonic()
    attrs = None
    try:
        read_fd, write_fd = os.pipe(); descriptors.extend([read_fd, write_fd])
        null = open(os.devnull, 'rb'); files.append(null)
        inherited = [msvcrt.get_osfhandle(null.fileno()), msvcrt.get_osfhandle(write_fd)]
        birth_read = birth_write = None
        if birth_handoff:
            birth_read,birth_write = os.pipe(); descriptors.extend([birth_read,birth_write])
            inherited.extend([int(job.handle),msvcrt.get_osfhandle(birth_read)])
        for handle in inherited:
            os.set_handle_inheritable(handle, True)
        size = ctypes.c_size_t()
        k.InitializeProcThreadAttributeList(None,2,0,ctypes.byref(size))
        attrs = ctypes.create_string_buffer(size.value)
        check(k.InitializeProcThreadAttributeList(attrs,2,0,ctypes.byref(size))); initialized=True
        jobs = (wt.HANDLE*1)(job.handle)
        handles = (wt.HANDLE*len(inherited))(*inherited)
        check(k.UpdateProcThreadAttribute(attrs,0,0x2000D,jobs,ctypes.sizeof(jobs),None,None))
        check(k.UpdateProcThreadAttribute(attrs,0,0x20002,handles,ctypes.sizeof(handles),None,None))
        command = command_builder(int(job.handle),k.GetTickCount64(),None if birth_read is None else msvcrt.get_osfhandle(birth_read))
        startup = STARTEX(); startup.startup.cb=ctypes.sizeof(startup); startup.attributes=ctypes.cast(attrs,ctypes.c_void_p)
        startup.startup.flags=0x100; startup.startup.input=inherited[0]
        startup.startup.output=startup.startup.error=inherited[1]
        line=ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
        check(k.CreateProcessW(None,line,None,None,True,0x80000|4|8,None,str(cwd),ctypes.byref(startup),ctypes.byref(pi)))
        times=[ctypes.c_ulonglong() for _ in range(4)]
        check(k.GetProcessTimes(pi.process,*[ctypes.byref(x) for x in times]))
        birth=times[0].value
        if birth_handoff:
            if os.write(birth_write,struct.pack('<Q',birth)) != 8:
                raise OSError('Incomplete birth handoff')
            os.close(birth_write); descriptors.remove(birth_write)
        os.close(write_fd); descriptors.remove(write_fd)
        def drain():
            nonlocal received
            try:
                while True:
                    block=os.read(read_fd,16384)
                    if not block:
                        break
                    with guard:
                        received += len(block)
                        capture.extend(block[:max(0,1024**2-len(capture))])
                        if received>1024**2:
                            excess.set()
            except BaseException as error:
                errors.append(repr(error))
            finally:
                ended.set()
        thread=threading.Thread(target=drain,daemon=True); threads.append(thread); thread.start()
        if on_start is not None:
            on_start(dict(pid=pi.pid,creation_filetime_decimal=str(birth),
                          suspended=True,creation_flags=0x80000|4|8,usage=job.usage()))
        if k.ResumeThread(pi.thread)!=1:
            raise OSError('Cannot resume suspended child')
        reason='exit'
        while True:
            wait=k.WaitForSingleObject(pi.process,20)
            if wait==0:
                break
            if wait!=258:
                raise OSError('Native wait failed')
            if excess.is_set() or errors:
                reason='capture-limit'; job.terminate(); break
            if stop_path is not None and Path(stop_path).exists():
                reason='operator-stop'; job.terminate(); break
            if time.monotonic()-start_time>=limits.wall_seconds:
                reason='wall-limit'; job.terminate(); break
        if k.WaitForSingleObject(pi.process,3000)!=0:
            raise RuntimeError('Child closure unknown')
        code=wt.DWORD(); check(k.GetExitCodeProcess(pi.process,ctypes.byref(code)))
        # Kill lingering descendants even if the root exited successfully.
        usage=job.usage()
        leaked=usage['active_before_close']!=0
        if leaked:
            job.terminate()
        deadline=time.monotonic()+3
        while job.usage()['active_before_close'] and time.monotonic()<deadline:
            time.sleep(.01)
        usage=job.usage()
        if usage['active_before_close']:
            raise RuntimeError('Job closure unknown')
        thread.join(3)
        if not ended.is_set() or errors:
            raise RuntimeError('Capture closure unknown: '+repr(errors))
        return dict(command=command,pid=pi.pid,creation_filetime_decimal=str(birth),exit_code=code.value,
                    reason=reason,elapsed_seconds=time.monotonic()-start_time,usage=usage,
                    descendant_leak=leaked,post_close_processes_exited=True,capture_eof=True,
                    received_bytes=received,retained_bytes=len(capture),
                    output_limit_exceeded=excess.is_set(),output=bytes(capture).decode('utf8',errors='replace'))
    finally:
        # Original Job stays owned until all wait/capture checks or exception cleanup.
        try:
            if job.handle:
                job.terminate()
        finally:
            job.close()
            for thread in threads:
                thread.join(3)
            if pi.thread: check(k.CloseHandle(pi.thread))
            if pi.process: check(k.CloseHandle(pi.process))
            if initialized: k.DeleteProcThreadAttributeList(attrs)
            for fd in descriptors: os.close(fd)
            for stream in files: stream.close()
