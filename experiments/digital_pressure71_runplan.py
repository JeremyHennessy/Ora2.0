"""Registered71 fixed role order; no execution, sampler or admission authority."""
from experiments.digital_pressure71_admission import SEEDS,REFERENCE_DOSE
EXPORTS=('original','restored');DOSES=(1,8)

def roles():
    result=[dict(name=f'{s}-faithful-parent_copy-d{REFERENCE_DOSE}',kind='population',seed=s,
                 mode='faithful',inheritance_mode='parent_copy',dose=REFERENCE_DOSE) for s in SEEDS]
    for seed in SEEDS:
        for dose in DOSES:
            for inheritance in ('parent_copy','ancestor_copy'):
                result.append(dict(name=f'{seed}-mutating-{inheritance}-d{dose}',kind='population',seed=seed,
                    mode='mutating',inheritance_mode=inheritance,dose=dose))
    for seed in SEEDS:
        for dose in DOSES:
            for slot,control in [('parent','ancestor_value_control'),('child','inherited_source_control')]:
                for role in ('sham',control):
                    result.append(dict(name=f'{seed}-{slot}-{role}-d{dose}',kind='fork',seed=seed,
                        dose=dose,slot_kind=slot,fork_role=role,
                        natural_role=f'{seed}-mutating-parent_copy-d{dose}'))
    assert len(result)==104 and len({r['name'] for r in result})==104
    return result

def schedule():
    result=[dict(export=e,role='prepared',endpoint='prepared',treatment=False) for e in EXPORTS]
    for role in roles():
        treatment=role['kind']=='fork' or role.get('mode')=='mutating'
        for export in EXPORTS:
            for endpoint in ('raw','proof'):
                result.append(dict(export=export,role=role['name'],endpoint=endpoint,treatment=treatment))
    assert len(result)==418 and all(not r['treatment'] for r in result[:34])
    assert all(r['treatment'] for r in result[34:])
    return result
