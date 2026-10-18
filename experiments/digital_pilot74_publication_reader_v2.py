"""Independent bounded physical v2 reader; no producer/VM/writer imports.

External registration is the authority premise. Full literal projection proof
is separate paid work; this reader alone does not accept execution or liveness.
"""
import hashlib,json,os,stat
from pathlib import Path
from datetime import datetime,timezone
MIB=1024**2
CUTS={1:8192,2:9216,3:10240}

def encode(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def integer(v,low,high):
    assert type(v) is int and low<=v<=high
    return v

def checksum(v):
    assert type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v)
    return v

def timestamp(v):
    assert type(v) is str and len(v)==20
    d=datetime.strptime(v,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc);assert d.strftime('%Y-%m-%dT%H:%M:%SZ')==v
    return d

def parse(raw,cap):
    assert type(raw) is bytes and 0<len(raw)<=cap
    def pairs(items):
        result={}
        for k,v in items:assert k not in result;result[k]=v
        return result
    def bad(v):raise ValueError(v)
    value=json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=bad)
    assert encode(value)==raw
    def typed(v,depth=0):
        assert depth<=24
        if type(v) is dict:
            assert all(type(k) is str for k in v)
            for x in v.values():typed(x,depth+1)
        elif type(v) is list:
            for x in v:typed(x,depth+1)
        else:assert v is None or type(v) in (str,int,bool)
    typed(value);return value

def plain(path,directory=False):
    info=path.lstat();assert not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400
    if directory:assert stat.S_ISDIR(info.st_mode)
    else:assert stat.S_ISREG(info.st_mode) and info.st_nlink==1
    return info

def identity_tuple(info):return (info.st_dev,info.st_ino,info.st_size)

def read_exact(path,spec,cap):
    assert type(spec) is dict and set(spec)=={'extent','sha256'};extent=integer(spec['extent'],1,cap);checksum(spec['sha256'])
    path=Path(path);assert path.is_absolute()
    ancestors=[(p,identity_tuple(plain(p,True))[:2]) for p in path.parents]
    before=plain(path);assert before.st_size==extent
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    try:
        opened=os.fstat(fd);assert stat.S_ISREG(opened.st_mode) and opened.st_nlink==1 and identity_tuple(opened)==identity_tuple(before)
        blocks=[];left=extent
        while left:
            block=os.read(fd,min(left,65536));assert block;blocks.append(block);left-=len(block)
        assert not os.read(fd,1)
        after=plain(path);final=os.fstat(fd);assert identity_tuple(after)==identity_tuple(final)==identity_tuple(before) and final.st_nlink==1
        for parent,old in ancestors:assert identity_tuple(plain(parent,True))[:2]==old
        raw=b''.join(blocks);assert digest(raw)==spec['sha256'];return raw,identity_tuple(after)
    finally:os.close(fd)

def external(spec,cap):
    assert type(spec) is dict and set(spec)=={'path','extent','sha256'}
    return read_exact(spec['path'],{k:spec[k] for k in ('extent','sha256')},cap)[0]

def basename(value):
    assert type(value) is str and 1<=len(value)<=100 and value.isascii() and value not in ('.','..') and all(c.isalnum() or c in '-_.' for c in value) and '..' not in value
    return value

def process_id(v):
    assert type(v) is dict and set(v)=={'pid','creation_filetime_decimal'};integer(v['pid'],1,2**32-1)
    text=v['creation_filetime_decimal'];assert type(text) is str and 1<=len(text)<=20 and text.isascii() and text.isdecimal() and str(int(text))==text and 0<int(text)<2**64

def check_process(value,authority,identity,sequence):
    assert set(value)=={'schema','identity','sequence','observed_at','producer','operator','process_status','reason'} and value['schema']=='ora-pilot-process-attestation-v1'
    assert value['identity']==identity and type(value['sequence']) is int and value['sequence']==sequence and value['operator'] is None
    assert type(value['reason']) is str and 1<=len(value['reason'])<=512 and value['reason'].isascii()
    if value['observed_at'] is not None:timestamp(value['observed_at'])
    assert type(authority) is dict and set(authority)=={'kind','native','observation','command'}
    if authority['kind']=='unknown':
        assert authority['native'] is authority['observation'] is authority['command'] is None
        assert value['process_status']=='unknown' and value['producer'] is None;return
    assert authority['kind']=='stopped' and value['process_status']=='stopped' and value['observed_at'] is not None
    process_id(value['producer']);n=parse(external(authority['native'],MIB),MIB);o=parse(external(authority['observation'],16384),16384)
    assert type(authority['command']) is list and all(type(x) is str for x in authority['command']) and n['command']==authority['command']
    assert type(n['exit_code']) is int and n['exit_code'] in (0,78) and n['post_close_processes_exited'] is True and type(n['usage']['active_before_close']) is int and n['usage']['active_before_close']==0
    assert n['timed_out'] is False and n['output_truncated'] is False and value['producer']['pid'] in n['owned_pids_before_close']
    assert type(n['owned_pids_before_close']) is list and all(type(p) is int and p>0 for p in n['owned_pids_before_close'])
    owner=o['owner'];assert owner['actual_self_query'] is True and type(owner['pid']) is int and type(owner['creation_filetime']) is int
    assert value['producer']==dict(pid=owner['pid'],creation_filetime_decimal=str(owner['creation_filetime']))
    observed=n['observed_job_processes'];assert type(observed) is list and len(observed)<=64
    for member in observed:process_id(member)
    assert len({m['pid'] for m in observed})==len(observed) and value['producer'] in observed
    assert o['observed_at']==value['observed_at'] and o['identity']=={'revision':identity['source_revision'],'source_sha256':identity['source_manifest_sha256'],'config_sha256':identity['configuration_sha256'],'law':'DIGITAL-PILOT74-FINITE-QUALIFICATION-v1'}

def read_publication(root,registration,*,now=None,previous=None):
    """Return physically checked bytes for the SEPARATE literal projector."""
    r=registration
    assert type(r) is dict and set(r)=={'schema','identity','source_identity','sequence','mode','head','files','world','initial','owner_observation','process_authority'} and r['schema']=='PILOT74-PUBLICATION-REGISTRATION-v2'
    identity=r['identity'];source=r['source_identity'];assert type(identity) is dict and set(identity)=={'run_id','world_id','source_revision','source_manifest_sha256','configuration_sha256'}
    for key in ('run_id','world_id'):
        v=identity[key];assert type(v) is str and 1<=len(v)<=80 and v.isascii() and all(c.isalnum() or c in '-_.' for c in v)
    assert type(source) is dict and set(source)=={'revision','source_sha256','config_sha256','law'} and source==dict(revision=identity['source_revision'],source_sha256=identity['source_manifest_sha256'],config_sha256=identity['configuration_sha256'],law='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1')
    checksum(source['source_sha256']);checksum(source['config_sha256']);assert type(source['revision']) is str and len(source['revision'])==40 and all(c in '0123456789abcdef' for c in source['revision'])
    seq=integer(r['sequence'],1,3);cut=CUTS[seq];assert r['mode'] in ('fixture','recorded')
    assert type(r['files']) is dict
    for name in r['files']:basename(name)
    root=Path(root);assert root.is_absolute();plain(root,True)
    head_raw,head_id=read_exact(root/'head.json',r['head'],16384);head=parse(head_raw,16384)
    hf={'schema','identity','sequence'}|{k+'_'+s for k in ('status','audit','process','event_manifest') for s in ('name','extent','sha256')}
    assert set(head)==hf and head['schema']=='ora-pilot-publication-head-v2' and head['identity']==identity and type(head['sequence']) is int and head['sequence']==seq
    payload={};values={}
    for kind in ('status','audit','process','event_manifest'):
        name=head[kind+'_name'];expected=('manifest' if kind=='event_manifest' else kind)+'.'+format(seq,'06d')+'.json';assert basename(name)==expected
        spec=dict(extent=head[kind+'_extent'],sha256=head[kind+'_sha256']);assert r['files'][name]==spec
        raw,_=read_exact(root/name,spec,16384);payload[name]=raw;values[kind]=parse(raw,16384)
    status=values['status'];audit=values['audit'];process=values['process'];manifest=values['event_manifest']
    assert set(status)=={'schema','mode','live_attachment','identity','sequence','published_at','start_tick','end_tick','committed','observation','process_status'} and status['schema']=='ora-pilot-status-v1'
    assert status['mode']==r['mode'] and status['live_attachment'] is False and status['identity']==identity and type(status['sequence']) is int and status['sequence']==seq
    assert type(status['start_tick']) is int and type(status['end_tick']) is int and (status['start_tick'],status['end_tick'])==(8192,10240)
    published=timestamp(status['published_at']);world=r['world'];assert set(world)=={'head','capsule','audit','committed_at'}
    assert type(world['head']) is dict and set(world['head'])=={'path','extent','sha256'}
    whraw,whid=read_exact(world['head']['path'],{k:world['head'][k] for k in ('extent','sha256')},16384);wh=parse(whraw,16384)
    assert set(wh)=={'version','sequence','tick','identity','payload_name','extent','sha256','audit_sha256'} and wh['version']=='DIGITAL-PILOT74-COMMIT-v1' and wh['identity']==source
    assert type(wh['sequence']) is int and type(wh['tick']) is int and (wh['sequence'],wh['tick'])==(seq,cut) and wh['payload_name']=='capsule-'+str(seq)+'.json'
    assert Path(world['head']['path']).name=='head.json' and Path(world['capsule']['path'])==Path(world['head']['path']).parent/wh['payload_name']
    assert wh['extent']==world['capsule']['extent'] and wh['sha256']==world['capsule']['sha256'] and wh['audit_sha256']==world['audit']['sha256']
    capraw=external(world['capsule'],40*MIB);araw=external(world['audit'],128*1024);cap=parse(capraw,40*MIB);proof=parse(araw,128*1024)
    assert cap['version']=='DIGITAL-PILOT74-STATE-data-v1' and cap['identity']==source and type(cap['state']['tick']) is int and cap['state']['tick']==cut and cap['state_sha256']==digest(encode(cap['state']))
    assert proof['version']=='DIGITAL-PILOT74-AUDIT-v1' and proof['verified'] is True and proof['engineering_only'] is True and proof['stage_credit'] is False
    assert proof['identity']==source and proof['capsule_sha256']==digest(capraw) and type(proof['extent']) is int and proof['extent']==len(capraw) and proof['state_sha256']==cap['state_sha256'] and type(proof['tick']) is int and proof['tick']==cut
    committed_at=timestamp(world['committed_at']);assert published>=committed_at
    assert set(status['committed'])=={'tick','state_sha256','at'} and type(status['committed']['tick']) is int and status['committed']==dict(tick=cut,state_sha256=cap['state_sha256'],at=world['committed_at'])
    observation=status['observation'];assert type(observation) is dict and set(observation)=={'tick','at'} and observation==r['owner_observation']
    if observation['tick'] is None:assert observation['at'] is None
    else:integer(observation['tick'],cut,10240);assert committed_at<=timestamp(observation['at'])<=published
    check_process(process,r['process_authority'],identity,seq);assert status['process_status']==process['process_status']
    if process['observed_at'] is not None:assert timestamp(process['observed_at'])<=published
    af={'schema','identity','sequence','status_sha256','world_journal_head_sha256','committed_capsule_sha256','committed_literal_audit_sha256','process_sha256','event_manifest_sha256','scope','verified_at'}
    assert set(audit)==af and audit['schema']=='ora-pilot-publication-audit-v2' and audit['identity']==identity and type(audit['sequence']) is int and audit['sequence']==seq
    assert audit['status_sha256']==head['status_sha256'] and audit['process_sha256']==head['process_sha256'] and audit['event_manifest_sha256']==head['event_manifest_sha256']
    assert audit['world_journal_head_sha256']==digest(whraw) and audit['committed_capsule_sha256']==digest(capraw) and audit['committed_literal_audit_sha256']==digest(araw)
    assert audit['scope']=='committed_literal_with_owner_reported_observation' and committed_at<=timestamp(audit['verified_at'])<=published
    mf={'schema','identity','sequence','mode','initial_state','genesis_summary','chunks','first_tick','last_tick','supplied_behavior','schematic_positioning'}
    assert set(manifest)==mf and manifest['schema']=='ora-pilot-event-manifest-v1' and manifest['identity']==identity and type(manifest['sequence']) is int and manifest['sequence']==seq and manifest['mode']==r['mode']
    assert type(manifest['first_tick']) is int and type(manifest['last_tick']) is int and (manifest['first_tick'],manifest['last_tick'])==(8192,cut) and manifest['supplied_behavior'] is True and manifest['schematic_positioning'] is True
    assert type(r['initial']) is dict and set(r['initial'])=={'capsule','audit'}
    iraw=external(r['initial']['capsule'],40*MIB);iaraw=external(r['initial']['audit'],128*1024)
    initial=manifest['initial_state'];assert set(initial)=={'name','extent','sha256','cut','source_capsule_sha256','literal_audit_sha256'} and initial['name']=='initial.000001.json' and type(initial['cut']) is int and initial['cut']==8192 and initial['source_capsule_sha256']==digest(iraw) and initial['literal_audit_sha256']==digest(iaraw)
    refs=[(initial,65536),(manifest['genesis_summary'],16384)];assert set(manifest['genesis_summary'])=={'name','extent','sha256'} and manifest['genesis_summary']['name']=='genesis.000001.json'
    assert type(manifest['chunks']) is list and len(manifest['chunks'])==(cut-8192)//128
    for index,chunk in enumerate(manifest['chunks'],1):
        assert type(chunk) is dict and set(chunk)=={'name','extent','sha256','sequence','first_tick','last_tick','event_count','identity'}
        assert chunk['name']=='events.000001.'+format(index,'04d')+'.json' and chunk['identity']==identity and type(chunk['sequence']) is int and chunk['sequence']==index
        assert type(chunk['first_tick']) is int and type(chunk['last_tick']) is int and type(chunk['event_count']) is int and (chunk['first_tick'],chunk['last_tick'],chunk['event_count'])==(8193+128*(index-1),8192+128*index,128);refs.append((chunk,MIB))
    for item,limit in refs:
        name=basename(item['name']);spec={k:item[k] for k in ('extent','sha256')};assert name not in payload and r['files'][name]==spec
        payload[name]=read_exact(root/name,spec,limit)[0]
    assert set(payload)==set(r['files'])
    # No newer orphan can override either externally registered head.
    reread,reid=read_exact(root/'head.json',r['head'],16384);assert reread==head_raw and reid==head_id
    whagain,whagain_id=read_exact(world['head']['path'],{k:world['head'][k] for k in ('extent','sha256')},16384);assert whagain==whraw and whagain_id==whid
    if previous is not None:
        assert previous['identity']==identity and previous['sequence']<=seq and previous['committed_tick']<=cut
        if previous['sequence']==seq:assert previous['head_sha256']==digest(head_raw)
        else:assert seq==previous['sequence']+1
        assert published>=timestamp(previous['published_at'])
        if previous['observed_at'] is not None and observation['at'] is not None:assert timestamp(observation['at'])>=timestamp(previous['observed_at'])
    ages=dict(publication_ms=None,observation_ms=None,commit_ms=None)
    if now is not None:
        clock=timestamp(now);assert clock>=published
        ages['publication_ms']=int((clock-published).total_seconds()*1000);ages['commit_ms']=int((clock-committed_at).total_seconds()*1000)
        if observation['at'] is not None:ages['observation_ms']=int((clock-timestamp(observation['at'])).total_seconds()*1000)
    freshness='unknown' if any(ages[k] is None for k in ('publication_ms','observation_ms')) else 'stale' if any(ages[k]>30000 for k in ('publication_ms','observation_ms')) else 'fresh'
    projected={name:raw for name,raw in payload.items() if name not in (head['status_name'],head['audit_name'],head['process_name'])}
    return dict(schema='PILOT74-PHYSICAL-PUBLICATION-v2',physical_integrity=True,projection_verified=False,identity=identity,sequence=seq,head_sha256=digest(head_raw),committed_tick=cut,published_at=status['published_at'],observed_at=observation['at'],uncommitted_gap=None if observation['tick'] is None else observation['tick']-cut,ages=ages,freshness=freshness,process_status=process['process_status'],projection_files=projected,raw_inputs=dict(initial_capsule=iraw,initial_audit=iaraw,terminal_capsule=capraw,terminal_audit=araw),publication_accepted=False,live_attachment=False,stage_credit=False)
