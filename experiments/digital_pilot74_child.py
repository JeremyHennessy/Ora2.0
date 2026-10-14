"""Finite source/grant-bound PILOT74 endpoints; no activation API."""
import hashlib,json,sys,time
from pathlib import Path
from experiments import digital_pressure71_scientific_child as boundary

CONFIG=dict(version='DIGITAL-PILOT74-NATIVE-qualification-v1',seeds=[3],cuts=[8192,9216,10240],horizon=10240,mode='faithful',inheritance_mode='parent_copy',fuel_mode='renewed',dose=8,software_only=True)
MIB=1024**2
NEW_FILES={'experiments/digital_pilot74_'+n+'.py' for n in ('data','loader','referee','child','custody','journal')}|{'experiments/digital_pilot74_population.py','experiments/digital_pilot74_custody.py'}
def canonical(v):return boundary.canonical(v)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def admit(request):
    assert type(request) is dict and set(request)=={'configuration','revision','source_files','source_sha256','configuration_sha256','seed','export','kind','cut','role','inputs','outputs'}
    assert canonical(request['configuration'])==canonical(CONFIG)
    assert type(request['seed']) is int and request['seed'] ==3
    assert request['export'] in ('original','restored') and request['kind'] in ('generate','audit','resume')
    cut=request['cut'];kind=request['kind']
    assert (cut is None if kind=='generate' else type(cut) is int and cut in (8192,9216,10240))
    role=f"{request['export']}:{request['seed']}:{kind}"+('' if kind=='generate' else ':'+str(cut))
    assert request['role']==role
    assert type(request['revision']) is str and len(request['revision'])==40 and all(c in '0123456789abcdef' for c in request['revision'])
    assert NEW_FILES<=set(request['source_files'])
    assert request['source_sha256']==sha(canonical(request['source_files']))
    assert request['configuration_sha256']==sha(canonical(CONFIG))
    assert set(request['inputs'])==({'capsule'} if kind=='audit' else {'capsule','audit','reference'} if kind=='resume' else set())
    assert set(request['outputs'])==({'8192','9216','10240'} if kind=='generate' else {'main'})
    output_identities=[]
    for label,item in request['outputs'].items():
        assert type(item) is dict and set(item)=={'grant','seal'}
        cap=40*MIB if kind=='generate' or kind=='resume' and cut in (8192,9216) else 128*1024 if kind=='audit' else 8*1024
        out_role=role+':'+label if kind=='generate' else role
        grant_request=dict(grant=item['grant'],grant_seal=item['seal'],configuration_sha256=request['configuration_sha256'],role=out_role)
        boundary.validate_grant(grant_request,request['source_sha256'],'proof' if kind=='audit' else 'raw')
        assert item['grant']['limit']<=cap
        output_identities.append((item['grant']['device'],item['grant']['inode']))
    assert len(set(output_identities))==len(output_identities)
    return role

def read_input(spec,cap):
    assert type(spec) is dict and set(spec)=={'path','extent','sha256'}
    assert type(spec['extent']) is int and 0<spec['extent']<=cap
    from experiments.digital_pilot74_custody import read_recording
    raw=read_recording(spec['path'],spec['extent'],spec['sha256'])
    from experiments.digital_pilot74_referee import _pairs
    value=json.loads(raw.decode('ascii'),object_pairs_hook=_pairs)
    assert canonical(value)==raw
    return raw,value

def main():
    request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),MIB));role=admit(request)
    root=Path.cwd();pins=request['source_files'];boundary.verify_source(root,pins)
    from experiments import evidence_write_grant68 as transport
    identity=dict(revision=request['revision'],source_sha256=request['source_sha256'],config_sha256=request['configuration_sha256'],law='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1')
    kind=request['kind'];cut=request['cut'];counts=dict(genesis=0,ordinary_steps=0,hydrations=0);loading=None
    forbidden_calls=dict(genesis=0,prefix_steps=0,restore=0)
    def record(label,value):
        item=request['outputs'][label];out_role=role+':'+label if kind=='generate' else role
        return transport.record(item['grant'],item['seal'],request['source_sha256'],request['configuration_sha256'],out_role,value)
    if kind=='audit':
        # Independent proof imports neither VM, loader nor shared data validator.
        from experiments import digital_pilot74_referee as referee
        raw,item=read_input(request['inputs']['capsule'],40*MIB)
        assert item['state']['seed']==request['seed'] and item['state']['tick']==cut
        value=referee.verify_capsule(raw,identity,sha(raw),len(raw))
        assert 'experiments.digital_pressure71_population' not in sys.modules
        manifests={'main':record('main',value)}
    else:
        from experiments import digital_pressure71_population as base,digital_pilot74_population as kernel,digital_pilot74_data as data
        old_init,old_step,old_restore=base.World.__init__,base.World.step,base.World.__dict__['restore']
        def counted_init(self,*a,**kw):counts['genesis']+=1;return old_init(self,*a,**kw)
        def counted_step(self):counts['ordinary_steps']+=1;return old_step(self)
        base.World.__init__,base.World.step=counted_init,counted_step
        try:
            if kind=='generate':
                world=kernel.World(request['seed'],'faithful','ancestor','renewed','parent_copy',dose=8)
                checkpoint=None;manifests={}
                while world.tick<10240:
                    assert world.step(),'fixture extinction retained as failure'
                    if world.tick==64:checkpoint=world.snapshot()
                    if world.tick in (8192,9216,10240):
                        state=world.snapshot();value=dict(version=data.VERSION,identity=identity,checkpoint64=checkpoint,state=state,state_sha256=data.digest(state))
                        manifests[str(world.tick)]=record(str(world.tick),value)
                assert counts==dict(genesis=1,ordinary_steps=10240,hydrations=0)
            else:
                from experiments import digital_pilot74_loader as loader
                raw,item=read_input(request['inputs']['capsule'],40*MIB)
                audit_raw,proof=read_input(request['inputs']['audit'],128*1024)
                assert item['identity']==identity and item['state']['seed']==request['seed'] and item['state']['tick']==cut
                def no_init(*a,**kw):forbidden_calls['genesis']+=1;raise AssertionError('genesis during hydration')
                def no_step(*a,**kw):forbidden_calls['prefix_steps']+=1;raise AssertionError('prefix step during hydration')
                def no_restore(*a,**kw):forbidden_calls['restore']+=1;raise AssertionError('historical restore during hydration')
                base.World.__init__,base.World.step,base.World.restore=no_init,no_step,no_restore
                before=time.perf_counter();world=loader.hydrate(raw,identity,sha(raw),proof,sha(audit_raw));elapsed=time.perf_counter()-before
                counts['hydrations']+=1;assert type(world) is kernel.World and world.snapshot()==item['state']
                assert counts['genesis']==counts['ordinary_steps']==0
                base.World.step=counted_step
                while world.tick<10240:
                    assert world.step(),'resumed fixture extinction retained as failure'
                final=world.snapshot();_,reference=read_input(request['inputs']['reference'],40*MIB)
                assert reference['identity']==identity and reference['state']['seed']==request['seed'] and reference['state']['tick']==10240
                assert final==reference['state'] and counts['ordinary_steps']==10240-cut
                final_raw=canonical(final)
                value=dict(version=CONFIG['version'],identity=identity,seed=request['seed'],cut=cut,terminal=10240,state_sha256=sha(final_raw),state_extent=len(final_raw),exact_final_and_events=True,prefix_step_calls=0,genesis_calls=0,hydrations=1,suffix_steps=10240-cut,stage_credit=False)
                if cut in (8192,9216):value['final']=final
                manifests={'main':record('main',value)}
                loading=dict(capsule_bytes=len(raw),elapsed_seconds=elapsed,retained_events=cut)
        except BaseException as error:
            print(canonical(dict(failed=True,role=role,counts=counts,forbidden_calls=forbidden_calls,error=repr(error),partial_state_unavailable=True,stage_credit=False)).decode(),file=sys.stderr)
            raise
        finally:
            base.World.__init__,base.World.step,base.World.restore=old_init,old_step,old_restore
    boundary.module_origins(root,pins);boundary.verify_source(root,pins)
    print(canonical(dict(role=role,identity=identity,manifests=manifests,counts=counts,forbidden_calls=forbidden_calls,loading=loading,software_only=True,scientific_acceptance=False,stage_credit=False)).decode())

if __name__=='__main__':main()
