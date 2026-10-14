"""Frozen70 role schedule; no execution, sampler or admission authority."""
from experiments.digital_functional70_admission import SEEDS
EXPORTS=('original','restored')


def roles():
    result=[dict(name=f'{s}-faithful-parent_copy',kind='population',seed=s,
                 mode='faithful',inheritance_mode='parent_copy') for s in SEEDS]
    for seed in SEEDS:
        for inheritance in ('parent_copy','ancestor_copy'):
            result.append(dict(name=f'{seed}-mutating-{inheritance}',kind='population',seed=seed,
                               mode='mutating',inheritance_mode=inheritance))
    for seed in SEEDS:
        for slot,control in [('parent','ancestor_value_control'),('child','inherited_source_control')]:
            for role in ('sham',control):
                result.append(dict(name=f'{seed}-{slot}-{role}',kind='fork',seed=seed,
                                   slot_kind=slot,fork_role=role))
    assert len(result)==56 and len({r['name'] for r in result})==56
    return result


def schedule():
    result=[dict(export=e,role='prepared',endpoint='prepared',treatment=False) for e in EXPORTS]
    for role in roles():
        treatment=role['kind']=='fork' or role.get('mode')=='mutating'
        for export in EXPORTS:
            for endpoint in ('raw','proof'):
                result.append(dict(export=export,role=role['name'],endpoint=endpoint,treatment=treatment))
    assert len(result)==226 and all(not r['treatment'] for r in result[:34])
    assert all(r['treatment'] for r in result[34:])
    return result
