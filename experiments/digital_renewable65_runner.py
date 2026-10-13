"""Finite ordinary-first sequencing; no World construction in this module."""
from experiments.digital_renewable65 import SEEDS,ordinary_admission,cohort

LOCATIONS=('original','restored')


def panel(run_role,save_admission):
    references={location:[] for location in LOCATIONS}
    for location in LOCATIONS:
        for seed in SEEDS:references[location].append(run_role(location,seed,'faithful'))
    gates={location:ordinary_admission([p['summary'] for p in proofs]) for location,proofs in references.items()}
    assert references['original']==references['restored']
    receipt=dict(admitted=all(gates.values()),gates=gates,ordinary_roles=16,
                 ordinary_engineering_replays=16,mutating_world_calls=0,stage_credit=False)
    save_admission(receipt)  # Required durable zero-treatment receipt before treatment.
    proofs=list(references['original'])
    if receipt['admitted']:
        for seed in SEEDS:
            original=run_role('original',seed,'mutating')
            restored=run_role('restored',seed,'mutating')
            assert original==restored;proofs.append(original)
    return dict(admission=receipt,proofs=proofs,comparison=cohort(proofs) if receipt['admitted'] else None,
                original_roles=len(proofs),engineering_replays=len(proofs),
                selection=False,evolution=False,learning=False,stage_credit=False)
