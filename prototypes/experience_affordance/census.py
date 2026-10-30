"""Isolated exhaustive controller affordance probe; never imports Ora's World.

No population, stochastic search, birth or historical sample is executed.
The supplied Mealy controller class and altered task are NOT Ora's native VM.
"""
from collections import deque
from fractions import Fraction
from itertools import product
from pathlib import Path
import argparse
import hashlib
import json
import time

ARMS = ('true', 'sham', 'feedback_erased', 'state_erased', 'feedback_complement')
FIELDS = ('correct', 'probes', 'attempts', 'earned_successes', 'transitions', 'senses', 'writes',
          'external_resets', 'external_feedback_changes')
PROTOCOL = {
    'schema': 'ORA-EXPLORATORY-EXPERIENCE-AFFORDANCE-v1',
    'status': 'ISOLATED_CONTROLLER_CENSUS_NOT_SCIENTIFIC_POPULATION',
    'controller': '12 bits: six (state,input) cells, low bit output, high bit nextstate',
    'inputs': '0/1 success from own attempt; 2 blank. Observation type is a supplied cue.',
    'initial_state': 0,
    'development': {'all_binary_target_sequences_length': 3, 'delays': [0, 1]},
    'validation': {'all_binary_target_sequences_length': 4, 'delays': [2, 3]},
    'block': 'target fixed for blank attempt, own feedback, delay blank transitions, two probes; changes only next block',
    'ordering': 'output from old state and input, then new state; reset intervention before EACH probe',
    'state': 'persists across blocks; resets between sequences, never inherited acquired state',
    'arms': list(ARMS),
    'control': 'fixed0/fixed1; all one-state input maps; latest-success latch; strong win-stay/lose-shift',
    'prices': {'formation_per_code_bit': 1, 'formation_per_state_bit': 1,
               'transition': 1, 'sense_feedback': 1, 'write_changed_state': 1,
               'reward_grid': list(range(1, 17)), 'storage_bit_per_transition_grid': list(range(5))},
    'note': 'Explicit toy prices, not historical Ora prices or a host-energy exchange rate',
    'copy_quote': '12 code bits + 1 blank state bit = 13, affordability proxy only; no actual birth',
    'founder': 0,
    'primary_path': 'all Hamming1 edges; nondecreasing development net at reward8/storage0',
    'selection': 'minimum development break-even vs fixed/memoryless/latest-success; lowest genotype tie. Strong win-stay/lose-shift compared separately, never omitted from claims.',
    'ceiling': '300 seconds, all4096 tables, 24576 undirected edges; no retry or retuning',
    'claim_limit': 'Controller-class affordance and mutation topology; accounting is not survival, paid birth or evolved fitness',
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def transition(genome, state, signal):
    assert type(genome) is int and 0 <= genome < 4096
    assert state in (0, 1) and signal in (0, 1, 2)
    cell = (genome >> (2 * (3 * state + signal))) & 3
    return cell & 1, cell >> 1


def episodes(length, delays):
    return [(targets, delay) for targets in product((0, 1), repeat=length) for delay in delays]


def evaluate(genome, cases, arm='true', kind='fsm'):
    assert arm in ARMS
    totals = dict.fromkeys(FIELDS, 0)
    stream = hashlib.sha256()
    for targets, delay in cases:
        state = 0
        for target in targets:
            def step(signal, probe=False):
                nonlocal state
                if probe and arm == 'state_erased':
                    totals['external_resets'] += 1
                    state = 0  # external intervention; no natural fee credited or debited
                before = state
                if kind == 'fsm':
                    action, state = transition(genome, state, signal)
                elif kind == 'memoryless':
                    action = (genome >> signal) & 1
                elif kind == 'latest_success':
                    action = state
                    if signal != 2:
                        state = signal  # supplied reference, not discovered machinery
                elif kind == 'win_stay_lose_shift':
                    action = state
                    if signal != 2:
                        state ^= 1 - signal
                else:
                    action = genome
                totals['transitions'] += 1
                totals['senses'] += int(signal != 2)
                totals['writes'] += int(before != state)
                stream.update(bytes((signal, action, state, int(probe))))
                return action
            attempt = step(2)
            totals['attempts'] += 1
            feedback = int(attempt == target)  # each arm's own action, never another arm's feedback
            totals['earned_successes'] += feedback
            original_feedback = feedback
            if arm == 'feedback_erased':
                feedback = 0
            elif arm == 'feedback_complement':
                feedback ^= 1
            totals['external_feedback_changes'] += int(feedback != original_feedback)
            step(feedback)
            for _ in range(delay):
                step(2)
            for _ in range(2):
                action = step(2, probe=True)
                totals['correct'] += int(action == target)
                totals['probes'] += 1
    return dict(totals, trace_sha256=stream.hexdigest())


def cost(row, code_bits=12, state_bits=1, storage=0):
    # Formation is paid once per separate sequence, not once per aggregate.
    return row['sequences'] * (code_bits + state_bits) + row['transitions'] + row['senses'] + row['writes'] + storage * state_bits * row['transitions']


def attach_sequences(row, cases):
    return dict(row, sequences=len(cases))


def references(cases):
    result = []
    # The efficient fixed controllers skip nondecision work/sensing altogether.
    for bit in (0, 1):
        row = attach_sequences(evaluate(bit, cases, kind='fixed'), cases)
        row.update(transitions=row['probes'], senses=0, writes=0)
        result.append(dict(name='fixed'+str(bit), code_bits=1, state_bits=0, row=row))
    # All eight memoryless maps are retained, rather than a chosen reactive loser.
    for code in range(8):
        row = attach_sequences(evaluate(code, cases, kind='memoryless'), cases)
        result.append(dict(name='memoryless'+str(code), code_bits=3, state_bits=0, row=row))
    row = attach_sequences(evaluate(0, cases, kind='latest_success'), cases)
    result.append(dict(name='latest_success', code_bits=6, state_bits=1, row=row))
    # Strong supplied reference: same 12-bit table-class representation and fees.
    row = attach_sequences(evaluate(0, cases, kind='win_stay_lose_shift'), cases)
    result.append(dict(name='win_stay_lose_shift', code_bits=12, state_bits=1, row=row))
    return result


def break_even(row, refs, storage=0):
    """Reward must exceed this rational bound to beat every reference; None if impossible."""
    bounds = [Fraction(0)]
    for ref in refs:
        delta = row['correct'] - ref['row']['correct']
        extra = cost(row, storage=storage) - cost(ref['row'], ref['code_bits'], ref['state_bits'], storage)
        if delta <= 0:
            if extra >= 0:
                return None
            # Not expected here (balanced schedules); refuse hidden upper-bound assumptions.
            raise ValueError('Need two-sided reward interval, not a lower-bound-only frontier')
        bounds.append(Fraction(extra, delta))
    return max(bounds)


def reward_interval(row, refs, storage=0):
    """General exact strict net-superiority interval, including cheaper partial accuracy."""
    lower, upper = Fraction(0), None
    for ref in refs:
        delta = row['correct'] - ref['row']['correct']
        extra = cost(row, storage=storage) - cost(ref['row'], ref['code_bits'], ref['state_bits'], storage)
        if delta == 0:
            if extra >= 0:
                return {'possible': False}
        elif delta > 0:
            lower = max(lower, Fraction(extra, delta))
        else:
            bound = Fraction(extra, delta)
            upper = bound if upper is None else min(upper, bound)
    if upper is not None and upper <= lower:
        return {'possible': False}
    return {'possible': True, 'reward_strictly_above': str(lower),
            'reward_strictly_below': None if upper is None else str(upper)}


def census(selection_path):
    start = time.monotonic()
    dev = episodes(3, (0, 1))
    valid = episodes(4, (2, 3))
    refs = {'development': references(dev)}
    records = []
    for genome in range(4096):
        if time.monotonic() - start > 300:
            raise TimeoutError('Frozen census wall limit; incomplete, no retry')
        row = {'genome': genome}
        row['development'] = {arm: attach_sequences(evaluate(genome, dev, arm), dev) for arm in ARMS}
        assert row['development']['true'] == row['development']['sham']
        records.append(row)
    # Fix selection on development alone. Validation is evaluated for all genotypes,
    # but neither its score nor interventions enter this selection or path.
    opportunity_refs = [r for r in refs['development'] if r['name'] != 'win_stay_lose_shift']
    thresholds = [break_even(r['development']['true'], opportunity_refs) for r in records]
    eligible = [i for i, q in enumerate(thresholds) if q is not None]
    selected = min(eligible, key=lambda i: (thresholds[i], i)) if eligible else None
    scores = [8 * r['development']['true']['correct'] - cost(r['development']['true']) for r in records]
    parents = {0: None}
    queue = deque([0])
    while queue:
        g = queue.popleft()
        for bit in range(12):
            child = g ^ (1 << bit)
            if child not in parents and scores[child] >= scores[g]:
                parents[child] = g
                queue.append(child)
    targets = [g for g in eligible if g in parents and thresholds[g] < 8]
    endpoint = min(targets, key=lambda g: (thresholds[g], g)) if targets else None
    path = []
    if endpoint is not None:
        g = endpoint
        while g is not None:
            path.append({'genome': g, 'development_net_reward8_storage0': scores[g]})
            g = parents[g]
        path.reverse()
    selection = dict(protocol_sha256=digest(PROTOCOL), selected=selected, path=path,
                     development_records_sha256=digest(records),
                     validation_accessed=False, note='Frozen before any validation controller evaluation')
    with selection_path.open('x', encoding='utf8') as frozen:
        json.dump(selection, frozen, indent=2)
    selection_sha256 = hashlib.sha256(selection_path.read_bytes()).hexdigest()
    refs['validation'] = references(valid)
    for genome, row in enumerate(records):
        if time.monotonic() - start > 300:
            raise TimeoutError('Frozen validation wall limit; incomplete, no retry')
        row['validation'] = {arm: attach_sequences(evaluate(genome, valid, arm), valid) for arm in ARMS}
        assert row['validation']['true'] == row['validation']['sham']
    grid = []
    for storage in range(5):
        for reward in range(1, 17):
            best_ref = max(reward * r['row']['correct'] - cost(r['row'], r['code_bits'], r['state_bits'], storage) for r in opportunity_refs)
            strong = refs['development'][-1]
            strong_net = reward * strong['row']['correct'] - cost(strong['row'], strong['code_bits'], strong['state_bits'], storage)
            count = sum(reward * r['development']['true']['correct'] - cost(r['development']['true'], storage=storage) > best_ref for r in records)
            above_strong = sum(reward * r['development']['true']['correct'] - cost(r['development']['true'], storage=storage) > strong_net for r in records)
            grid.append(dict(storage=storage, reward=reward, development_tables_beating_opportunity_references=count,
                             development_tables_beating_strong_reactive=above_strong))
    selected_summary = None
    if selected is not None:
        selected_summary = {'genome': selected, 'development_threshold_strictly_above': str(thresholds[selected]),
            'validation_threshold_strictly_above': str(break_even(records[selected]['validation']['true'], refs['validation'][:-1])),
            'validation_reward_interval_vs_all_including_strong': reward_interval(records[selected]['validation']['true'], refs['validation']),
            'measurements': records[selected], 'code': [[transition(selected, s, i) for i in range(3)] for s in range(2)]}
    return dict(protocol=PROTOCOL, protocol_sha256=digest(PROTOCOL), controller_count=4096,
        undirected_single_bit_edges=24576, independent_populations=0, actual_births=0,
        actual_deaths=0, extinct_lineages=0, lineage_measurement='NOT_APPLICABLE_NO_POPULATION',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        controls=refs, all_controller_records=records, selected_on_development_only=selected_summary,
        development_beneficial_tables=len(eligible), development_nondecreasing_reachable=len(parents),
        reachable_net_advantage_tables_at_reward8_storage0=len(targets), path=path,
        reward_storage_grid=grid, elapsed_wall_seconds=time.monotonic()-start,
        development_selection_file_sha256=selection_sha256,
        native_ora_vm_executions=0, historical_bank_reads=0,
        claims={'evolved_learning': False, 'paid_reproduction': False, 'open_ended_evolution': False})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Exclusive creation prevents replacing even partial or failed receipts.
    with args.output.open('x', encoding='utf8') as output:
        try:
            result = census(args.output.with_suffix('.selection.json'))
            json.dump(result, output, indent=2)
        except BaseException as exc:
            json.dump({'status': 'INCOMPLETE', 'exception': repr(exc), 'protocol_sha256': digest(PROTOCOL)}, output)
            raise


if __name__ == '__main__':
    main()
