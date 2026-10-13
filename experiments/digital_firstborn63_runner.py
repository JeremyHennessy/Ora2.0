"""Ordinary-first finite ordering; callback is the pinned native pair runner.

No World construction here. Both complete reference sets finish before any
enrolled-source callback. Refusals preserve complete ordinary denominators.
"""
from experiments.digital_firstborn63_integration import SEEDS, ROSTER, ordinary_admission, cohort

LOCATIONS = ('original', 'restored')


def panel(run_pair, save_admission):
    ordinary = {location: [] for location in LOCATIONS}
    for location in LOCATIONS:
        for seed in SEEDS:
            ordinary[location].append(run_pair(location, seed, None))
    # Evaluate both full sets, even if the first set fails its lifecycle gate.
    gates = {location: ordinary_admission(ordinary[location]) for location in LOCATIONS}
    assert ordinary['original'] == ordinary['restored']
    admitted = all(gates.values())
    receipt = dict(admitted=admitted, gates=gates, ordinary_histories=32,
                   ordinary_engineering_replays=32, retained_calls_so_far=0)
    save_admission(receipt)  # Durable receipt BEFORE any source callback.
    pairs = [result['pair'] for result in ordinary['original']]
    if admitted:
        for source in ROSTER:
            for seed in SEEDS:
                original = run_pair('original', seed, source)
                restored = run_pair('restored', seed, source)
                assert original == restored
                pairs.append(original['pair'])
    return dict(admission=receipt, comparison=cohort(pairs) if admitted else None,
                pairs=pairs, unique_histories=len(pairs)*2,
                engineering_replays=len(pairs)*2, learning=False,
                evolution=False, selection=False, stage_credit=False)
