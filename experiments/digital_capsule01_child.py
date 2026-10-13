"""Finite seven-role exact persistence01 adapter. Requires external admission.

Source/configuration, grants, operator ownership, caps and custody are parent
responsibilities. No service/activation interface or scientific bank exists.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

CONFIG=dict(version='DIGITAL-EXACT-PERSISTENCE-QUALIFICATION-01',seed=1,mode='faithful',
            inheritance_mode='parent_copy',fuel_mode='renewed',endpoint=512,cuts=[64,256])
ROLES=('reference','cut64','cut256','prepared','referee','resume64','resume256')


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def sha(value):return hashlib.sha256(value).hexdigest()


def main():
    request=json.loads(Path(sys.argv[1]).read_bytes())
    assert request['configuration']==CONFIG and type(request['configuration']['seed']) is int
    role=request['role'];assert role in ROLES
    root=Path.cwd();pins=request['source_files']
    assert all(sha((root/name).read_bytes())==digest for name,digest in pins.items())
    source_sha=sha(canonical(pins));config_sha=sha(canonical(CONFIG))
    identity=dict(revision=request['revision'],source_sha256=source_sha,config_sha256=config_sha,law='DIGITAL-SHARED-LINEAGE-68-v1')
    assert identity==request['identity']
    from experiments import evidence_write_grant68 as transport
    from experiments import digital_capsule01_data as boundary
    from experiments import digital_capsule01_loader as loader
    from experiments import digital_capsule01_referee as referee
    from experiments import digital_capsule01_custody as custody
    from experiments import digital_sharedlineage68_population as kernel
    constructors=hydrations=steps=0
    original_init=kernel.World.__init__;original_new=kernel.World.__new__;original_step=kernel.World.step
    def counted_init(self,*args,**kwargs):
        nonlocal constructors
        constructors+=1;return original_init(self,*args,**kwargs)
    def counted_step(self):
        nonlocal steps
        steps+=1;return original_step(self)
    kernel.World.__init__=counted_init;kernel.World.step=counted_step
    def capsule(state):return dict(version=boundary.VERSION,identity=identity,state=state,state_sha256=boundary.digest(state))
    def read(spec,independent=False):
        reader=custody.read_recording if independent else loader.read_recording
        raw=reader(spec['path'],spec['extent'],spec['sha256'])
        value=json.loads(raw.decode('ascii'),object_pairs_hook=referee._pairs)
        assert canonical(value)==raw
        return raw,value
    if role in ('reference','cut64','cut256'):
        world=kernel.World(1,'faithful','ancestor','renewed','parent_copy')
        endpoint=512 if role=='reference' else int(role[3:]);cuts={}
        while world.tick<endpoint:
            assert world.step()
            if role=='reference' and world.tick in (64,256):cuts[str(world.tick)]=capsule(world.snapshot())
        value=capsule(world.snapshot())
        if role=='reference':value=dict(identity=identity,configuration=CONFIG,final=value,cuts=cuts)
        assert constructors==1 and steps==endpoint
    elif role=='referee':
        _,reference=read(request['inputs']['reference'],True)
        assert reference['identity']==identity and reference['configuration']==CONFIG and set(reference['cuts'])=={'64','256'}
        final=reference['final'];raw=canonical(final)
        final_audit=referee.verify_capsule(raw,identity,sha(raw),len(raw));assert final_audit['tick']==512
        cut_audits={}
        for cut in (64,256):
            raw,item=read(request['inputs']['cut'+str(cut)],True)
            assert item==reference['cuts'][str(cut)]
            proof=referee.verify_capsule(raw,identity,sha(raw),len(raw));assert proof['tick']==cut
            cut_audits[str(cut)]=proof
        value=dict(identity=identity,configuration=CONFIG,reference_audit=final_audit,cut_audits=cut_audits,
                   literal_prefix_instructions=832,verified=True,stage_credit=False)
        assert constructors==steps==0
    elif role=='prepared':
        from copy import deepcopy
        from unittest.mock import patch
        raw,item=read(request['inputs']['cut64'],True)
        refused=[]
        cases=[]
        def altered(name,edit):
            changed=deepcopy(item);edit(changed)
            changed['state_sha256']=referee.h(changed['state']);cases.append((name,canonical(changed)))
        altered('formation_genome',lambda x:x['state']['formation'][0].update(value=0))
        altered('paid_copy_ancestry',lambda x:x['state']['events'][0].update(before='0'*64))
        altered('register',lambda x:x['state']['entities']['0']['registers'].__setitem__(0,15))
        altered('cursor',lambda x:x['state'].update(writes=x['state']['writes']+1))
        altered('scheduler',lambda x:x['state'].update(last=-1))
        altered('ledger',lambda x:x['state'].update(heat=x['state']['heat']+1))
        altered('missing_state',lambda x:x['state'].pop('free'))
        altered('extra_state',lambda x:x['state'].update(host_command='disabled'))
        altered('bool_seed',lambda x:x['state'].update(seed=True))
        altered('missing_history',lambda x:x['state']['events'].pop())
        altered('duplicate_material',lambda x:x['state']['free'].__setitem__(0,x['state']['free'][1]))
        altered('wrong_config',lambda x:x['identity'].update(config_sha256='0'*64))
        cases.extend([('duplicate_JSON',raw.replace(b'"tick":64',b'"tick":64,"tick":64')),
                      ('truncated',raw[:-1]),('altered_byte',raw+b'x')])
        # Literal referee remains independent even if loader/boundary helpers lie.
        with patch.object(boundary,'decode_prepared',return_value=item['state']),patch.object(loader,'hydrate',return_value=object()),patch.object(kernel.World,'__init__',side_effect=AssertionError('constructor forbidden')):
            for name,bad in cases:
                try:referee.verify_capsule(bad,identity,sha(bad),len(bad))
                except (AssertionError,ValueError,KeyError,IndexError,TypeError):refused.append(name)
                else:raise AssertionError('forged capsule accepted: '+name)
        # Prepared lstat witnesses only. Actual OS link/reparse privilege and
        # adversarial confinement are NOT qualified by these negative fixtures.
        import stat
        from types import SimpleNamespace
        physical=[]
        leaf=Path(request['inputs']['cut64']['path'])
        base=dict(st_dev=1,st_ino=1,st_size=len(raw),st_nlink=1,st_file_attributes=0)
        witnesses={'symlink':dict(base,st_mode=stat.S_IFLNK),
                   'reparse':dict(base,st_mode=stat.S_IFREG,st_file_attributes=0x400),
                   'hardlink':dict(base,st_mode=stat.S_IFREG,st_nlink=2),
                   'short_extent':dict(base,st_mode=stat.S_IFREG,st_size=len(raw)-1)}
        for name,info in witnesses.items():
            def lstat(candidate):
                return SimpleNamespace(**(info if candidate==leaf else dict(base,st_mode=stat.S_IFDIR)))
            for label,reader in [('loader',loader.read_recording),('referee',custody.read_recording)]:
                with patch.object(Path,'lstat',lstat),patch.object(loader.os,'open',side_effect=AssertionError('unsafe open reached')):
                    try:reader(leaf,len(raw),sha(raw))
                    except (ValueError,OSError):physical.append(name+':'+label)
                    else:raise AssertionError('unsafe recording accepted: '+name)
        value=dict(identity=identity,verified=True,forged_refusals=refused,physical_refusals=physical,
                   producer_helper_corruption_trap=True,physical_cases_prepared_only=True,
                   world_constructors=constructors,steps=steps,stage_credit=False)
        assert len(refused)==15 and len(physical)==8 and constructors==steps==0
    else:
        cut=int(role[6:]);raw,item=read(request['inputs']['cut'+str(cut)])
        _,proofs=read(request['inputs']['referee'])
        assert proofs['identity']==identity and proofs['configuration']==CONFIG and proofs['verified'] is True
        proof=proofs['cut_audits'][str(cut)];assert sha(canonical(proof))==request['audit_sha256']
        def no_init(*args,**kwargs):raise AssertionError('genesis constructor during load')
        def no_step(*args,**kwargs):raise AssertionError('prefix step during load')
        def no_restore(*args,**kwargs):raise AssertionError('genesis restore during load')
        before=time.perf_counter()
        # Constructor, prefix-step and old restore traps stay active THROUGH load.
        kernel.World.__init__=no_init;kernel.World.step=no_step;kernel.World.restore=no_restore
        world=loader.hydrate(raw,identity,sha(raw),proof,request['audit_sha256']);hydrations+=1
        elapsed=time.perf_counter()-before
        assert world.snapshot()==item['state'] and constructors==steps==0
        kernel.World.step=counted_step
        while world.tick<512:assert world.step()
        final=capsule(world.snapshot())
        _,reference=read(request['inputs']['reference']);assert final==reference['final']
        value=dict(identity=identity,configuration=CONFIG,cut=cut,final=final,
                   loading=dict(capsule_bytes=len(raw),elapsed_seconds=elapsed,constructor_calls=constructors,
                                prefix_step_calls=0,hydrations=hydrations,retained_events=cut),
                   suffix_steps=steps,exact_final_and_complete_events=True,stage_credit=False)
        assert steps==512-cut
    assert all(sha((root/name).read_bytes())==digest for name,digest in pins.items())
    manifest=transport.record(request['grant'],request['grant_seal'],source_sha,config_sha,role,value)
    manifest.update(role=role,world_constructors=constructors,hydrations=hydrations,ordinary_steps=steps,
                    software_only=True,stage_credit=False)
    print(canonical(manifest).decode('ascii'))


if __name__=='__main__':main()
