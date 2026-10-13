"""Trusted bounded scientific adapter; all laws and neutral sourcing are frozen.

The parent owns admission custody, grants, global budgets and verified parsing.
This adapter supplies no policy, teacher, candidate selection or stage credit.
"""
import hashlib,json,sys
from pathlib import Path


def admit(request,provenance,receipt=None):
    """Pure pre-construction checks. A prepared receipt is not paid evidence."""
    from experiments.digital_sharedlineage68_admission import SEEDS,require_durable_admission
    from experiments.digital_sharedlineage68_transition import validate_provenance
    validate_provenance(provenance)
    assert type(request['seed']) is int and request['seed'] in SEEDS
    kind=request['kind']
    assert kind in ('population','population_ref','fork','fork_ref')
    if kind.startswith('population'):
        assert (request['mode'],request['inheritance_mode']) in (
            ('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy'))
        treatment=request['mode']=='mutating'
    else:
        assert type(request['generation']) is int and request['generation'] in (1,2)
        assert request['fork_role'] in ('sham','ancestor_value_control')
        treatment=True
    if treatment:
        assert receipt is not None
        require_durable_admission(receipt,provenance['source_sha256'],provenance['configuration_sha256'])
    return treatment


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    request=json.loads(Path(sys.argv[1]).read_bytes())
    root=Path.cwd();pins=request['source_files']
    assert all(sha(root/name)==digest for name,digest in pins.items())
    source_sha=hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert source_sha==request['source_sha256']
    provenance=dict(source_sha256=source_sha,configuration_sha256=request['configuration_sha256'])
    def read(spec,cap):
        path=Path(spec['path']);assert sha(path)==spec['sha256']
        assert type(spec['extent']) is int and path.stat().st_size==spec['extent'] and 0<spec['extent']<=cap
        return json.loads(path.read_bytes())
    receipt=read(request['admission'],1024**2) if 'admission' in request else None
    treatment=admit(request,provenance,receipt)
    # No World import or construction precedes seed/role/durable admission.
    from experiments import evidence_write_grant68 as transport
    from experiments import digital_sharedlineage68_population as kernel
    calls=0;original=kernel.World.__init__
    def counted(self,*args,**kwargs):
        nonlocal calls
        calls+=1;return original(self,*args,**kwargs)
    kernel.World.__init__=counted
    kind=request['kind'];role=request['role']
    if kind=='population':
        value=kernel.history(request['seed'],mode=request['mode'],inheritance_mode=request['inheritance_mode'])
    elif kind=='fork':
        from experiments import digital_sharedlineage68_world as fork
        natural=read(request['input'],64*1024**2);assert natural['seed']==request['seed']
        assert natural['mode']=='mutating' and natural['inheritance_mode']=='parent_copy'
        value=fork.history(natural,request['generation'],request['fork_role'],provenance)
    elif kind=='population_ref':
        from experiments import digital_sharedlineage68_observe as observer
        row=read(request['input'],64*1024**2)
        assert (row['seed'],row['mode'],row['inheritance_mode'])==(request['seed'],request['mode'],request['inheritance_mode'])
        value=observer.audit_row(row,provenance)
    else:
        from experiments import digital_sharedlineage68_fork_interpret as referee
        row=read(request['input'],64*1024**2)
        assert (row['natural']['seed'],row['generation'],row['role'])==(request['seed'],request['generation'],request['fork_role'])
        value=referee.audit(row,provenance)
    manifest=transport.record(request['grant'],request['grant_seal'],source_sha,
        request['configuration_sha256'],role,value)
    assert all(sha(root/name)==digest for name,digest in pins.items())
    manifest.update(world_constructors=calls,kind=kind,software_only=False,treatment=treatment)
    print(json.dumps(manifest,sort_keys=True,separators=(',',':')))


if __name__=='__main__':main()
