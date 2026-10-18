"""Unqualified finite parent precharge/initial-commit evidence helpers.

No controller entrypoint, native launch, World import or execution authority.
The separate complete registered source/native/custody graph is still required.
"""
import os,stat,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from experiments.evidence_budget import Budget
from experiments import digital_pilot74_finite_inventory_v2 as inventory
from experiments import digital_pilot74_publication_reader_v2 as physical
MIB=1024**2

def encode(v):return physical.encode(v)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def utc():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def precharge(root):
    """All raw/failure/archive/restore leaves BEFORE any endpoint or grant."""
    root=Path(root);assert root.is_absolute() and root.resolve().is_relative_to(Path('D:/OraLab/runs').resolve())
    plan=inventory.plan()
    budget=Budget(root,dict(raw=1280*MIB,archive=1280*MIB,restore=1280*MIB,failure=128*MIB),3968*MIB)
    slots={}
    def reserve(phase,name,cap):
        with budget.create(phase,name,reserve=cap) as stream:path=stream.path
        info=physical.plain(path);assert info.st_size==0
        slots[phase+'/'+name]=dict(path=str(path),limit=cap,device=info.st_dev,inode=info.st_ino)
    for phase,rows in (('raw',plan['raw']),('failure',plan['failure'])):
        for row in rows:
            reserve(phase,row['name'],row['limit'])
            reserve('restore',phase+'/'+row['name'],row['limit'])
    reserve('archive','complete.zip',1280*MIB)
    assert budget.used['restore']<=1280*MIB
    write_empty(slots['raw/metadata/budget-before.json'],encode(budget.snapshot()))
    return budget,slots,plan

def write_empty(slot,raw):
    """One forward fsynced write; no truncate, retry or overwrite."""
    assert type(slot) is dict and set(slot)=={'path','limit','device','inode'}
    assert type(raw) is bytes and 0<len(raw)<=slot['limit']
    path=Path(slot['path']);assert path.is_absolute()
    chain=[(p,physical.identity_tuple(physical.plain(p,True))[:2]) for p in path.parents]
    old=physical.plain(path);assert old.st_size==0 and (old.st_dev,old.st_ino)==(slot['device'],slot['inode'])
    fd=os.open(path,os.O_RDWR|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    try:
        now=os.fstat(fd);assert stat.S_ISREG(now.st_mode) and now.st_nlink==1 and now.st_size==0 and (now.st_dev,now.st_ino)==(slot['device'],slot['inode'])
        if os.write(fd,raw)!=len(raw):raise OSError('Partial parent write retained; no retry')
        os.fsync(fd);last=os.fstat(fd);after=physical.plain(path)
        assert physical.identity_tuple(last)==physical.identity_tuple(after)==(slot['device'],slot['inode'],len(raw))
        for parent,identity in chain:assert physical.identity_tuple(physical.plain(parent,True))[:2]==identity
    finally:os.close(fd)
    spec=dict(path=str(path),extent=len(raw),sha256=digest(raw));assert physical.external(spec,slot['limit'])==raw
    return spec

def grant(slot,root,name,source_sha,config_sha,role):
    """Seal an already reserved leaf; never create a second reservation."""
    physical.checksum(source_sha);physical.checksum(config_sha)
    root=Path(root);assert root.is_absolute() and Path(slot['path'])==root/'raw'/name
    info=physical.plain(Path(slot['path']));assert info.st_size==0 and (info.st_dev,info.st_ino)==(slot['device'],slot['inode'])
    assert type(role) is str and role and role.isascii()
    result=dict(version='sharedlineage68-file-grant-candidate-v1',root=str(root),phase='raw',name=name,limit=slot['limit'],source_sha=source_sha,config_sha=config_sha,role=role,device=slot['device'],inode=slot['inode'])
    return dict(grant=result,seal=digest(encode(result)))

def initial_commit(directory,slots,capsule_raw,audit_raw,identity,role,receipt_slot,operator_lock):
    """Capture parent commit time at actual head replacement, never later."""
    from experiments import digital_pilot74_journal as journal
    assert Path(operator_lock['path'])==Path('D:/OraLab/state/operator.lock')
    def owner():
        raw,ident=physical.read_exact(operator_lock['path'],{k:operator_lock[k] for k in ('extent','sha256')},16384)
        assert ident[:2]==(operator_lock['device'],operator_lock['inode'])
    owner();directory=Path(directory);assert directory.is_absolute() and directory.resolve().is_relative_to(Path('D:/OraLab/runs').resolve())
    cap=physical.parse(capsule_raw,40*MIB);proof=physical.parse(audit_raw,128*1024)
    assert cap['identity']==identity and cap['state']['tick'] in (8192,9216,10240)
    seq={8192:1,9216:2,10240:3}[cap['state']['tick']]
    head=journal.head(capsule_raw,proof,seq);raw=encode(head)
    for name in (head['payload_name'],'head.json','head.pending'):
        assert Path(slots[name]['path'])==directory/name and physical.plain(directory/name).st_size==0
    write_empty(slots[head['payload_name']],capsule_raw);owner()
    write_empty(slots['head.pending'],raw);owner()
    before=physical.plain(directory/'head.json');assert before.st_size==0 and (before.st_dev,before.st_ino)==(slots['head.json']['device'],slots['head.json']['inode'])
    os.replace(directory/'head.pending',directory/'head.json');committed_at=utc()
    # Preserve replacement before any subsequent allocation/receipt can fail.
    info=physical.plain(directory/'head.json')
    commit=dict(head_ascii=raw.decode('ascii'),committed_at=committed_at,device=info.st_dev,inode=info.st_ino,tick=head['tick'])
    fd=os.open(directory/'head.pending',os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_BINARY',0));os.close(fd)
    pending=physical.plain(directory/'head.pending')
    receipt=dict(schema='PILOT74-INITIAL-COMMIT-RECEIPT-v2',role=role,identity=identity,commit=commit)
    spec=write_empty(receipt_slot,encode(receipt));owner()
    assert physical.external(dict(path=str(directory/'head.json'),extent=len(raw),sha256=digest(raw)),16384)==raw
    return dict(receipt=receipt,spec=spec,head_slot=dict(path=str(directory/'head.json'),limit=16384,device=info.st_dev,inode=info.st_ino),pending_slot=dict(path=str(directory/'head.pending'),limit=16384,device=pending.st_dev,inode=pending.st_ino))

def retain_native(slots,name,native):
    """Record the available native result BEFORE asserting success or size fit."""
    raw=encode(native);slot=slots['raw/native/'+name+'.json']
    target=slot if len(raw)<=slot['limit'] else slots['failure/native-first-failure.json']
    spec=write_empty(target,raw)
    # Available retained bytes are never mislabeled complete if the cap lost any.
    complete=native['output_truncated'] is False
    assert complete,'Native output loss: retained available prefix/result; evidence incomplete'
    assert target is slot,'Oversize native result retained in failure phase; stop, no retry'
    return spec
