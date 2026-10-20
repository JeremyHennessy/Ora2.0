"""Finite supervised service renewal. No installation or automatic boot startup."""
import argparse
import hashlib
import json
import msvcrt
from pathlib import Path
import sys
import time
from experiments.ora_native_slice_v1 import run_slice, Limits
from experiments.ora_controller_v1 import atomic


def supervise(directory, seconds=60, slice_seconds=15, max_restarts=2, max_attempts=64):
    if not 0 < seconds <= 3600 or not 0 < slice_seconds <= 60:
        raise ValueError('Supervision requires finite <=1h total and <=60s slices')
    if type(max_restarts) is not int or not 0 <= max_restarts <= 3:
        raise ValueError('At most three crash retries')
    if type(max_attempts) is not int or not 1<=max_attempts<=64:
        raise ValueError('At most 64 attempts')
    root=Path(directory).resolve(); root.mkdir(parents=True,exist_ok=True)
    for p in (root,root/'supervisor.lock'):
        if p.exists() and (p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400 or
                           (p.is_file() and p.stat().st_nlink!=1)):
            raise ValueError('Supervisor requires plain local paths')
    stop=root/'STOP'; rows=[]; failures=0; started=time.monotonic(); deadline=started+seconds
    with (root/'supervisor.lock').open('a+b') as owner:
        owner.seek(0); msvcrt.locking(owner.fileno(),msvcrt.LK_NBLCK,1)
        if (root/'service-safety-hold.json').exists():
            raise RuntimeError('Service safety hold requires operator review; no worker started')
        reason='time-bound'
        while time.monotonic()<deadline and len(rows)<max_attempts:
            if stop.exists(): reason='operator-stop'; break
            duration=min(slice_seconds,deadline-time.monotonic())
            def publish_start(value):
                value.update(schema='ORA-SERVICE-SUSPENDED-START-v1',attempt=len(rows))
                temporary=root/'active-worker.next'
                temporary.write_text(json.dumps(value,sort_keys=True))
                temporary.replace(root/'active-worker.json')
            try:
                result=run_slice(lambda *unused:[sys.executable,'-B','-m','experiments.ora_task_store_v1',
                    str(root),'--seconds',str(duration),'--max-tasks','1000'],
                    Path(__file__).resolve().parents[1],
                    Limits(memory_bytes=256*1024**2,cpu_seconds=10,processes=2,wall_seconds=duration+2),
                    stop_path=stop,on_start=publish_start)
            except BaseException as error:
                atomic(root/'service-safety-hold.json',dict(kind='native-launch-or-closure-error',
                    attempt=len(rows),error=(type(error).__name__+': '+str(error))[:2048]))
                raise
            output=result.pop('output')
            result['output_sha256']=hashlib.sha256(output.encode()).hexdigest()
            # Two rotating bounded transport logs; receipt rows contain no task text.
            log=root/f'service-output-{len(rows)%2}.log'
            with log.open('wb') as stream: stream.write(output.encode())
            atomic(root/'supervisor-last-attempt.json',dict(attempt=len(rows),native=result,log=log.name))
            if result['output_limit_exceeded'] or result['descendant_leak']:
                atomic(root/'service-safety-hold.json',dict(kind='worker-capture-or-process-guard',
                    attempt=len(rows),native=result,log=log.name))
                raise RuntimeError('Service safety hold: output_limit_exceeded='+str(result['output_limit_exceeded'])+
                    ', descendant_leak='+str(result['descendant_leak'])+'; exact native receipt retained')
            rows.append(result)
            if result['exit_code']==0:
                from experiments.ora_task_store_v1 import Store
                from experiments.ora_ollama_feedback_v1 import configuration
                generator,key=configuration(root)
                with Store(root,generator,key) as store:
                    result['backup']=store.backup(root/'backups')
            if stop.exists(): reason='operator-stop'; break
            if result['exit_code']!=0:
                failures+=1
                if failures>max_restarts: reason='retry-bound'; break
                until=min(deadline,time.monotonic()+min(2**(failures-1),4))
                while time.monotonic()<until and not stop.exists(): time.sleep(.05)
            else:
                # A successful bounded slice is a renewal, not a crash retry.
                try:
                    child=json.loads(output)
                    if child['run']['reason']!='slice-bound':
                        reason='worker-stop'; break
                except (ValueError,KeyError,TypeError):
                    raise RuntimeError('Invalid worker terminal output; refuse renewal')
        if len(rows)==max_attempts: reason='attempt-bound'
        receipt=dict(schema='ORA-SUPERVISED-SERVICE-v1',reason=reason,attempts=rows,
            crash_failures=failures,elapsed_seconds=time.monotonic()-started,
            all_attempts_closed=all(x['post_close_processes_exited'] for x in rows),
            continuous_startup_installed=False)
        destination=root/'supervisor-receipt.json'; temporary=root/'supervisor-receipt.next'
        temporary.write_text(json.dumps(receipt,indent=2)+'\n')
        temporary.replace(destination)
        return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--seconds',type=float,default=60)
    parser.add_argument('--slice-seconds',type=float,default=15)
    parser.add_argument('--max-restarts',type=int,default=2)
    parser.add_argument('--max-attempts',type=int,default=64)
    args=parser.parse_args()
    receipt=supervise(args.directory,args.seconds,args.slice_seconds,args.max_restarts,args.max_attempts)
    print(json.dumps(dict(reason=receipt['reason'],attempts=len(receipt['attempts']),
                         crash_failures=receipt['crash_failures'],all_attempts_closed=receipt['all_attempts_closed'])))
    return 0 if receipt['reason'] in ('time-bound','operator-stop') else 1


if __name__=='__main__': raise SystemExit(main())
