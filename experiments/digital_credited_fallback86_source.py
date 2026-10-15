"""Disclosed generic source and data-only control interface; no World admission.

The predictor/updater/credit rule and neutral initial priors are supplied. Model
labels and semantic fallback state would be personally acquired at runtime.
These helpers do not install a control, supply a target or invoke a VM.
"""
import hashlib
import json

VERSION = 'DIGITAL-CREDITED-FALLBACK86-SOURCE-v1'
CAPACITIES = (2, 4, 8)
ENTRIES = {'fallback0': 1, 'model': 6, 'fallback1': 16}
CONTROLS = ('intact', 'model_erased', 'model_misbound',
            'fallback_misbound', 'history_disabled')
BOUNDARIES = ((4, 6), (5, 1), (11, 6), (15, 1), (15, 16), (19, 6), (20, 16))
OPS = (0, 1, 4, 6, 7, 8, 19, 20, 21)
DESCRIPTORS = tuple((q, route) for q in CAPACITIES for route in ENTRIES)


def programme(capacity, initial_route):
    assert type(capacity) is int and capacity in CAPACITIES
    assert type(initial_route) is str and initial_route in ENTRIES
    return [
        [7, capacity, ENTRIES[initial_route]],
        [4, 0, 0], [6, 0, 0], [1, 0, 0], [8, 0, 6], [7, 0, 1],
        [0, 1, 0], [19, 0, 1], [6, 0, 0], [1, 0, 0], [8, 0, 12], [7, 0, 6],
        [19, 0, 1], [21, 0, 0], [20, 1, 0], [8, 0, 1],
        [4, 0, 1], [6, 0, 0], [1, 0, 0], [8, 0, 6], [7, 0, 16],
    ]


def _control(control, active):
    assert type(control) is str and control in CONTROLS
    assert type(active) is bool


def entry_after_completed_decision(previous_pc, next_pc, initial_route, control, active):
    """Pure proposed boundary substitution, after ordinary branch CPU/counting."""
    _control(control, active)
    assert type(previous_pc) is int and type(next_pc) is int
    assert (previous_pc, next_pc) in BOUNDARIES
    assert type(initial_route) is str and initial_route in ENTRIES
    if active and control == 'history_disabled':
        return ENTRIES[initial_route]
    if active and control == 'fallback_misbound' and next_pc != 6:
        return 17-next_pc
    return next_pc


def model_read(pc, memory, index, control, active):
    """Pure READ value only; physical cells/STORE/current feedback stay intact."""
    _control(control, active)
    assert type(pc) is int and pc in (7, 12)
    assert type(memory) is list and len(memory) in CAPACITIES
    assert all(type(v) is int and 0 <= v < 16 for v in memory)
    assert type(index) is int and 0 <= index < 16
    q = len(memory)
    if active and control in ('model_erased', 'history_disabled'):
        return 0
    offset = q//2 if active and control == 'model_misbound' else 0
    return memory[(index+offset) % q]


def manifest():
    descriptions = []
    for q, route in DESCRIPTORS:
        code = programme(q, route)
        descriptions.append(dict(capacity=q, initial_route=route, programme=code,
            programme_sha256=hashlib.sha256(json.dumps(code, separators=(',', ':')).encode()).hexdigest(),
            words=63, physical_state=q+8, formation=71+q, blank_models=[0]*q,
            initial_pc=0, performance_selection=False,
            ancestor='Supplied generic cue updater; distinct authored experience-credit routing after closed85'))
    return dict(version=VERSION, descriptors=descriptions, header_cpu=1,
        instruction_costs=dict(fallback=dict(success=5, error=4, absent=5),
                               model=dict(success=6, error=9, absent=6)),
        ordinary_instruction_cost=1, ordinary_word_and_state_cost=1,
        controls=list(CONTROLS), controls_installed=False,
        completed_branch_pairs=[list(p) for p in BOUNDARIES], model_read_pcs=[7, 12],
        history_channels=['model cells', 'typed semantic entry/fallback bit at PC1/6/16'],
        acquired_labels_supplied=False, machinery_and_initial_priors_supplied=True,
        worlds=0, targets_queried=0, scientific_admission=False, stage_credit=False,
        scope='Source/control interface only; not VM physics, viability, useful learning or selection')
