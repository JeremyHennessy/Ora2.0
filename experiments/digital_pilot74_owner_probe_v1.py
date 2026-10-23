"""NEW-only no-World enclosing-Job probes; callable only from reviewed owner.

Not the native G protocol or production controller/referee. No scientific imports.
"""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path


def save(path,value,cap=65536):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
    if len(raw)>cap:raise ValueError('Full probe receipt exceeds declared cap')
    with Path(path).open('xb') as stream:
        if stream.write(raw)!=len(raw):raise OSError('Short probe receipt')
        stream.flush();os.fsync(stream.fileno())


def main():
    # Direct-file invocation: bind source BEFORE importing the checked package.
    mode,path,expected,*extra=sys.argv[1:]
    raw=Path(path).read_bytes()
    if len(raw)>131072 or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Registration pin mismatch')
    reg=json.loads(raw);root=Path(reg['source_root'])
    if Path(__file__).resolve()!=root/'experiments/digital_pilot74_owner_probe_v1.py':raise ValueError('Probe source origin')
    for name,pin in reg['source_files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=pin:raise ValueError('Source changed')
    sys.path.insert(0,str(root))
    from experiments import digital_pilot74_outer_owner_v1 as outer
    from experiments.digital_pilot74_durable_supervisor_v1 import Attempt,diagnostic
    from experiments.digital_pilot74_guardian_boundary_qualifier_v2 import kernel,birth
    case_root=Path(extra[0]);name=extra[1]
    if name not in reg['cases'] or case_root!=Path(reg['root'])/name:raise ValueError('Unregistered probe case')
    def nested(depth):
        command=[sys.executable,'-B',str(Path(__file__)), 'level',path,expected,str(case_root),name,str(depth)]
        result=outer.launch(dict(command=command,cwd=str(root),wall_ms=20000),lambda request:request['command']==command)
        if (result['exit_code']!=0 or not result['closure_observed'] or result['usage']['started_processes']!=depth+1):
            raise RuntimeError('Nested level did not complete expected exact topology')
        return result
    if mode=='level':
        depth=int(extra[2])
        if not 0<=depth<=2:raise ValueError('Finite topology only')
        if depth:value=nested(depth-1)
        else:
            k=kernel();own=k.OpenProcess(0x1000|0x100000,False,os.getpid())
            if not own:raise OSError('Leaf original identity unavailable')
            try:value=dict(leaf=True,pid=os.getpid(),creation_filetime_decimal=str(birth(k,own)))
            finally:k.CloseHandle(own)
        save(case_root/('level-'+str(depth)+'.json'),value)
        return
    if mode=='leaf-wait':
        time.sleep(60)
        return
    if mode!='case':raise ValueError('No generic command or World mode')
    if name=='ordinary':
        attempt=Attempt(case_root/'durable',expected)
        try:
            result=nested(2) # caller + three descendants == four contained
            attempt.write('terminal',dict(status='RETURNED',native=result,publication_accepted=False))
        finally:attempt.close()
        if attempt.cleanup_errors:raise OSError('Probe evidence handles not closed')
    elif name=='terminal-write-refusal':
        attempt=Attempt(case_root/'durable',expected)
        try:
            result=nested(0)
            attempt.handles['terminal'][1].close() # one sealed deterministic intervention
            try:attempt.write('terminal',dict(status='RETURNED',native=result))
            except (ValueError,OSError) as first:
                save(case_root/'write-refusal.json',dict(diagnostic=diagnostic(first),native=result,intervention='closed-terminal-handle-after-nested-closure',no_retry=True))
            else:raise AssertionError('Expected terminal write refusal absent')
        finally:attempt.close()
        return 79
    elif name=='caller-crash-live-child':
        command=[sys.executable,'-B',str(Path(__file__)),'leaf-wait',path,expected,str(case_root),name]
        child=subprocess.Popen(command,close_fds=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        k=kernel();creation=birth(k,int(child._handle))
        if k.WaitForSingleObject(int(child._handle),0)!=258:raise RuntimeError('Intervention child not live')
        own=k.OpenProcess(0x1000|0x100000,False,os.getpid())
        if not own:raise OSError('Caller original identity unavailable')
        try:caller=dict(pid=os.getpid(),creation_filetime_decimal=str(birth(k,own)))
        finally:k.CloseHandle(own)
        save(case_root/'child-before-crash.json',dict(pid=child.pid,creation_filetime_decimal=str(creation),command=command,caller=caller,child_wait_before_crash=258,expected_caller_exit=78))
        os._exit(78) # deliberately bypass Python cleanup; outer Job owns child
    else:raise ValueError('Unknown sealed case')
    return 0


if __name__=='__main__':raise SystemExit(main())
