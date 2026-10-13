"""Disclosed Firstborn63 genesis adapter; no law, policy or evaluator changes.

Scientific execution requires the separately pinned finite controller. This
adapter supplies an existing enrolled genome, never selects from outcomes.
"""
from experiments.digital_firstborn63_integration import SEEDS, MODES, VERSION
from experiments.digital_transfer57 import choice, SOURCE_HASH
from experiments.digital_informative_exposure23_interpret import clone, h

ROUTE = 'firstborn63'


def generate(seed, mode, arm, source, manifest):
    assert type(seed) is int and seed in SEEDS
    assert type(mode) is str and mode in MODES
    program, origin = choice(arm, source, manifest)
    from experiments import digital_informative_exposure23 as substrate
    assert ROUTE not in substrate.PROGRAMS
    before = h(substrate.PROGRAMS)
    matches = [name for name, value in substrate.PROGRAMS.items() if value == program]
    assert len(matches) <= 1
    route = matches[0] if matches else ROUTE
    if not matches:
        substrate.PROGRAMS[ROUTE] = clone(program)
    try:
        row = substrate.history(seed, route, mode)
        assert row['seed'] == seed and row['mode'] == mode
        assert row['route'] == route and row['genesis_program'] == program
        return dict(version=VERSION, arm=arm, source=origin,
                    source_manifest_hash=SOURCE_HASH, history=row)
    finally:
        if not matches:
            del substrate.PROGRAMS[ROUTE]
        assert h(substrate.PROGRAMS) == before
