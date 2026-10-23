"""Fresh reserved-closure qualification only; old failed attempts remain sealed.

No production registration/grant issuer. Preparation and postflight custody are
cooperative bounded original-owner writes, outside the measured native Job.
They are explicitly NOT hard whole-host I/O confinement. No scheduler/retry.
"""
import ctypes,hashlib,json,os,sys,time
from pathlib import Path
from experiments import digital_pilot74_outer_owner_v1 as outer
from experiments import digital_pilot74_guardian_boundary_qualifier_v2 as win
from experiments.digital_pilot74_durable_supervisor_v1 import ancestors,recheck,plain,read_slot,diagnostic

CASES=['reserved-closure-deadline']
LOCK=None
PRESERVED_LOCK=Path('D:/OraLab/state/operator.lock')


def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(pin,cap=131072):
    path=Path(pin['path']);chain=ancestors(path);identity=plain(path)
    with path.open('rb') as f:
        info=os.fstat(f.fileno());assert (info.st_dev,info.st_ino)==identity
        raw=f.read(cap+1)
        assert os.fstat(f.fileno()).st_size==len(raw)==pin['extent']<=cap
    recheck(chain);assert plain(path)==identity and sha(raw)==pin['sha256'];return raw
def pin(path):
    raw=path.read_bytes();return dict(path=str(path),extent=len(raw),sha256=sha(raw))
def write(path,value,cap=131072):
    raw=enc(value);assert len(raw)<=cap
    with path.open('xb') as f:
        assert f.write(raw)==len(raw);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==raw
    return pin(path)


def validate_grant(grant,registration,reg,now):
    assert grant['schema']=='PILOT74-NEW-OWNER-PROBE-GRANT-v1' and grant['verdict']=='PASS'
    assert grant['registration']==registration and grant['cases']==CASES
    assert grant['owner']==reg['owner'] and grant['operator_lock']==reg['operator_lock']
    assert grant['source_head']==reg['source_head'] and grant['source_files']==reg['source_files']
    assert grant['python']==reg['python'] and grant['argv_sha256']==reg['argv_sha256']
    assert grant['reviewer_identity'] and grant['review_evidence'] and grant['worlds']==0
    assert grant['production_admission'] is False
    assert reg['prepared_monotonic_ns']<=grant['issued_monotonic_ns']<=now
    assert now+60*10**9<=grant['expires_monotonic_ns']<=grant['issued_monotonic_ns']+300*10**9


def observed_closed(evidence):
    if type(evidence) is not dict:return False
    after=evidence.get('after_termination')
    return type(after) is dict and after.get('closure_observed') is True


def verify_deadline(evidence,intervention,command):
    assert observed_closed(evidence) and evidence['phase']=='wait'
    assert evidence['raw_wait_result']==258 and evidence['wall_limit_ms']==2000
    assert evidence['original_deadline_ms']==evidence['started_tick_ms']+2000
    assert evidence['closure_reserve_ms']==250
    assert evidence['soft_deadline_ms']==evidence['started_tick_ms']+1750
    assert evidence['soft_deadline_ms']<=evidence['observed_wait_tick_ms']<evidence['original_deadline_ms']
    assert evidence['closure_wait_result']==0 and evidence['caller_signal_within_original_budget'] is True
    assert evidence['closure_within_original_budget'] is True
    assert evidence['closure_observed_tick_ms']<=evidence['full_closure_observed_tick_ms']<=evidence['original_deadline_ms']
    assert evidence['elapsed_at_wait_ms']==evidence['observed_wait_tick_ms']-evidence['started_tick_ms']>=1750
    assert evidence['caller_exit_code'] is None and evidence['command']==command
    before=evidence['before_termination'];after=evidence['after_termination']
    assert before['pid']==intervention['pid'] and before['process_wait']==258
    assert before['creation_filetime_decimal']==intervention['creation_filetime_decimal']
    assert before['usage']['started_processes']==1 and before['usage']['active_before_close']==1
    assert before['pids']==[intervention['pid']] and before['observation_errors']==[]
    assert evidence['termination_requested'] is True
    assert evidence['owned_identity_snapshot_before_termination'] is None
    assert evidence['owned_identity_snapshot_skipped']=='soft deadline reached;reserved closure takes precedence'
    assert after['pid']==intervention['pid'] and after['creation_filetime_decimal']==intervention['creation_filetime_decimal']
    assert after['process_wait']==0 and after['usage']['started_processes']==1
    assert after['usage']['active_before_close']==0 and after['pids']==[] and after['observation_errors']==[]
    assert intervention['expected_intervention']=='original-owner-soft-stop-1750-hard-deadline-2000' and intervention['wait_seconds']==60


def preserved_failure_check(preserved):
    assert Path(preserved['path'])==PRESERVED_LOCK
    assert plain(PRESERVED_LOCK)==(preserved['device'],preserved['inode'])
    read(preserved)


def qualification_lock(root,path):
    root=Path(root);path=Path(path)
    if path!=root/'qualification-owner.lock' or path==PRESERVED_LOCK:
        raise ValueError('Fresh qualification-only owner lock required')
    ancestors(root)
    return path


def main():
    global LOCK
    # Plan pin and exact source are data prerequisites, not self-issued reviews.
    plan_path,expected=sys.argv[1:];raw=Path(plan_path).read_bytes();assert len(raw)<=131072 and sha(raw)==expected
    plan=json.loads(raw);assert enc(plan)==raw and plan['cases']==CASES and plan['worlds']==plan['vm_steps']==0
    root=Path(plan['root']);source=Path(plan['source_root'])
    assert root.is_absolute() and root.parent==Path('D:/OraLab/runs') and not root.exists()
    assert Path(__file__).resolve()==source/'experiments/digital_pilot74_reserved_closure_registration_v1.py'
    assert Path(sys.executable).resolve()==Path(plan['python']['path']).resolve()==Path('D:/OraLab/tools/Python312/python.exe')
    read(plan['python'],16*1024**2)
    def sources():
        for name,value in plan['source_files'].items():assert sha((source/name).read_bytes())==value
    sources();assert plan['native_process_cap']==1 and plan['controller_storage_cap']==8*1024**2
    LOCK=qualification_lock(root,plan['qualification_lock_path'])
    preserved=plan['preserved_failure_lock']
    preserved_failure_check(preserved)
    root.mkdir()
    k=win.kernel();own=k.OpenProcess(0x1000|0x100000,False,os.getpid());win.checked(own)
    fd=None;origin=None;original=None;first=None;closed=True
    try:
        creation=win.birth(k,own)
        # A foreign/old lock is never removed or adopted.
        fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_RDWR)
        owner=dict(pid=os.getpid(),creation_filetime_decimal=str(creation))
        body=enc(dict(schema='PILOT74-QUALIFICATION-OWNER-LOCK-v1',**owner));assert os.write(fd,body)==len(body);os.fsync(fd)
        info=os.fstat(fd);original=(info.st_dev,info.st_ino);origin=dict(**pin(LOCK),device=info.st_dev,inode=info.st_ino)
        def owner_check():
            preserved_failure_check(preserved)
            assert plain(LOCK)==original and read({q:origin[q] for q in ('path','extent','sha256')})==body
            assert k.WaitForSingleObject(own,0)==258 and win.birth(k,own)==creation
        owner_check()
        reg=dict(plan,owner=owner,operator_lock=origin,plan=pin(Path(plan_path)),argv_sha256=sha(enc(sys.argv)),prepared_monotonic_ns=time.monotonic_ns())
        registration=write(root/'registration.json',reg)
        print(enc(dict(waiting_for_independent_grant=True,registration=registration,owner=owner)).decode(),flush=True)
        deadline=time.monotonic()+300
        grant_path=root/'execution-grant.json'
        while not grant_path.exists():
            owner_check()
            if time.monotonic()>=deadline:raise TimeoutError('Fresh independent execution grant absent;no native probes')
            time.sleep(0.2)
        raw_grant=read(pin(grant_path));grant=json.loads(raw_grant);assert enc(grant)==raw_grant
        validate_grant(grant,registration,reg,time.monotonic_ns());sources();owner_check()
        write(root/'attempt.claimed.json',dict(registration=registration,grant=pin(grant_path),no_retry=True))
        results=[]
        for name in CASES:
            owner_check();sources();validate_grant(grant,registration,reg,time.monotonic_ns())
            case_root=root/name;case_root.mkdir()
            command=[sys.executable,'-B',str(source/'experiments/digital_pilot74_reserved_closure_probe_v1.py'),registration['path'],registration['sha256'],str(case_root)]
            request=dict(command=command,cwd=str(source),wall_ms=2000,closure_reserve_ms=250)
            try:
                closed=False
                result=outer.launch(request,lambda current: current==request and (owner_check() is None) and (sources() is None) and time.monotonic_ns()<grant['expires_monotonic_ns'])
            except BaseException as error:
                evidence=getattr(error,'guardian_failure_evidence',None)
                write(case_root/'owner-error.json',dict(diagnostic=diagnostic(error),native=evidence))
                closed=observed_closed(evidence)
                if not isinstance(error,TimeoutError) or not closed:raise
                intervention=json.loads((case_root/'before-wait.json').read_bytes())
                verify_deadline(evidence,intervention,command)
                assert read_slot(case_root/'durable/started.slot')['status']=='STARTED'
                try:read_slot(case_root/'durable/terminal.slot')
                except ValueError:pass
                else:raise AssertionError('Killed caller cannot claim complete terminal')
                result=dict(expected_caller_failure=True,native=evidence)
            else:
                closed=result['closure_observed']
                raise AssertionError('Deadline caller returned instead of timing out')
            write(case_root/'owner-result.json',result);results.append(dict(case=name,result=result))
            assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<=plan['controller_storage_cap']
        owner_check();sources();preserved_failure_check(preserved)
        write(root/'result.json',dict(collected=True,cases=results,worlds=0,production_resource_fit=False,natural_one_hour_deadline_tested=False,production_admission=False))
        print('NEW-only native probe panel collected;production admission remains false',flush=True)
    except BaseException as error:
        first=error
        try:write(root/'failure.json',dict(diagnostic=diagnostic(error),native_closure_known=closed,no_retry=True))
        except BaseException as later:
            try:error.add_note('Failure receipt unavailable: '+repr(later))
            except BaseException:pass
        raise
    finally:
        # Release only actual original lock and only after observed owned closure.
        try:
            if fd is not None:
                os.close(fd)
                if original is not None and closed:
                    assert plain(LOCK)==original and LOCK.read_bytes()==body
                    LOCK.unlink()
                    write(root/'lock-release.json',dict(original=origin,released=True))
        except BaseException as later:
            if first is not None:first.add_note('Original lock release UNKNOWN: '+repr(later))
            else:raise
        finally:
            try:win.checked(k.CloseHandle(own))
            except BaseException as later:
                if first is not None:
                    try:first.add_note('Original owner observation handle cleanup UNKNOWN: '+repr(later))
                    except BaseException:pass
                else:raise


if __name__=='__main__':main()
