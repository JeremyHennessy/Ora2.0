"""Finite70 adapter retaining reviewed69 measurement envelopes, not an execution admission or complete qualified runner.

The parent authenticates admission custody, grants, limits and reference order.
Referee roles import no World. No policy, teacher or successful genome is supplied.
"""
import hashlib,json,sys
from pathlib import Path


def admit(request,provenance,receipt=None):
    """Pure guard before producer import; a prepared receipt is not paid truth."""
    from experiments.digital_functional70_admission import SEEDS,require_durable_admission
    from experiments.digital_functional69_transition import validate_provenance
    validate_provenance(provenance)
    assert type(request['seed']) is int and request['seed'] in SEEDS
    kind=request['kind'];assert kind in ('population','population_ref','fork','fork_ref')
    if kind.startswith('population'):
        assert (request['mode'],request['inheritance_mode']) in (
            ('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy'))
        treatment=request['mode']=='mutating'
    else:
        assert request['slot_kind'] in ('parent','child')
        assert request['fork_role'] in (('sham','ancestor_value_control') if request['slot_kind']=='parent'
                                      else ('sham','inherited_source_control'))
        treatment=True
    if treatment:
        assert receipt is not None
        require_durable_admission(receipt,provenance['source_sha256'],provenance['configuration_sha256'])
    return treatment


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source(root,pins):
    required={'experiments/'+name+'.py' for name in (
        '__init__','digital_functional70_scientific_child','digital_functional70_admission',
        'digital_functional69_referee','digital_functional69_world','digital_functional69_transition',
        'digital_functional69_family','digital_functional69_contract','digital_sharedlineage68_population',
        'digital_sharedlineage68_interpret','digital_mobile54','digital_informative_exposure23_interpret',
        'evidence_write_grant68','digital_functional69_measure')}
    assert type(pins) is dict and required<=set(pins)
    assert all(sha(root/name)==digest for name,digest in pins.items())
    return hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def module_origins(root):
    for name,module in list(sys.modules.items()):
        if name.startswith('experiments.'):
            assert Path(module.__file__).resolve()==root/('experiments/'+name.split('.')[-1]+'.py')


def main():
    request=json.loads(Path(sys.argv[1]).read_bytes());root=Path.cwd();pins=request['source_files']
    assert Path(__file__).resolve()==root/'experiments/digital_functional70_scientific_child.py'
    source_sha=verify_source(root,pins)
    assert source_sha==request['source_sha256']
    provenance=dict(source_sha256=source_sha,configuration_sha256=request['configuration_sha256'])
    def read(spec,cap):
        path=Path(spec['path']);assert sha(path)==spec['sha256']
        assert type(spec['extent']) is int and path.stat().st_size==spec['extent'] and 0<spec['extent']<=cap
        return json.loads(path.read_bytes())
    receipt=read(request['admission'],1024**2) if 'admission' in request else None
    treatment=admit(request,provenance,receipt)
    # No producer import/construction precedes scientific membership/admission.
    from experiments import evidence_write_grant68 as transport
    kind=request['kind'];role=request['role'];calls=0
    if kind in ('population','fork'):
        from experiments import digital_sharedlineage68_population as kernel
        original=kernel.World.__init__
        def counted(self,*args,**kwargs):
            nonlocal calls
            calls+=1;return original(self,*args,**kwargs)
        kernel.World.__init__=counted
        if kind=='population':
            module_origins(root)
            value=kernel.history(request['seed'],mode=request['mode'],inheritance_mode=request['inheritance_mode'])
        else:
            from experiments import digital_functional69_world as fork
            module_origins(root)
            natural=read(request['input'],64*1024**2);assert natural['seed']==request['seed']
            assert natural['mode']=='mutating' and natural['inheritance_mode']=='parent_copy'
            value=fork.history(natural,request['slot_kind'],request['fork_role'],provenance)
    else:
        from experiments import digital_functional69_referee as referee
        module_origins(root)
        row=read(request['input'],64*1024**2)
        if kind=='population_ref':
            assert (row['seed'],row['mode'],row['inheritance_mode'])==(request['seed'],request['mode'],request['inheritance_mode'])
            value=dict(verified=True,summary=referee.audit_history(row),natural_history_hash=row['hash'],provenance=provenance,stage_credit=False)
        else:
            assert (row['natural']['seed'],row['slot_kind'],row['role'])==(request['seed'],request['slot_kind'],request['fork_role'])
            value=referee.audit(row,provenance)
    module_origins(root)
    manifest=transport.record(request['grant'],request['grant_seal'],source_sha,
                              request['configuration_sha256'],role,value)
    assert all(sha(root/name)==digest for name,digest in pins.items())
    manifest.update(world_constructors=calls,kind=kind,software_only=False,treatment=treatment)
    print(json.dumps(manifest,sort_keys=True,separators=(',',':')))


if __name__=='__main__':main()
