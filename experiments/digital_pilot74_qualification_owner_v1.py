"""Original-owner integration API. No issuer, scheduler, CLI or automatic launch.

The original registrar retains its real lock descriptor and obtains independent
review and an expiring grant before calling. One-shot claim is never removed.
Preparation/claim I/O precedes the measured outer launch and is cooperative host
custody, not a whole-machine resource confinement claim.
"""
import os,hashlib,stat
from pathlib import Path
from experiments import digital_pilot74_qualification_controller_v1 as controller
from experiments import digital_pilot74_qualification_admission_v1 as admission
from experiments import digital_pilot74_outer_owner_v1 as outer

def recheck_descriptor(owner_fd,lock):
    info=os.fstat(owner_fd)
    assert stat.S_ISREG(info.st_mode) and info.st_nlink==1
    assert (info.st_dev,info.st_ino,info.st_size)==(lock['device'],lock['inode'],lock['extent'])
    position=os.lseek(owner_fd,0,os.SEEK_CUR)
    try:
        os.lseek(owner_fd,0,os.SEEK_SET);raw=os.read(owner_fd,16385)
    finally:os.lseek(owner_fd,position,os.SEEK_SET)
    assert len(raw)==lock['extent']<=16384 and hashlib.sha256(raw).hexdigest()==lock['sha256']
    path=Path(lock['path']).lstat()
    assert (path.st_dev,path.st_ino,path.st_size)==(info.st_dev,info.st_ino,info.st_size)
    assert not stat.S_ISLNK(path.st_mode) and not getattr(path,'st_file_attributes',0)&0x400

def launch(spec,expected,owner_fd,closure_reserve_ms):
    assert type(closure_reserve_ms) is int and 0<closure_reserve_ms<3600000
    r=controller.validate_guardian(spec,expected)
    grant=admission.parsed(r['qualification']['grant'])
    assert grant['owner']['pid']==os.getpid()
    lock=r['operator_lock'];recheck_descriptor(owner_fd,lock)
    command=[r['python']['path'],'-B','-m','experiments.digital_pilot74_qualification_caller_v1',spec['path'],str(spec['extent']),spec['sha256']]
    request=dict(command=command,cwd=r['source_root'],wall_ms=3600000,closure_reserve_ms=closure_reserve_ms)
    plan=admission.parsed(r['qualification']['plan'])
    assert plan['closure_reserve_ms']==closure_reserve_ms
    assert plan['caller_module']=='experiments.digital_pilot74_qualification_caller_v1'
    # Claim precedes native entry; any subsequent exception seals this attempt.
    claim=Path(r['root']).parent/'qualification.claim'
    with claim.open('xb') as f:
        raw=controller.enc(dict(registration_sha256=expected,owner=grant['owner'],retry_permitted=False))
        assert f.write(raw)==len(raw);f.flush();os.fsync(f.fileno())
    def admit(actual):
        assert actual==request
        recheck_descriptor(owner_fd,lock)
        current=controller.validate_guardian(spec,expected)
        assert current['operator_lock']==lock
        current_grant=admission.parsed(current['qualification']['grant'])
        assert current_grant['owner']==grant['owner'] and current_grant['owner']['pid']==os.getpid()
        return True
    return outer.launch(request,admit)
