"""Complete references then durable admission then unscreened sources; no World."""
from experiments.digital_genotype66 import SEEDS,SOURCE_SEEDS,ordinary_admission,cohort


def panel(run_role,save_admission):
    references={where:[] for where in ('original','restored')}
    for where in references:
        for seed in SEEDS:references[where].append(run_role(where,seed,None))
    gates={where:ordinary_admission(proofs) for where,proofs in references.items()}
    assert references['original']==references['restored']
    receipt=dict(admitted=all(gates.values()),gates=gates,parent_worlds=8,parent_engineering_replays=8,
                 source_world_calls=0,stage_credit=False)
    save_admission(receipt)
    proofs=references['original'][:]
    if receipt['admitted']:
        for source in SOURCE_SEEDS:
            for seed in SEEDS:
                a=run_role('original',seed,source);b=run_role('restored',seed,source)
                assert a==b;proofs.append(a)
    return dict(admission=receipt,proofs=proofs,comparison=cohort(proofs) if receipt['admitted'] else None,
                original_roles=len(proofs),engineering_replays=len(proofs),stage_credit=False)
