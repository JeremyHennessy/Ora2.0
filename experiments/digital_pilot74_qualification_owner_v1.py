"""Original-owner integration API. No issuer, scheduler, CLI or automatic launch.

The original registrar retains its real lock descriptor and obtains independent
review and an expiring grant before calling. One-shot claim is never removed.
Preparation/claim I/O precedes the measured outer launch and is cooperative host
custody, not a whole-machine resource confinement claim.
"""
import os
from pathlib import Path
from experiments import digital_pilot74_qualification_controller_v1 as controller
from experiments import digital_pilot74_qualification_admission_v1 as admission
from experiments import digital_pilot74_outer_owner_v1 as outer

def launch(spec,expected,owner_fd,closure_reserve_ms):
    assert type(closure_reserve_ms) is int and 0<closure_reserve_ms<3600000
    r=controller.validate_guardian(spec,expected)
    grant=admission.parsed(r['qualification']['grant'])
    assert grant['owner']['pid']==os.getpid()
    fd=os.fstat(owner_fd);lock=r['operator_lock']
    assert (fd.st_dev,fd.st_ino)==(lock['device'],lock['inode'])
    assert fd.st_size==lock['extent']
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
        assert actual==request and os.fstat(owner_fd).st_ino==lock['inode']
        controller.validate_guardian(spec,expected)
        return True
    return outer.launch(request,admit)
