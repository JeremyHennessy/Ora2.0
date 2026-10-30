"""Finite synthetic OS fixtures only. No experiment imports or arbitrary tasks."""
import os
import subprocess
import sys
import time


def process_identity(kernel,handle):
    import ctypes
    from ctypes import wintypes as wt
    kernel.GetProcessId.argtypes=[wt.HANDLE];kernel.GetProcessId.restype=wt.DWORD
    kernel.GetProcessTimes.argtypes=[wt.HANDLE]+[ctypes.c_void_p]*4;kernel.GetProcessTimes.restype=wt.BOOL
    kernel.WaitForSingleObject.argtypes=[wt.HANDLE,wt.DWORD];kernel.WaitForSingleObject.restype=wt.DWORD
    times=[ctypes.c_ulonglong() for unused in range(4)]
    pid=kernel.GetProcessId(handle)
    if not pid or not kernel.GetProcessTimes(handle,*[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
    if not times[0].value or kernel.WaitForSingleObject(handle,0)!=258:raise OSError('Expected process birth is not live')
    return pid,times[0].value


def identity_frame(prefix,pid,birth):
    import msvcrt
    msvcrt.setmode(1,os.O_BINARY)  # Exact LF bytes for the native frame parser.
    raw=(prefix+' '+str(pid)+' '+str(birth)+'\n').encode('ascii')
    if os.write(1,raw)!=len(raw):raise OSError('Short descendant identity frame; no retry')


mode = int(sys.argv[1])
if mode == 0:
    print('EKA_SYNTHETIC_OK', flush=True)
elif mode in (2, 7):
    print('EKA_SLEEP_STARTED', flush=True)
    time.sleep(20)
elif mode == 9:
    import ctypes
    from ctypes import wintypes as wt
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.argtypes=[];kernel.GetCurrentProcess.restype=wt.HANDLE
    pid,birth=process_identity(kernel,kernel.GetCurrentProcess())
    if pid!=os.getpid():raise OSError('Self PID differs')
    identity_frame('EKA_DESCENDANT_SELF',pid,birth)
    time.sleep(20)
elif mode == 3:
    print('EKA_CPU_STARTED', flush=True)
    while True:
        pass
elif mode == 4:
    blocks = []
    try:
        while True:
            blocks.append(bytearray(1024**2))
    except MemoryError:
        print('EKA_MEMORY_LIMIT', flush=True)
elif mode == 5:
    while True:
        os.write(1, b'x' * 16384)
elif mode == 6:
    # Exactly two descendant creation attempts, both covered by the parent's
    # conservative four-birth envelope (guardian, leader, these two attempts).
    child = subprocess.Popen([sys.executable, '-I', '-S', '-B', __file__, '9'])
    import ctypes
    from ctypes import wintypes as wt
    gate=ctypes.WinDLL('kernel32',use_last_error=True)
    gate.WaitForSingleObject.argtypes=[wt.HANDLE,wt.DWORD];gate.WaitForSingleObject.restype=wt.DWORD
    gate.CloseHandle.argtypes=[wt.HANDLE];gate.CloseHandle.restype=wt.BOOL
    pid,birth=process_identity(gate,int(child._handle))
    if pid!=child.pid:raise OSError('Popen handle PID differs')
    identity_frame('EKA_DESCENDANT_CREATED',pid,birth)
    handle=int(sys.argv[3])
    if not handle or gate.WaitForSingleObject(handle,3000)!=0:raise OSError('Guardian descendant-birth handshake absent')
    if not gate.CloseHandle(handle):raise ctypes.WinError(ctypes.get_last_error())
    try:
        subprocess.Popen([sys.executable, '-I', '-S', '-B', __file__, '9'])
    except OSError as exc:
        print('EKA_PROCESS_CAP_REFUSED',getattr(exc,'winerror',None),flush=True)
    else:
        raise RuntimeError('Second child unexpectedly admitted')
    # Exit while a real descendant is still alive: guardian must kill the tree.
elif mode == 8:
    import ctypes
    from ctypes import wintypes as wt
    dll=ctypes.WinDLL(sys.argv[2],use_last_error=True)
    dll.EkaStartWatchdog.argtypes=[wt.DWORD,ctypes.c_ulonglong,ctypes.c_ulonglong];dll.EkaStartWatchdog.restype=wt.BOOL
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetCurrentProcess.restype=wt.HANDLE;k.GetTickCount64.restype=ctypes.c_ulonglong
    k.GetProcessTimes.argtypes=[wt.HANDLE]+[ctypes.c_void_p]*4
    times=[ctypes.c_ulonglong() for unused in range(4)]
    if not k.GetProcessTimes(k.GetCurrentProcess(),*[ctypes.byref(v) for v in times]):raise ctypes.WinError(ctypes.get_last_error())
    if not dll.EkaStartWatchdog(os.getpid(),times[0].value,k.GetTickCount64()+2000):raise OSError('Owner watchdog refused')
    print('EKA_PYTHON_OWNER_WATCHDOG_STARTED',flush=True)
    k.Sleep(20000)  # Native thread must terminate this blocked Python process.
else:
    raise SystemExit(125)
