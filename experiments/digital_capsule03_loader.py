"""Candidate finite efficient hydration, requiring externally pinned audit data.

Not independently qualified; never a persistent runtime or activation API.
The parent must obtain the audit from the separately pinned literal referee and
bind its physical bytes/hash. A caller-supplied 'verified' flag alone is not proof.
No ancestry replay, constructor, policy edit or host-code decoding occurs here.
"""
import hashlib
import json
import os
import stat
from pathlib import Path
from experiments import digital_capsule03_data as boundary
from experiments import digital_longitudinal01_population as kernel

STATE_FIELDS=frozenset('_dose inheritance_mode fuel_mode turns offered admitted rejected next_packet seed mode tick last next_id writes constructor_remaining heat formation food free entities events births deaths maximum'.split())


def read_recording(path, extent, expected_sha256):
    """Trusted bounded filesystem custody, not adversarial confinement."""
    if type(extent) is not int or not 0 < extent <= 64*1024**2:
        raise ValueError('recording extent')
    path=Path(path)
    if not path.is_absolute():
        raise ValueError('absolute recording')
    def plain(candidate,directory=False):
        info=candidate.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('link/reparse recording')
        if directory:
            if not stat.S_ISDIR(info.st_mode):raise ValueError('plain parent')
        elif not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:
            raise ValueError('unshared regular recording')
        return info
    for parent in path.parents:plain(parent,True)
    before=plain(path)
    if before.st_size!=extent:raise ValueError('physical recording extent')
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    try:
        opened=os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink!=1 or (opened.st_dev,opened.st_ino,opened.st_size)!=(before.st_dev,before.st_ino,extent):
            raise ValueError('opened recording identity')
        chunks=[];remaining=extent
        while remaining:
            block=os.read(fd,min(65536,remaining))
            if not block:raise ValueError('short recording')
            chunks.append(block);remaining-=len(block)
        if os.read(fd,1):raise ValueError('overlong recording')
        after=plain(path);closed=os.fstat(fd)
        if (after.st_dev,after.st_ino,after.st_size)!=(before.st_dev,before.st_ino,extent) or closed.st_nlink!=1 or closed.st_size!=extent:
            raise ValueError('changed recording identity')
        raw=b''.join(chunks)
        if hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('recording hash')
        return raw
    finally:os.close(fd)


def hydrate(raw, expected_identity, expected_sha256, audit, expected_audit_sha256):
    """Load an independently authenticated cut7168/8192 without prefix execution."""
    audit_raw=json.dumps(audit,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
    if hashlib.sha256(audit_raw).hexdigest()!=expected_audit_sha256:
        raise ValueError('externally pinned audit custody')
    fields={'version','verified','identity','capsule_sha256','extent','state_sha256','tick','audit_prefix_instructions','summary','engineering_only','stage_credit'}
    if type(audit) is not dict or set(audit)!=fields or audit['version']!='DIGITAL-CAPSULE03-AUDIT-v1' or audit['verified'] is not True:
        raise ValueError('literal audit receipt')
    if audit['identity']!=expected_identity or audit['capsule_sha256']!=expected_sha256 or type(audit['extent']) is not int or audit['extent']!=len(raw):
        raise ValueError('audit capsule binding')
    if type(audit['tick']) is not int or audit['tick'] not in (7168,8192) or type(audit['audit_prefix_instructions']) is not int or audit['audit_prefix_instructions']!=audit['tick']:
        raise ValueError('frozen cut')
    if audit['engineering_only'] is not True or audit['stage_credit'] is not False:
        raise ValueError('qualification scope')
    state=boundary.decode_prepared(raw,expected_identity,expected_sha256,64*1024**2)
    # Numeric runtime map order differs from lexically sorted JSON string IDs.
    # Hash the wire representation, exactly as the unchanged snapshot does.
    wire=json.loads(json.dumps(state))
    if type(state) is not dict or set(state)!=STATE_FIELDS or boundary.digest(wire)!=audit['state_sha256'] or state['tick']!=audit['tick']:
        raise ValueError('audited exact state')
    if type(state['seed']) is not int or state['seed'] not in (3,4) or (state['mode'],state['inheritance_mode'],state['fuel_mode'])!=('faithful','parent_copy','renewed'):
        raise ValueError('frozen software configuration')
    if type(state['_dose']) is not int or state['_dose']!=8:raise ValueError('frozen dose')
    summary=audit['summary']
    expected=dict(verified=True,seed=state['seed'],dose=8,horizon=state['tick'],ticks=state['tick'],
                  software_only=True,scientific_admission=False,mode='faithful',
                  inheritance_mode='parent_copy',fuel_mode='renewed',stage_credit=False,selection=False)
    if type(summary) is not dict or any(type(summary.get(k)) is not type(v) or summary.get(k)!=v for k,v in expected.items()):
        raise ValueError('audit summary configuration/cut binding')
    world=object.__new__(kernel.World)
    world.__dict__.update(state)
    world.check()  # Bounded physical invariants, not prefix replay.
    if world.snapshot()!=wire:
        raise ValueError('hydrated exact state mismatch')
    return world
