"""Finite trusted-filesystem commit envelope; no VM or lock deletion API."""
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path

def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(path,cap):
    p=Path(path); info=p.lstat()
    assert info.st_nlink==1 and not p.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400
    assert 0<info.st_size<=cap
    raw=p.read_bytes();assert len(raw)==info.st_size
    return raw
def write(path,raw,cap):
    assert type(raw) is bytes and len(raw)<=cap
    p=Path(path);info=p.lstat()
    assert info.st_nlink==1 and not p.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400
    with p.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def birth(pid):
    """Read exact Windows process creation identity; failure stays UNKNOWN."""
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
    k.GetProcessTimes.restype=wintypes.BOOL;k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x1000,False,pid)
    if not h:return None
    try:
        times=[wintypes.FILETIME() for _ in range(4)]
        if not k.GetProcessTimes(h,*[ctypes.byref(t) for t in times]):return None
        return (times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
    finally:k.CloseHandle(h)
def owner_decision(expected,observed):
    if observed is None:return 'UNKNOWN'
    return 'ACTIVE' if expected==observed else 'REUSED'
def own_identity():
    pid=os.getpid();creation=birth(pid);assert type(creation) is int
    assert owner_decision(creation,birth(pid))=='ACTIVE'
    assert owner_decision(creation,creation+1)=='REUSED' and owner_decision(creation,None)=='UNKNOWN'
    return dict(pid=pid,creation_filetime=creation,actual_self_query=True,
                reused_and_unknown_prepared=True,stale_lock_removal=False)
CUTS={1:8192,2:9216,3:10240}
VERSION='DIGITAL-PILOT74-COMMIT-v1'
FIELDS={'version','sequence','tick','identity','payload_name','extent','sha256','audit_sha256'}

def _head(raw,expected_identity):
    value=json.loads(raw)
    assert enc(value)==raw and type(value) is dict and set(value)==FIELDS
    assert value['version']==VERSION and value['identity']==expected_identity
    sequence=value['sequence'];assert type(sequence) is int and sequence in CUTS
    assert type(value['tick']) is int and value['tick']==CUTS[sequence]
    assert value['payload_name']==f'capsule-{sequence}.json'
    assert type(value['extent']) is int and 0<value['extent']<=40*1024**2
    return value

def head(capsule,audit,sequence):
    assert type(sequence) is int and sequence in CUTS and type(capsule) is bytes and 0<len(capsule)<=40*1024**2
    value=json.loads(capsule);assert enc(value)==capsule
    assert value['version']=='DIGITAL-PILOT74-STATE-data-v1'
    assert type(value['state']['tick']) is int and value['state']['tick']==CUTS[sequence]
    assert audit['version']=='DIGITAL-PILOT74-AUDIT-v1' and audit['verified'] is True and audit['stage_credit'] is False and audit['engineering_only'] is True
    assert audit['identity']==value['identity'] and type(audit['tick']) is int and audit['tick']==CUTS[sequence]
    assert type(audit['extent']) is int and audit['extent']==len(capsule) and audit['capsule_sha256']==sha(capsule)
    return dict(version=VERSION,sequence=sequence,tick=CUTS[sequence],identity=value['identity'],
        payload_name=f'capsule-{sequence}.json',extent=len(capsule),sha256=sha(capsule),audit_sha256=sha(enc(audit)))

def select(directory,expected_identity,expected_audits):
    directory=Path(directory);authority=_head(read(directory/'head.json',16384),expected_identity)
    payload=read(directory/authority['payload_name'],40*1024**2)
    assert len(payload)==authority['extent'] and sha(payload)==authority['sha256']
    proof=expected_audits[str(authority['tick'])]
    assert sha(enc(proof))==authority['audit_sha256']
    assert head(payload,proof,authority['sequence'])==authority
    return authority,payload,proof

def commit(directory,payload,audit,fault,sequence,expected_audits):
    directory=Path(directory);assert fault in ('partial','orphan','committed','normal')
    new_head=head(payload,audit,sequence)
    previous,_,_=select(directory,new_head['identity'],expected_audits)
    assert sequence==previous['sequence']+1 and new_head['tick']>previous['tick']
    pending=directory/'payload.pending';new=directory/new_head['payload_name']
    # Caller precharges all paths. Never replace an earlier completed/orphan slot.
    for p in (pending,new,directory/'head.pending'):
        info=p.lstat();assert info.st_nlink==1 and p.is_file() and not p.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400 and info.st_size==0
    if fault=='partial':
        write(pending,payload[:len(payload)//2],40*1024**2);return False
    write(pending,payload,40*1024**2);os.replace(pending,new);pending.touch(exist_ok=False)
    if fault=='orphan':return False
    write(directory/'head.pending',enc(new_head),16384)
    os.replace(directory/'head.pending',directory/'head.json');(directory/'head.pending').touch(exist_ok=False)
    assert read(directory/'head.json',16384)==enc(new_head)
    return True
