from experiments.digital_pilot74_lock_scope_v1 import allowed as allowed_owner_lock
"""Bounded recorded-only PILOT74 publication builder and sealed file writer.

No VM, observer, network, autonomous owner or activation entrypoint. Calls are
refused until the separate parent has precharged/sealed all files and source.
"""
import hashlib,json,os,stat
from pathlib import Path
from datetime import datetime,timezone
MIB=1024**2

def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(b):return hashlib.sha256(b).hexdigest()
def integer(v,a,b):
    assert type(v) is int and a<=v<=b
    return v

def stamp(v):
    assert type(v) is str and len(v)==20
    d=datetime.strptime(v,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc);assert d.strftime('%Y-%m-%dT%H:%M:%SZ')==v
    return d

def decode(raw,cap):
    assert type(raw) is bytes and 0<len(raw)<=cap
    def pairs(items):
        d={}
        for k,v in items:assert k not in d;d[k]=v
        return d
    def bad(v):raise ValueError(v)
    result=json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=bad);assert enc(result)==raw
    def typed(v,depth=0):
        assert depth<=24
        if type(v) is dict:
            assert all(type(k) is str for k in v)
            for x in v.values():typed(x,depth+1)
        elif type(v) is list:
            for x in v:typed(x,depth+1)
        else:assert v is None or type(v) in (str,int,bool)
    typed(result);return result

def hexadecimal(v,n=64):assert type(v) is str and len(v)==n and all(c in '0123456789abcdef' for c in v)
def descriptor(name,raw):return dict(name=name,extent=len(raw),sha256=sha(raw))

def expected(raw,spec,cap):
    assert type(spec) is dict and set(spec)=={'extent','sha256'};integer(spec['extent'],1,cap);hexadecimal(spec['sha256'])
    assert type(raw) is bytes and len(raw)==spec['extent'] and sha(raw)==spec['sha256']
    return decode(raw,cap)

def process_identity(v):
    assert type(v) is dict and set(v)=={'pid','creation_filetime_decimal'};integer(v['pid'],1,2**32-1)
    t=v['creation_filetime_decimal'];assert type(t) is str and 1<=len(t)<=20 and t.isascii() and t.isdecimal() and str(int(t))==t and 0<int(t)<2**64

def build(projection,world_head_raw,capsule_raw,literal_audit_raw,process,*,identity,world_authority,committed_at,observation,published_at,verified_at):
    """Build ONLY; independent reader/literal/custody acceptance is still owed."""
    assert type(projection) is dict and type(projection['files']) is dict and projection['publication_accepted'] is False and projection['live_attachment'] is False
    assert set(identity)=={'run_id','world_id','source_revision','source_manifest_sha256','configuration_sha256'}
    for k in ('run_id','world_id'):
        x=identity[k];assert type(x) is str and x.isascii() and 1<=len(x)<=80 and all(c.isalnum() or c in '-_.' for c in x)
    hexadecimal(identity['source_revision'],40);hexadecimal(identity['source_manifest_sha256']);hexadecimal(identity['configuration_sha256'])
    pm=projection['manifest'];assert set(pm)=={'name','extent','sha256'}
    files=dict(projection['files']);mf=expected(files[pm['name']],{k:pm[k] for k in ('extent','sha256')},16384)
    assert set(mf)=={'schema','identity','sequence','mode','initial_state','genesis_summary','chunks','first_tick','last_tick','supplied_behavior','schematic_positioning'} and mf['schema']=='ora-pilot-event-manifest-v1' and mf['identity']==identity and mf['mode'] in ('fixture','recorded')
    seq=integer(mf['sequence'],1,3);cut={1:8192,2:9216,3:10240}[seq];assert type(mf['first_tick']) is int and type(mf['last_tick']) is int and (mf['first_tick'],mf['last_tick'])==(8192,cut)
    assert mf['supplied_behavior'] is True and mf['schematic_positioning'] is True and pm['name']=='manifest.'+format(seq,'06d')+'.json'
    refs=[(mf['initial_state'],65536),(mf['genesis_summary'],16384)]+[(x,MIB) for x in mf['chunks']]
    assert len(mf['chunks'])==(cut-8192)//128 and mf['initial_state']['name']=='initial.000001.json' and mf['genesis_summary']['name']=='genesis.000001.json'
    names={pm['name']}
    for d,cap in refs:
        name=d['name'];assert type(name) is str and name not in names and name in files;names.add(name);expected(files[name],{k:d[k] for k in ('extent','sha256')},cap)
    assert names==set(files)
    assert set(world_authority)=={'head','capsule','audit'}
    wh=expected(world_head_raw,world_authority['head'],16384);cap=expected(capsule_raw,world_authority['capsule'],40*MIB);proof=expected(literal_audit_raw,world_authority['audit'],128*1024)
    sid=dict(revision=identity['source_revision'],source_sha256=identity['source_manifest_sha256'],config_sha256=identity['configuration_sha256'],law='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1')
    assert set(wh)=={'version','sequence','tick','identity','payload_name','extent','sha256','audit_sha256'} and wh['version']=='DIGITAL-PILOT74-COMMIT-v1' and wh['identity']==sid
    assert type(wh['sequence']) is int and type(wh['tick']) is int and (wh['sequence'],wh['tick'])==(seq,cut) and wh['payload_name']=='capsule-'+str(seq)+'.json'
    assert wh['extent']==len(capsule_raw) and wh['sha256']==sha(capsule_raw) and wh['audit_sha256']==sha(literal_audit_raw)
    assert cap['version']=='DIGITAL-PILOT74-STATE-data-v1' and cap['identity']==sid and cap['state_sha256']==sha(enc(cap['state'])) and type(cap['state']['tick']) is int and cap['state']['tick']==cut
    assert proof['version']=='DIGITAL-PILOT74-AUDIT-v1' and proof['verified'] is True and proof['engineering_only'] is True and proof['stage_credit'] is False and proof['identity']==sid
    assert proof['capsule_sha256']==sha(capsule_raw) and type(proof['extent']) is int and proof['extent']==len(capsule_raw) and proof['state_sha256']==cap['state_sha256'] and type(proof['tick']) is int and proof['tick']==cut
    assert projection['raw_terminal_capsule_sha256']==sha(capsule_raw) and projection['raw_terminal_literal_audit_sha256']==sha(literal_audit_raw)
    commit=stamp(committed_at);pub=stamp(published_at);assert commit<=stamp(verified_at)<=pub
    assert type(observation) is dict and set(observation)=={'tick','at'}
    if observation['tick'] is None:assert observation['at'] is None
    else:integer(observation['tick'],cut,10240);assert commit<=stamp(observation['at'])<=pub
    assert type(process) is dict and set(process)=={'schema','identity','sequence','observed_at','producer','operator','process_status','reason'} and process['schema']=='ora-pilot-process-attestation-v1' and process['identity']==identity and type(process['sequence']) is int and process['sequence']==seq
    assert process['operator'] is None and type(process['reason']) is str and 1<=len(process['reason'])<=512 and process['reason'].isascii()
    if process['observed_at'] is not None:assert stamp(process['observed_at'])<=pub
    if process['process_status']=='unknown':assert process['producer'] is None
    else:assert process['process_status']=='stopped' and process['observed_at'] is not None;process_identity(process['producer'])
    status=dict(schema='ora-pilot-status-v1',mode=mf['mode'],live_attachment=False,identity=identity,sequence=seq,published_at=published_at,start_tick=8192,end_tick=10240,committed=dict(tick=cut,state_sha256=cap['state_sha256'],at=committed_at),observation=observation,process_status=process['process_status'])
    status_raw=enc(status);process_raw=enc(process)
    audit=dict(schema='ora-pilot-publication-audit-v2',identity=identity,sequence=seq,status_sha256=sha(status_raw),world_journal_head_sha256=sha(world_head_raw),committed_capsule_sha256=sha(capsule_raw),committed_literal_audit_sha256=sha(literal_audit_raw),process_sha256=sha(process_raw),event_manifest_sha256=pm['sha256'],scope='committed_literal_with_owner_reported_observation',verified_at=verified_at)
    head=dict(schema='ora-pilot-publication-head-v2',identity=identity,sequence=seq)
    for kind,raw in (('status',status_raw),('process',process_raw),('audit',enc(audit)),('event_manifest',files[pm['name']])):
        name=('manifest' if kind=='event_manifest' else kind)+'.'+format(seq,'06d')+'.json';assert len(raw)<=16384
        if name in files:assert files[name]==raw
        else:files[name]=raw
        for key,value in descriptor(name,raw).items():head[kind+'_'+key]=value
    head_raw=enc(head);assert len(head_raw)<=16384
    return dict(files=files,head=head_raw,publication_accepted=False,live_attachment=False)

def slot_limits():
    result={'initial.000001.json':65536,'genesis.000001.json':16384,'head.json':16384,'head.pending':16384}
    for i in range(1,17):result['events.000001.'+format(i,'04d')+'.json']=MIB
    for seq in (1,2,3):
        for kind in ('manifest','status','audit','process'):result[kind+'.'+format(seq,'06d')+'.json']=16384
    return result

def plain(path,directory=False):
    v=path.lstat();assert not stat.S_ISLNK(v.st_mode) and not getattr(v,'st_file_attributes',0)&0x400
    if directory:assert stat.S_ISDIR(v.st_mode)
    else:assert stat.S_ISREG(v.st_mode) and v.st_nlink==1
    return v

def ident(info):return (info.st_dev,info.st_ino)
def parents(path):return [(p,ident(plain(p,True))) for p in path.parents]
def recheck(items):
    for p,old in items:assert ident(plain(p,True))==old

def read_slot(path,expected_size,identity,cap):
    chain=parents(path);before=plain(path);assert ident(before)==identity and before.st_size==expected_size and 0<=expected_size<=cap
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    try:
        current=os.fstat(fd);assert stat.S_ISREG(current.st_mode) and current.st_nlink==1 and ident(current)==identity and current.st_size==expected_size
        data=[];left=expected_size
        while left:
            block=os.read(fd,min(left,65536));assert block;data.append(block);left-=len(block)
        assert not os.read(fd,1);after=plain(path);last=os.fstat(fd);assert ident(after)==ident(last)==identity and after.st_size==last.st_size==expected_size and last.st_nlink==1;recheck(chain)
        return b''.join(data)
    finally:os.close(fd)

def owner(grant):
    v=grant['operator_lock'];assert type(v) is dict and set(v)=={'path','extent','sha256','device','inode'} and allowed_owner_lock(v)
    integer(v['extent'],1,65536);assert type(v['device']) is int and type(v['inode']) is int;hexadecimal(v['sha256']);raw=read_slot(Path(v['path']),v['extent'],(v['device'],v['inode']),65536);assert sha(raw)==v['sha256']
    lock=json.loads(raw)
    if Path(v['path'])==Path('D:/OraLab/state/operator.lock'):
        assert set(lock)=={'pid','started_utc'} and type(lock['pid']) is int and lock['pid']>0 and type(lock['started_utc']) is str
        return
    # Non-production paths already require the native-bound exact QREG in
    # allowed_owner_lock. Authenticate its distinct body and current birth;
    # never reinterpret/adopt the preserved global production lock.
    from experiments import digital_pilot74_publication_reader_v2 as physical
    from experiments import digital_pilot74_guardian_v1 as guardian
    assert physical.parse(raw,16384)==lock
    assert set(lock)=={'schema','pid','creation_filetime_decimal'} and lock['schema']=='PILOT74-QUALIFICATION-OWNER-LOCK-v1'
    identity={k:lock[k] for k in ('pid','creation_filetime_decimal')};physical.process_id(identity)
    k=guardian._kernel();handle=k.OpenProcess(0x1000|0x100000,False,identity['pid']);guardian.checked(handle)
    first=None
    try:
        assert str(guardian._birth(k,handle))==identity['creation_filetime_decimal'] and k.WaitForSingleObject(handle,0)==258
    except BaseException as error:
        first=error;raise
    finally:
        try:guardian.checked(k.CloseHandle(handle))
        except BaseException as later:
            if first is None:raise
            guardian.failure_note(first,'Publication owner handle cleanup: ',later)

def write_slot(path,data,identity,limit,grant):
    assert type(data) is bytes and 0<len(data)<=limit;owner(grant);chain=parents(path);v=plain(path);assert ident(v)==identity
    if v.st_size:
        assert read_slot(path,v.st_size,identity,limit)==data,'Immutable publication differs';return False
    fd=os.open(path,os.O_RDWR|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    try:
        v=os.fstat(fd);assert stat.S_ISREG(v.st_mode) and v.st_nlink==1 and ident(v)==identity and v.st_size==0
        # A short write is a retained failure, not a retry/append/truncation.
        if os.write(fd,data)!=len(data):raise OSError('Partial publication write retained')
        os.fsync(fd);after=plain(path);last=os.fstat(fd);assert ident(after)==ident(last)==identity and after.st_size==last.st_size==len(data) and last.st_nlink==1;recheck(chain);owner(grant)
    finally:os.close(fd)
    assert read_slot(path,len(data),identity,limit)==data
    return True

def publish(grant,seal,source_sha256,configuration_sha256,publication,*,fault='none'):
    """ONE externally sealed/precharged owner operation, no retry or cleanup."""
    assert type(grant) is dict and set(grant)=={'version','root','source_sha256','configuration_sha256','role','operator_lock','slots','head_before'} and sha(enc(grant))==seal
    assert grant['version']=='PILOT74-PUBLICATION-WRITE-GRANT-v2' and grant['source_sha256']==source_sha256 and grant['configuration_sha256']==configuration_sha256
    hexadecimal(source_sha256);hexadecimal(configuration_sha256)
    assert fault in ('none','after_payloads','after_pending','after_head')
    assert grant['role']==('pilot74:owner-publication' if fault=='none' else 'pilot74:publication-prepared')
    root=Path(grant['root']);assert root.is_absolute() and root.resolve().is_relative_to(Path('D:/OraLab/runs').resolve());plain(root,True)
    limits=slot_limits();slots=grant['slots'];assert type(slots) is dict and set(slots)==set(limits)
    seen=[]
    for name,s in slots.items():
        assert type(s) is dict and set(s)=={'limit','device','inode'} and type(s['limit']) is int and s['limit']==limits[name] and type(s['device']) is int and type(s['inode']) is int
        ident_now=ident(plain(root/name));assert ident_now==(s['device'],s['inode']);seen.append(ident_now)
    assert len(set(seen))==len(seen);owner(grant)
    assert type(publication) is dict and set(publication)=={'files','head','publication_accepted','live_attachment'} and publication['publication_accepted'] is False and publication['live_attachment'] is False
    files=publication['files'];assert type(files) is dict and set(files)<=set(limits)-{'head.json','head.pending'}
    for name,data in files.items():assert type(data) is bytes and 0<len(data)<=limits[name]
    new_head=decode(publication['head'],16384);assert new_head['schema']=='ora-pilot-publication-head-v2'
    assert set(new_head)=={'schema','identity','sequence'}|{k+'_'+field for k in ('status','audit','process','event_manifest') for field in ('name','extent','sha256')}
    assert new_head['identity']['source_manifest_sha256']==source_sha256 and new_head['identity']['configuration_sha256']==configuration_sha256
    seq=integer(new_head['sequence'],1,3);needed={'initial.000001.json','genesis.000001.json'}|{'events.000001.'+format(i,'04d')+'.json' for i in range(1,(seq-1)*8+1)}|{k+'.'+format(seq,'06d')+'.json' for k in ('manifest','status','audit','process')};assert set(files)==needed
    for k in ('status','audit','process','event_manifest'):
        name=('manifest' if k=='event_manifest' else k)+'.'+format(seq,'06d')+'.json';assert new_head[k+'_name']==name and new_head[k+'_extent']==len(files[name]) and new_head[k+'_sha256']==sha(files[name])
    prior=grant['head_before'];assert type(prior) is dict and set(prior)=={'extent','sha256','device','inode'} and (prior['device'],prior['inode'])==(slots['head.json']['device'],slots['head.json']['inode'])
    integer(prior['extent'],0,16384);assert type(prior['device']) is int and type(prior['inode']) is int;hexadecimal(prior['sha256']);old=read_slot(root/'head.json',prior['extent'],(prior['device'],prior['inode']),16384);assert sha(old)==prior['sha256']
    if old:
        old_head=decode(old,16384);assert old_head['schema']=='ora-pilot-publication-head-v2' and old_head['identity']==new_head['identity'] and type(old_head['sequence']) is int and seq==old_head['sequence']+1
    else:assert seq==1
    assert plain(root/'head.pending').st_size==0
    receipts={}
    for name in sorted(files):
        s=slots[name];new=write_slot(root/name,files[name],(s['device'],s['inode']),s['limit'],grant);receipts[name]=dict(descriptor(name,files[name]),written=new,device=s['device'],inode=s['inode'])
    if fault=='after_payloads':raise RuntimeError('Prepared interruption after immutable payloads; retained')
    s=slots['head.pending'];write_slot(root/'head.pending',publication['head'],(s['device'],s['inode']),s['limit'],grant)
    if fault=='after_pending':raise RuntimeError('Prepared interruption after fsynced pending head; retained')
    chain=parents(root/'head.json');assert read_slot(root/'head.json',prior['extent'],(prior['device'],prior['inode']),16384)==old;owner(grant);recheck(chain)
    os.replace(root/'head.pending',root/'head.json')
    recheck(chain)
    if fault=='after_head':raise RuntimeError('Prepared interruption after atomic head replacement; retained')
    fd=os.open(root/'head.pending',os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_BINARY',0));os.close(fd)
    info=plain(root/'head.json');pending=plain(root/'head.pending');assert read_slot(root/'head.json',len(publication['head']),ident(info),16384)==publication['head'];owner(grant)
    return dict(schema='PILOT74-PUBLICATION-WRITE-RECEIPT-v2',grant_sha256=seal,sequence=seq,files=receipts,previous_head_ascii=old.decode('ascii'),head=dict(descriptor('head.json',publication['head']),device=info.st_dev,inode=info.st_ino),pending=dict(device=pending.st_dev,inode=pending.st_ino,extent=0),publication_accepted=False,live_attachment=False,stage_credit=False)
