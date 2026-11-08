"""Finite crash/recover/normal endpoints; parent qualification is still owed."""
import json,os,sys
from pathlib import Path
from experiments import digital_pilot74_journal as journal
from experiments import digital_pilot74_child as boundary
from experiments.digital_pilot74_custody import read_recording

MIB=1024**2
COMMON={'head.json':16384,'head.pending':16384,'observation.json':16384,'payload.pending':40*MIB,'capsule-2.json':32*MIB,'capsule-3.json':40*MIB}
REQUIRED=boundary.NEW_FILES|{'experiments/digital_pilot74_journal_child.py'}

def input_record(spec,cap):
    assert type(spec) is dict and set(spec)=={'path','extent','sha256'}
    assert type(spec['extent']) is int and 0<spec['extent']<=cap
    raw=read_recording(spec['path'],spec['extent'],spec['sha256'])
    from experiments.digital_pilot74_referee import _pairs
    value=json.loads(raw.decode('ascii'),object_pairs_hook=_pairs)
    assert journal.enc(value)==raw
    return raw,value

def shape(request):
    assert type(request) is dict and set(request)=={'configuration','revision','source_files','source_sha256','configuration_sha256','identity','kind','fault','role','directory','inputs','outputs'}
    assert journal.enc(request['configuration'])==journal.enc(boundary.CONFIG)
    assert request['kind'] in ('crash','recover','sequence')
    assert request['fault'] in ('partial','orphan','committed','normal')
    role='normal-sequence' if request['kind']=='sequence' else request['kind']+'/'+request['fault']
    assert request['role']==role and (request['kind']!='sequence' or request['fault']=='normal')
    assert type(request['revision']) is str and len(request['revision'])==40 and all(c in '0123456789abcdef' for c in request['revision'])
    assert type(request['source_files']) is dict and REQUIRED<=set(request['source_files'])
    assert request['source_sha256']==journal.sha(journal.enc(request['source_files']))
    assert request['configuration_sha256']==journal.sha(journal.enc(boundary.CONFIG))
    identity=dict(revision=request['revision'],source_sha256=request['source_sha256'],config_sha256=request['configuration_sha256'],law='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1')
    assert request['identity']==identity
    assert set(request['inputs'])=={kind+str(c) for kind in ('cut','audit') for c in (8192,9216,10240)}
    caps=dict(COMMON)
    caps['capsule-1.json' if request['kind']=='sequence' else 'recovery.json']=24*MIB if request['kind']=='sequence' else 40*MIB
    assert type(request['outputs']) is dict and set(request['outputs'])==set(caps)
    seen=[]
    for name,spec in request['outputs'].items():
        assert type(spec) is dict and set(spec)=={'limit','device','inode'}
        assert type(spec['limit']) is int and spec['limit']==caps[name]
        assert type(spec['device']) is int and type(spec['inode']) is int
        seen.append((spec['device'],spec['inode']))
    assert len(set(seen))==len(seen)
    return identity,caps

def admit(request):
    identity,caps=shape(request)
    root=Path.cwd();boundary.boundary.verify_source(root,request['source_files'])
    directory=Path(request['directory'])
    assert directory.is_absolute() and directory.resolve().is_relative_to(Path('D:/OraLab/runs').resolve())
    for p in (directory,*directory.parents):
        info=p.lstat();assert p.is_dir() and not p.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400
    for name,spec in request['outputs'].items():
        p=directory/name;info=p.lstat()
        assert p.is_file() and info.st_nlink==1 and not p.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400
        assert (info.st_dev,info.st_ino)==(spec['device'],spec['inode']) and info.st_size<=caps[name]
        if request['kind']!='recover':
            initial='capsule-1.json' if request['kind']=='sequence' else 'capsule-2.json'
            if name not in ('head.json',initial):assert info.st_size==0
        if name=='recovery.json':assert info.st_size==0
    audits={}
    for cut in (8192,9216,10240):
        raw,cap=input_record(request['inputs']['cut'+str(cut)],{8192:24*MIB,9216:32*MIB,10240:40*MIB}[cut])
        assert cap['version']=='DIGITAL-PILOT74-STATE-data-v1' and cap['identity']==identity and type(cap['state']['tick']) is int and cap['state']['tick']==cut and type(cap['state']['seed']) is int and cap['state']['seed']==3
        _,proof=input_record(request['inputs']['audit'+str(cut)],128*1024)
        assert proof['version']=='DIGITAL-PILOT74-AUDIT-v1' and proof['identity']==identity and type(proof['tick']) is int and proof['tick']==cut and proof['capsule_sha256']==journal.sha(raw) and type(proof['extent']) is int and proof['extent']==len(raw)
        assert proof['verified'] is True and proof['stage_credit'] is False and proof['engineering_only'] is True
        audits[str(cut)]=proof
    # Initial authority itself is authenticated before any VM import/hydration.
    authority,_,_=journal.select(directory,identity,audits)
    if request['kind']!='recover':assert authority['tick']==(8192 if request['kind']=='sequence' else 9216)
    else:assert authority['tick']==(9216 if request['fault'] in ('partial','orphan') else 10240)
    return directory,audits

def load_without_prefix(base,kernel,loader,raw,identity,proof,counts,forbidden):
    init,step,restore=base.World.__init__,base.World.step,base.World.__dict__['restore']
    def deny(which):
        def call(*a,**kw):forbidden[which]+=1;raise AssertionError('forbidden hydration '+which)
        return call
    try:
        base.World.__init__,base.World.step,base.World.restore=deny('genesis'),deny('prefix'),deny('restore')
        world=loader.hydrate(raw,identity,journal.sha(raw),proof,journal.sha(journal.enc(proof)))
        counts['hydrates']+=1
        assert type(world) is kernel.World and world.snapshot()==json.loads(raw)['state']
        assert counts['genesis']==counts['steps']==0 and not any(forbidden.values())
        return world
    finally:base.World.__init__,base.World.step,base.World.restore=init,step,restore

def main():
    raw=read_recording(sys.argv[1],int(sys.argv[2]),sys.argv[3]);request=json.loads(raw)
    assert journal.enc(request)==raw
    directory,audits=admit(request)
    if len(sys.argv)==5:
        assert sys.argv[4]=='prepared'
        print(journal.enc(dict(prepared_admission=True,genesis=0,steps=0,hydrates=0)).decode());return
    from experiments import digital_pilot74_loader as loader,digital_pilot74_population as kernel,digital_pressure71_population as base
    pins=request['source_files'];root=Path.cwd()
    def check():boundary.boundary.verify_source(root,pins);boundary.boundary.module_origins(root,pins)
    check();counts=dict(genesis=0,steps=0,hydrates=0);forbidden=dict(genesis=0,prefix=0,restore=0)
    authority,payload,proof=journal.select(directory,request['identity'],audits)
    original_step=base.World.step
    try:
        world=load_without_prefix(base,kernel,loader,payload,request['identity'],proof,counts,forbidden)
        del payload
        cut=world.tick;owner=journal.own_identity()
        def counted(w):counts['steps']+=1;return original_step(w)
        base.World.step=counted
        endpoints=(9216,10240) if request['kind']=='sequence' else (10240,)
        for endpoint in endpoints:
            while world.tick<endpoint:assert world.step(),'extinction closes qualification failed'
            terminal,reference=input_record(request['inputs']['cut'+str(endpoint)],40*MIB)
            assert world.snapshot()==reference['state']
            if request['kind'] in ('crash','sequence'):
                fault=request['fault'] if request['kind']=='crash' else 'normal'
                committed=journal.commit(directory,terminal,audits[str(endpoint)],fault,3 if endpoint==10240 else 2,audits)
                assert committed==(fault in ('committed','normal'))
            del reference,terminal
        assert counts==dict(genesis=0,steps=10240-cut,hydrates=1) and not any(forbidden.values());check()
        authority,_,_=journal.select(directory,request['identity'],audits)
        value=dict(role=request['role'],identity=request['identity'],owner=owner,counts=counts,forbidden_calls=forbidden,loaded_tick=cut,executed_tick=10240,authoritative_tick=authority['tick'],lost_instructions=10240-authority['tick'],exact_final_and_events=True,stage_credit=False,software_only=True)
        if request['kind']=='recover':
            value['final']=world.snapshot();journal.write(directory/'recovery.json',journal.enc(value),40*MIB)
        else:journal.write(directory/'observation.json',journal.enc(value),16384)
        check()
        if request['kind']=='crash' and request['fault']!='normal':os._exit(78)
        print(journal.enc({k:v for k,v in value.items() if k!='final'}).decode())
    except BaseException as error:
        print(journal.enc(dict(failed=True,error=repr(error),counts=counts,forbidden_calls=forbidden,unreceipted_state_unknown=True)).decode(),file=sys.stderr);raise
    finally:base.World.step=original_step
    check()

if __name__=='__main__':main()
