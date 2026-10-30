"""Finite synthetic OS fixtures only. No experiment imports or arbitrary tasks."""
import os
import subprocess
import sys
import time

mode = int(sys.argv[1])
if mode == 0:
    print('EKA_SYNTHETIC_OK', flush=True)
elif mode in (2, 7, 9):
    print('EKA_SLEEP_STARTED', flush=True)
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
    try:
        subprocess.Popen([sys.executable, '-I', '-S', '-B', __file__, '9'])
    except OSError:
        print('EKA_PROCESS_CAP_REFUSED', flush=True)
    print('EKA_DESCENDANT_CREATED', child.pid, flush=True)
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
