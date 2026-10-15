"""Supplied predictor arbitration source only; no World or target admission.

The constant and the initial route are neutral source parameters. Runtime route
changes and model cells would be acquired state; the switching/updating rules
themselves are authored. This module supplies no environmental labels or run.
"""
import hashlib
import json

VERSION = 'DIGITAL-ARBITRATION85-SOURCE-v1'
CAPACITIES = (2, 4, 8)
ROUTES = ('constant', 'model')
ENTRIES = {'constant': 1, 'model': 6}
OPS = (0, 1, 4, 6, 7, 8, 19, 20, 21)
DESCRIPTORS = tuple((q, bit, route) for q in CAPACITIES
                    for bit in (0, 1) for route in ROUTES)


def admit(capacity, constant, initial_route):
    assert type(capacity) is int and capacity in CAPACITIES
    assert type(constant) is int and constant in (0, 1)
    assert type(initial_route) is str and initial_route in ROUTES


def programme(capacity, constant, initial_route):
    admit(capacity, constant, initial_route)
    return [
        [7, capacity, ENTRIES[initial_route]],
        [4, 0, constant], [6, 0, 0], [1, 0, 0], [8, 0, 6], [7, 0, 1],
        [0, 1, 0], [19, 0, 1], [6, 0, 0], [1, 0, 0], [8, 0, 12], [7, 0, 6],
        [19, 0, 1], [21, 0, 0], [20, 1, 0], [7, 0, 1],
    ]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def manifest():
    descriptors = []
    for capacity, constant, route in DESCRIPTORS:
        code = programme(capacity, constant, route)
        descriptors.append(dict(
            capacity=capacity, constant=constant, initial_route=route,
            programme=code, programme_sha256=digest(code),
            words=48, physical_state=capacity+8, formation=56+capacity,
            blank_models=[0]*capacity, initial_pc=0,
            initial_route_supplied=True, performance_selection=False,
            ancestor='Supplied LateHistory78/Revision84 generic updater; supplied win-stay/lose-switch routing',
        ))
    return dict(
        version=VERSION, descriptors=descriptors,
        ordinary_instruction_cost=1, ordinary_word_and_state_cost=1,
        instruction_costs=dict(constant=dict(success=5, error=4, absent=5),
                               model=dict(success=6, error=9, absent=6)),
        header_instructions=1,
        history_channels=['model cells', 'semantic route at decision-entry PC1/6'],
        acquired_labels_supplied=False, predictors_updater_and_arbiter_supplied=True,
        worlds=0, targets_queried=0, scientific_admission=False, stage_credit=False,
        scope='Source/dataflow/cost inventory only; not physics, viability, learning or selection',
    )
