"""Finite dependency order/precharge arithmetic; no World, target or execution."""
M=1024**2

def plan(configuration):
    result=[f'{export}:{seed}:{kind}' for seed in configuration['seeds']
        for export,kind in (('original','generate'),('original','audit'),
                            ('restored','generate'),('original','metrics'))]
    return result+['original:interpret']

def capacity(role):
    return (64 if role.endswith(':generate') else 8)*M

def required_raw(configuration):
    # Every positive output and all four expected refusal request/native slots,
    # plus source/config/owners/archive staging ceiling before any producer.
    return sum(capacity(r)+M+64*1024 for r in plan(configuration))+4*(M+64*1024)+64*M

def input_for(role,originals,proofs,metrics):
    if role=='original:interpret':return list(metrics)
    export,seed,kind=role.split(':');seed=int(seed)
    if kind=='audit':return originals[seed]
    if kind=='metrics':return dict(recording=originals[seed],proof=proofs[seed])
    return None

def pipeline(configuration,launch):
    originals={};proofs={};metrics=[];final=None
    for role in plan(configuration):
        inputs=input_for(role,originals,proofs,metrics)
        output=launch(role,inputs)
        assert type(output) is dict and set(output)=={'path','extent','sha256'}
        if role=='original:interpret':final=output;continue
        export,seed,kind=role.split(':');seed=int(seed)
        if kind=='generate':
            if export=='original':originals[seed]=output
            else:assert all(output[k]==originals[seed][k] for k in ('extent','sha256')), 'Producer replay mismatch'
        elif kind=='audit':proofs[seed]=output
        else:metrics.append(output)
    assert list(originals)==list(proofs)==configuration['seeds']
    assert len(metrics)==len(configuration['seeds']) and final is not None
    return dict(originals=originals,proofs=proofs,metrics=metrics,final=final)
