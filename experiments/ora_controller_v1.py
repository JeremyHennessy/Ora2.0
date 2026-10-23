"""Persistent finite controller: owned model, service, trusted mixed task source.

Normal renewal rotates two control slots. A dead owner's interrupted slot is
reused only with kill-on-close/no-breakaway readback and dead owner/listener.
Failure budget persists across relaunch. No startup task or OS reboot on import.
"""
import argparse
import ctypes
from ctypes import wintypes as wt
import json
import math
import msvcrt
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
from experiments.ora_native_slice_v1 import run_slice,Limits
from experiments.ora_owned_ollama_v1 import OwnedOllama


def atomic(path,value):
    temporary=path.with_name(path.name+'.next')
    with temporary.open('w',encoding='utf8') as stream:
        json.dump(value,stream,sort_keys=True,indent=2); stream.flush(); os.fsync(stream.fileno())
    # Windows readers may briefly open without FILE_SHARE_DELETE. Do not let a
    # read-only monitor turn a committed state update into controller failure.
    for attempt in range(51):
        try:
            os.replace(temporary,path); return
        except PermissionError:
            if attempt==50: raise
            time.sleep(.02)


def identity(pid):
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD]; k.OpenProcess.restype=wt.HANDLE
    k.GetProcessTimes.argtypes=[wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
    k.WaitForSingleObject.argtypes=[wt.HANDLE,wt.DWORD]; k.CloseHandle.argtypes=[wt.HANDLE]
    handle=k.OpenProcess(0x1000|0x100000,False,pid)
    if not handle:
        error=ctypes.get_last_error()
        if error in (87,1168): return None
        raise ctypes.WinError(error)
    try:
        if k.WaitForSingleObject(handle,0)!=258: return None
        values=[ctypes.c_ulonglong() for _ in range(4)]
        if not k.GetProcessTimes(handle,*[ctypes.byref(v) for v in values]): raise ctypes.WinError(ctypes.get_last_error())
        return dict(pid=pid,creation_filetime_decimal=str(values[0].value))
    finally: k.CloseHandle(handle)


def boot_token():
    # Actual OS-provided UTC boot time, not a simulated reboot claim.
    return subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',
        "(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o')"],
        timeout=10,creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()


def resume_state(state,boot,now):
    if state['failures']>=3: raise RuntimeError('Persistent failure budget exhausted; operator review required')
    if now<state['started_utc']-60: raise RuntimeError('Wall clock moved backwards; refuse extended run')
    prior=state.get('owner')
    if prior and identity(prior['pid'])==prior: raise RuntimeError('Prior controller is still alive')
    if state.get('unclean'):
        state['failures']+=1
        state['recoveries']=state.get('recoveries',0)+1
        state['last_recovery']='boot-changed' if boot!=state.get('boot') else 'controller-loss-same-boot'
        if state['failures']>=3: raise RuntimeError('Interrupted controllers exhausted persistent failure budget')
    state['boot']=boot
    return state


def renew_completed(state,now):
    """Explicitly renew only a clean completed window, preserving lifetime state."""
    if state.get('unclean') or state.get('phase')!='stopped' or state.get('reason')!='time-bound' or now<state['deadline_utc'] or state['failures']>=3:
        raise ValueError('Only a clean expired time-bound contract can be renewed')
    state.setdefault('lifetime_started_utc',state['started_utc'])
    state.update(started_utc=now,deadline_utc=now+state['seconds'],epoch=0,
                 window=state.get('window',0)+1)
    return state


# Service native watchdog5 + controller monitor grace6 + join8 + model close8
# plus bounded 3-second model observation. All remain inside existing deadlines.
EPOCH_CLOSE_RESERVE=30.0


def service_duration(epoch_seconds,window_remaining,model_remaining):
    values=(epoch_seconds,window_remaining,model_remaining)
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in values):
        raise ValueError('Finite numeric epoch budgets required')
    duration=min(epoch_seconds,window_remaining-EPOCH_CLOSE_RESERVE,model_remaining-EPOCH_CLOSE_RESERVE)
    if duration<1:
        raise TimeoutError('Preparation exhausted service and closure budget; no work admitted')
    return duration


def controller(directory,seconds=7200,epoch_seconds=300,files=(),practice=2,renew=False):
    if not math.isfinite(seconds) or not 5<=seconds<=7200 or not 5<=epoch_seconds<=600 or seconds/epoch_seconds>28:
        raise ValueError('Finite <=2h contract, <=600s epochs and <=28 planned epochs required')
    if type(practice) is not int or not 0<=practice<=32 or len(files)>4: raise ValueError('Bounded task source required')
    root=Path(directory)
    root.mkdir(parents=True,exist_ok=True)
    if root.is_symlink() or getattr(root.lstat(),'st_file_attributes',0)&0x400: raise ValueError('Plain controller directory required')
    stop=root/'STOP'; state_path=root/'controller-state.json'
    lock_path=root/'controller.lock'
    if lock_path.exists() and (lock_path.is_symlink() or lock_path.stat().st_nlink!=1): raise ValueError('Invalid controller lock')
    with lock_path.open('a+b') as lock:
        lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        if stop.exists(): return dict(reason='operator-stop',started=False)
        if (root/'controller-safety-hold.json').exists(): raise RuntimeError('Saved controller safety hold; review before restart')
        if (root/'service-safety-hold.json').exists(): raise RuntimeError('Saved service safety hold; review before restart')
        for name in ('feedback.key','ollama.json','controller-state.json','controller-state.json.next','owned-ollama.json','owned-ollama.next'):
            path=root/name
            if path.exists() and (not path.is_file() or path.is_symlink() or path.stat().st_nlink!=1 or getattr(path.lstat(),'st_file_attributes',0)&0x400):
                raise ValueError('Plain unshared controller artifacts required')
        if not (root/'feedback.key').exists():
            if (root/'memory.sqlite3').exists(): raise ValueError('Existing memory requires its original feedback key')
            with (root/'feedback.key').open('xb') as stream: stream.write(secrets.token_bytes(32))
        config=root/'ollama.json'
        expected=dict(model='gpt-oss:20b',port=11435)
        if config.exists():
            if json.loads(config.read_text())!=expected: raise ValueError('Controller requires the owned endpoint; no shared fallback')
        else: atomic(config,expected)
        boot=boot_token(); owner=identity(os.getpid()); now=time.time()
        if state_path.exists():
            state=json.loads(state_path.read_text())
            if (state['seconds'],state['epoch_seconds'],state['files'],state['practice'])!=(seconds,epoch_seconds,list(files),practice):
                raise ValueError('Existing run contract differs; preserve it and choose a new run directory')
            state=resume_state(state,boot,now)
            if renew and state.get('phase')=='stopped' and state.get('reason')=='time-bound':
                state=renew_completed(state,now)
        else:
            state=dict(schema='ORA-CONTROLLER-v1',started_utc=now,deadline_utc=now+seconds,
                seconds=seconds,epoch_seconds=epoch_seconds,files=list(files),practice=practice,
                failures=0,recoveries=0,epoch=0,completed_epochs=0,source_offset=0,history=[],boot=boot)
        state.update(owner=owner,phase='starting',unclean=False)
        atomic(state_path,state)
        reason='time-bound'
        monotonic_deadline=time.monotonic()+max(0,state['deadline_utc']-now)
        while time.time()<state['deadline_utc'] and time.monotonic()<monotonic_deadline and state['epoch']<32:
            if stop.exists(): reason='operator-stop'; break
            if state['failures']>=3: reason='failure-budget'; break
            remaining=min(state['deadline_utc']-time.time(),monotonic_deadline-time.monotonic())
            if remaining<130:
                state.update(phase='deadline-idle'); atomic(state_path,state)
                while time.time()<state['deadline_utc'] and time.monotonic()<monotonic_deadline and not stop.exists(): time.sleep(.1)
                if stop.exists(): reason='operator-stop'
                break
            epoch=state['epoch']; state.update(unclean=True,phase='preparing-model')
            atomic(state_path,state)
            shutdown=threading.Event(); service_thread=None; service_result={}; failure=None
            try:
                model_seconds=min(900,remaining)
                model_deadline=time.monotonic()+model_seconds
                with OwnedOllama(root,epoch,seconds=model_seconds) as model:
                    model.prepare()
                    duration=service_duration(epoch_seconds,
                        min(state['deadline_utc']-time.time(),monotonic_deadline-time.monotonic()),
                        model_deadline-time.monotonic())
                    epoch_end=time.monotonic()+duration
                    state.update(phase='service-running',model_owner=model.start,
                        service_seconds=duration,closure_reserve_seconds=EPOCH_CLOSE_RESERVE)
                    atomic(state_path,state)
                    def service():
                        try:
                            service_result['native']=run_slice(lambda *unused:[sys.executable,'-B','-m',
                                'experiments.ora_supervised_service_v1',str(root),'--seconds',str(duration),
                                '--slice-seconds','60','--max-restarts','1'],Path(__file__).resolve().parents[1],
                                Limits(memory_bytes=512*1024**2,cpu_seconds=60,processes=4,wall_seconds=duration+5),
                                stop_path=stop,stop_event=shutdown,
                                on_start=lambda value:atomic(root/'controller-service.json',value))
                        except BaseException as error: service_result['error']=str(error)
                    service_thread=threading.Thread(target=service,daemon=True); service_thread.start()
                    source_seconds=min(120,duration)
                    command=[sys.executable,'-B','-m','experiments.ora_mixed_stream_v1',str(root),'--worker',
                        '--seconds',str(source_seconds),'--practice',str(practice),'--offset',str(state['source_offset'])]
                    for name in files: command.extend(['--file',name])
                    source=run_slice(lambda *unused:command,Path(__file__).resolve().parents[1],
                        Limits(memory_bytes=128*1024**2,cpu_seconds=10,processes=2,wall_seconds=source_seconds+3),
                        stop_path=stop,stop_event=shutdown)
                    if source['exit_code']!=0 and not stop.exists(): raise RuntimeError('Task source failed: '+source['output'][-1024:])
                    while service_thread.is_alive() and time.monotonic()<epoch_end+6 and not stop.exists():
                        if not model.thread.is_alive(): raise RuntimeError('Owned model server exited')
                        model.check_model()
                        until=min(epoch_end+6,time.monotonic()+2)
                        while time.monotonic()<until and not stop.exists() and service_thread.is_alive(): time.sleep(.1)
                    if stop.exists(): shutdown.set()
                    service_thread.join(8)
                    if service_thread.is_alive(): raise RuntimeError('Service closure unknown')
                    if 'error' in service_result: raise RuntimeError(service_result['error'])
                    result=service_result['native']
                    atomic(root/'controller-service-result.json',{k:v for k,v in result.items() if k!='output'})
                    if not result['post_close_processes_exited'] or result['descendant_leak'] or result['output_limit_exceeded']:
                        raise RuntimeError('Service custody/capture failed')
                    if not stop.exists() and (result['exit_code']!=0 or result['reason']!='exit'):
                        raise RuntimeError('Service epoch failed: '+result['output'][-1024:])
                state['completed_epochs']+=1
                state['source_offset']=(state['source_offset']+practice)%169
            except BaseException as error:
                failure=(type(error).__name__+': '+str(error))[:2048]
                if stop.exists() and isinstance(error,InterruptedError):
                    reason='operator-stop'
                else:
                    state['failures']+=1
                if isinstance(error,KeyboardInterrupt): reason='interrupted'
            finally:
                shutdown.set()
                if service_thread is not None:
                    service_thread.join(8)
                    if service_thread.is_alive(): raise RuntimeError('Service custody unknown; no renewal allowed')
            state['history']=(state['history']+[dict(epoch=epoch,error=failure,ended_utc=time.time())])[-8:]
            state.update(epoch=epoch+1,unclean=False,phase='between-epochs')
            atomic(state_path,state)
            if (root/'service-safety-hold.json').exists(): reason='service-safety-hold'; break
            if reason=='interrupted': break
            if stop.exists(): reason='operator-stop'; break
            if failure:
                atomic(root/'controller-safety-hold.json',dict(error=failure,epoch=epoch,failures=state['failures']))
                reason='controller-safety-hold'; break
        if state['epoch']>=32: reason='epoch-bound'
        state.update(phase='stopped',reason=reason,unclean=False,ended_utc=time.time())
        atomic(state_path,state)
        return state


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path); parser.add_argument('--seconds',type=float,default=7200)
    parser.add_argument('--epoch-seconds',type=float,default=300); parser.add_argument('--practice',type=int,default=2)
    parser.add_argument('--file',action='append',default=[])
    parser.add_argument('--renew-completed',action='store_true',help='Explicitly renew a clean expired window; retain memories and lifetime failure budget')
    args=parser.parse_args()
    result=controller(args.directory,args.seconds,args.epoch_seconds,args.file,args.practice,args.renew_completed)
    print(json.dumps({k:result[k] for k in ('reason','phase','completed_epochs','failures') if k in result}))
    raise SystemExit(0 if result['reason'] in ('time-bound','operator-stop') else 1)
