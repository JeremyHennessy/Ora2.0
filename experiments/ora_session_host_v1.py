"""Prepared logon host: outside Job custody and explicit activation gate.

No scheduler registration or OS reboot. Continuous mode requires verified soak
and physical-reboot receipts. A sticky STOP and saved failure budget survive
logoff, reboot and task retriggering. Secrets and memories stay in the same store.
"""
import argparse
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
import time
from experiments.ora_controller_v1 import atomic,identity,boot_token
from experiments.ora_native_slice_v1 import run_slice,Limits

ROOT=Path(__file__).resolve().parents[1]


def plain(path):
    if path.is_symlink() or getattr(path.lstat(),'st_file_attributes',0)&0x400 or (path.is_file() and path.stat().st_nlink!=1):
        raise ValueError('Plain local host artifacts required')


def read(path,cap=65536):
    plain(path)
    with path.open('rb') as stream: raw=stream.read(cap+1)
    if len(raw)>cap: raise ValueError('Host artifact size limit')
    return json.loads(raw)


def activation(root,continuous):
    value=read(root/'startup-activation.json')
    if value.get('enabled') is not True or value.get('mode')!=('continuous' if continuous else 'reboot-test'):
        raise ValueError('Explicit matching startup activation required')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if value['source_head']!=head or subprocess.call(['git','diff','--quiet','HEAD','--','experiments'],cwd=ROOT):
        raise ValueError('Startup source changed; review before activation')
    for name,digest in value['source_hashes'].items():
        path=ROOT/name
        if not path.resolve().is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('Startup dependency identity changed')
    if continuous:
        for key,flag in (('soak_receipt','passed'),('reboot_receipt','physical_reboot_passed')):
            item=value[key]; path=Path(item['path']); raw=path.read_bytes()
            if len(raw)>1024**2 or hashlib.sha256(raw).hexdigest()!=item['sha256'] or json.loads(raw).get(flag) is not True:
                raise ValueError('Verified soak and physical reboot evidence required')
    else:
        if boot_token()==value['before_boot']: raise ValueError('Physical reboot has not occurred')
        before=value['before_owner']
        if identity(before['pid'])==before: raise ValueError('Pre-reboot controller still alive')
    return value


def host(directory,continuous=False,windows=1):
    if type(windows) is not int or not 1<=windows<=4: raise ValueError('Finite host test window bound required')
    root=Path(directory); root.mkdir(parents=True,exist_ok=True); plain(root)
    stop=root/'STOP'; state_path=root/'host-state.json'
    lock_path=root/'host.lock'
    if lock_path.exists(): plain(lock_path)
    with lock_path.open('a+b') as lock:
        lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        if stop.exists(): return dict(reason='operator-stop')
        if (root/'startup-hold.json').exists(): raise RuntimeError('Startup held for operator review')
        plan=activation(root,continuous)
        seconds=plan['seconds']; epoch=plan['epoch_seconds']
        if not 130<=seconds<=7200 or not 5<=epoch<=600 or seconds/epoch>28:
            raise ValueError('Finite controller windows required')
        if not continuous and seconds>1200: raise ValueError('Reboot test at most20 minutes')
        state=read(state_path) if state_path.exists() else dict(failures=0,completed_windows=0,unclean=False)
        if 'controller_failures_seen' not in state:
            state['controller_failures_seen']=read(root/'controller-state.json')['failures'] if (root/'controller-state.json').exists() else 0
        if state['failures']>=3: raise RuntimeError('Saved host failure budget exhausted')
        if state.get('unclean'): state['failures']+=1
        if state['failures']>=3:
            state.update(reason='failure-budget',unclean=False); atomic(state_path,state)
            raise RuntimeError('Interrupted hosts exhausted saved budget')
        state.update(owner=identity(os.getpid()),unclean=False,reason='starting'); atomic(state_path,state)
        completed=0
        while continuous or completed<windows:
            if stop.exists(): state['reason']='operator-stop'; break
            if state['failures']>=3: state['reason']='failure-budget'; break
            # Recheck immutable source/activation before every new bounded window.
            activation(root,continuous)
            state.update(unclean=True,reason='running'); atomic(state_path,state)
            try:
                command=[sys.executable,'-B','-m','experiments.ora_controller_v1',str(root),
                    '--seconds',str(seconds),'--epoch-seconds',str(epoch),'--practice',str(plan['practice'])]
                for name in plan['files']: command.extend(['--file',name])
                if continuous: command.append('--renew-completed')
                result=run_slice(lambda *unused:command,ROOT,
                    Limits(memory_bytes=32*1024**3,cpu_seconds=21600,processes=16,wall_seconds=seconds+15),
                    stop_path=stop,on_start=lambda item:atomic(root/'host-active-controller.json',item))
                output=result.pop('output'); (root/f"host-output-{state['completed_windows']%2}.log").write_bytes(output.encode('utf8')[:1024**2])
                atomic(root/'host-native-result.json',result)
                if not result['post_close_processes_exited'] or result['descendant_leak'] or result['output_limit_exceeded'] or not result['capture_eof']:
                    raise RuntimeError('Host custody/capture failed')
                if stop.exists(): state['reason']='operator-stop'; break
                if result['exit_code']!=0 or result['reason']!='exit': raise RuntimeError('Controller window failed')
                terminal=read(root/'controller-state.json')
                if terminal.get('phase')!='stopped' or terminal.get('reason')!='time-bound' or terminal.get('unclean'):
                    raise RuntimeError('Controller terminal state not renewable')
                # Any new controller failure pauses automatic renewal for review.
                failures=terminal['failures']
                if continuous and failures>state['controller_failures_seen']: raise RuntimeError('New controller failure requires review')
                state['controller_failures_seen']=failures
                completed+=1; state['completed_windows']+=1; state['reason']='window-bound'
            except BaseException as error:
                state['failures']+=1; state['reason']='review-required'; state['error']=(type(error).__name__+': '+str(error))[:2048]
                # No silent crash loop: next trigger sees durable error until an
                # operator explicitly reviews it. The budget is never reset here.
                atomic(root/'startup-hold.json',dict(reason=state['error'],failures=state['failures']))
                raise
            finally:
                state.update(unclean=False,ended_utc=time.time()); atomic(state_path,state)
        state.update(unclean=False,ended_utc=time.time()); atomic(state_path,state)
        return state


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('directory',type=Path)
    parser.add_argument('--continuous',action='store_true'); parser.add_argument('--windows',type=int,default=1)
    args=parser.parse_args()
    if (args.directory/'startup-hold.json').exists(): raise SystemExit('Startup held for operator review')
    result=host(args.directory,args.continuous,args.windows)
    print(json.dumps({k:result[k] for k in ('reason','failures','completed_windows') if k in result}))
