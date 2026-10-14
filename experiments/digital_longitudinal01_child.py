"""Source/grant-bound finite engineering endpoint; no activation/science bank."""
import hashlib,json,sys
from pathlib import Path
from experiments import digital_pressure71_scientific_child as boundary

CONFIG=dict(version='DIGITAL-FINITE-LONGITUDINAL-ECOLOGY-01-engineering-v1',
    seeds=[3,4],horizon=8192,mode='faithful',route='ancestor',fuel_mode='renewed',
    inheritance_mode='parent_copy',dose=8,software_only=True)
NEW_FILES={'experiments/digital_longitudinal01_'+n+'.py' for n in ('population','referee','child')}

def validate_request(request):
    assert type(request) is dict and boundary.canonical(request['configuration'])==boundary.canonical(CONFIG)
    assert type(request['seed']) is int and request['seed'] in (3,4)
    assert request['endpoint'] in ('raw','proof') and request['export'] in ('original','restored')
    assert request['role']==f"{request['export']}:{request['seed']}:{request['endpoint']}"
    expected={'configuration','seed','endpoint','export','role','source_files','source_sha256',
              'configuration_sha256','grant','grant_seal'}
    if request['endpoint']=='proof':expected.add('input')
    assert set(request)==expected
    assert request['configuration_sha256']==hashlib.sha256(boundary.canonical(CONFIG)).hexdigest()
    assert NEW_FILES<=set(request['source_files'])
    return request['endpoint']

def main():
    request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),1024**2));endpoint=validate_request(request)
    root=Path.cwd().resolve();pins=request['source_files']
    source=boundary.verify_source(root,pins);assert source==request['source_sha256']
    boundary.validate_grant(request,source,endpoint);boundary.module_origins(root,pins)
    constructors=step_calls=0
    if endpoint=='raw':
        from experiments import digital_pressure71_population as kernel
        from experiments import digital_longitudinal01_population as candidate
        init,step=kernel.World.__init__,kernel.World.step
        def counted_init(self,*args,**kwargs):
            nonlocal constructors
            constructors+=1;return init(self,*args,**kwargs)
        def counted_step(self):
            nonlocal step_calls
            step_calls+=1;return step(self)
        kernel.World.__init__,kernel.World.step=counted_init,counted_step
        try:value=candidate.history(request['seed'])
        finally:kernel.World.__init__,kernel.World.step=init,step
        assert constructors==2 and value['horizon']==8192 and value['software_only'] is True
    else:
        value=boundary.read_spec(request['input'],64*1024**2)
        assert value['seed']==request['seed'] and value['horizon']==8192 and value['software_only'] is True
        from experiments import digital_longitudinal01_referee as literal
        summary=literal.audit(value)
        value=dict(verified=True,summary=summary,natural_history_hash=value['hash'],
            source_sha256=source,configuration_sha256=request['configuration_sha256'],
            engineering_only=True,stage_credit=False)
        assert 'experiments.digital_pressure71_population' not in sys.modules
    boundary.module_origins(root,pins);assert boundary.verify_source(root,pins)==source
    from experiments import evidence_write_grant68 as transport
    manifest=transport.record(request['grant'],request['grant_seal'],source,
        request['configuration_sha256'],request['role'],value)
    manifest.update(world_constructors=constructors,step_calls=step_calls,
                    software_only=True,scientific_acceptance=False,stage_credit=False)
    print(boundary.canonical(manifest).decode('ascii'))

if __name__=='__main__':main()
