"""Bounded literal CFG analysis and declared-path scalar worksheet, never a VM.

No experiment imports, register machine, entities, resource ecology, seed draws,
model calls or population execution. Run once against the frozen plan; failures
are printed as JSON with traceback. No runtime or laboratory store is opened.
"""
import argparse
import ast
import ctypes
import hashlib
import json
import time
import traceback
from collections import deque
from fractions import Fraction
from pathlib import Path

PLAN_HASH = 'bfcd07ca5b7e8ad3bbe0864e68fcf11addd72c533ea249d66385eb548226cf8d'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def cfg_certificate(program):
    """Both conditional successors; finite transitive closure, no execution."""
    n = len(program)
    edges = []
    for pc, (op, _, b) in enumerate(program):
        edges.append({b % n} if op == 7 else
                     {(pc + 1) % n, b % n} if op == 8 else
                     set() if op == 17 else {(pc + 1) % n})
    reach = [set(row) for row in edges]
    for k in range(n):
        for i in range(n):
            if k in reach[i]:
                reach[i].update(reach[k])
    components = []
    for i in range(n):
        if i not in ({0} | reach[0]) or i not in reach[i]:
            continue
        component = tuple(j for j in range(n) if j in reach[i] and i in reach[j])
        if component not in components:
            components.append(component)
    return [list(c) for c in components if {6, 10, 12} <= {program[i][0] for i in c}]


def worksheet(name, program, path, initially_matching):
    """Sum frozen path costs; no instruction/register/World interpretation."""
    slots = len(program)
    body = 3 * slots + 16
    if name.startswith('fixed') and not initially_matching:
        return dict(name=name, initially_matching=False, paid_birth=False,
                    status='IMPOSSIBLE_WITHOUT_INTAKE_OR_TRANSFER',
                    minimum_copy_division_parent_cost=slots * 4 + 31,
                    initial_energy=12, mature_material=body,
                    reason='Fixed wrong port has no intake under the conditional stable-target premise.')
    startup = len(path['startup'])
    energy = 12 - startup
    turns = startup
    heat = startup
    overflow = 0
    captures = 0
    rows = []
    if not initially_matching and name in ('candidate', 'authored_same_policy_8'):
        count = len(path['failure_cycle'])
        energy -= count
        turns += count
        heat += count
        assert energy > 0
        rows.append(dict(kind='initial_failed_port_branch', dispatches=count, end_energy=energy))
    cycle = path.get('success_cycle', path.get('cycle'))
    assert program[cycle[0]][0] == 6
    copy_at = next(i for i, pc in enumerate(cycle) if program[pc][0] == 10)
    divide_at = next(i for i, pc in enumerate(cycle) if program[pc][0] == 12)
    assert copy_at < divide_at == len(cycle) - 2 and program[cycle[-1]][0] == 7
    max_cycles = slots + (2 if name == 'blind_alternator' else 0)
    for group in range(max_cycles):
        success = (group % 2 == (0 if initially_matching else 1)) if name == 'blind_alternator' else True
        start_energy = energy
        after_food = energy - 1
        if success:
            loss = max(0, after_food + 20 - 64)
            overflow += loss
            heat += loss
            after_food = min(64, after_food + 20)
            captures += 1
        copying = group < slots
        extra = 3 if copying else 0
        # Scalar prefix inequalities for the declared contiguous action block.
        after_copy_base = after_food - copy_at
        assert not copying or after_copy_base >= 3
        at_divide = after_food - divide_at - extra
        assert after_food > 0 and after_copy_base - extra > 0 and at_divide > 0
        complete = group + 1 >= slots
        birth = complete and at_divide >= 30
        dispatches = len(cycle) - (1 if birth else 0)
        end_energy = after_food - (dispatches - 1) - extra - (30 if birth else 0)
        assert end_energy > 0
        turns += dispatches
        heat += dispatches + extra + (18 if birth else 0)
        energy = end_energy
        rows.append(dict(group=group + 1, food_success=success, start_energy=start_energy,
                         dispatches=dispatches, copy_extra=extra, full_nursery_copy_refused=not copying,
                         division_refused=not birth, division_guard_energy=at_divide,
                         end_energy=energy))
        if birth:
            assert turns < 256 and captures * 20 + 12 == energy + 12 + heat
            assert 512 - body >= slots * 3 + 16
            return dict(name=name, initially_matching=initially_matching, paid_birth=True,
                        status='CONDITIONAL_ARITHMETIC_PASS', first_birth_own_turn=turns,
                        parent_energy=energy, child_energy=12, captures=captures,
                        heat=heat, cap_heat=overflow, mature_material=body,
                        hypothetical_supplied_assembly_heat=body,
                        cost_scope='Parent lifetime to first child; hypothetical initial assembly listed separately, no evolved-origin formation claim.',
                        paid_copy_words=slots * 3, groups=rows,
                        simultaneous_parent_nursery_child_state_material=body + slots * 3 + 16)
    return dict(name=name, initially_matching=initially_matching, paid_birth=False,
                status='NO_BIRTH_WITHIN_FROZEN_WORKSHEET', end_energy=energy, groups=rows)


def peak_working_set():
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('faults', ctypes.c_ulong)] + [
            (n, ctypes.c_size_t) for n in ('peak', 'working', 'quota_peak_paged', 'quota_paged',
                                         'quota_peak_nonpaged', 'quota_nonpaged', 'pagefile', 'peak_pagefile')]
    process = ctypes.windll.kernel32.GetCurrentProcess
    process.restype = ctypes.c_void_p
    query = ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    assert query(process(), ctypes.byref(counters), counters.cb)
    return counters.peak


def analyze(root):
    started = time.monotonic()
    raw = (root / 'data/eka0-certificate-plan-20261023.json').read_bytes()
    assert digest(raw) == PLAN_HASH
    plan = json.loads(raw)
    for name, expected in plan['source_sha256'].items():
        assert digest((root / name).read_bytes()) == expected
    flat = lambda p: [word for triple in p for word in triple]
    founder, candidate = plan['founder'], plan['candidate']
    mobile = ast.parse((root / 'experiments/digital_mobile54.py').read_text(encoding='utf-8'))
    literal = next(node.value for node in mobile.body if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'PROGRAM' for t in node.targets))
    assert ast.literal_eval(literal) == founder
    all_programs = dict(candidate=candidate, **plan['references'])
    for program in [founder] + list(all_programs.values()):
        assert 1 <= len(program) <= 32
        assert all(len(t) == 3 and all(type(w) is int and 0 <= w < 32 for w in t) for t in program)
    old, new = flat(founder), flat(candidate)
    assert len(old) == len(new) == 27
    edits = [dict(index=i, before=a, after=b) for i, (a, b) in enumerate(zip(old, new)) if a != b]
    assert len(edits) == 10
    truth = []
    for port in (0, 1):
        for target in (0, 1):
            feedback = int(port == target)
            next_port = port if feedback else port ^ 1
            assert next_port == target
            truth.append(dict(port=port, target=target, truthful_nonempty_feedback=feedback, next_port=next_port))
    nodes = []
    for mask in range(1024):
        assert time.monotonic() - started < 60
        words = old[:]
        for bit, edit in enumerate(edits):
            if mask & (1 << bit):
                words[edit['index']] = edit['after']
        components = cfg_certificate([words[i:i+3] for i in range(0, 27, 3)])
        nodes.append(dict(mask=mask, necessary_structural_condition=bool(components), components=components))
    parents = {0: None} if nodes[0]['necessary_structural_condition'] else {}
    queue = deque(parents)
    while queue:
        node = queue.popleft()
        for bit in range(10):
            child = node | (1 << bit)
            if child not in parents and nodes[child]['necessary_structural_condition']:
                parents[child] = node
                queue.append(child)
    route = []
    if 1023 in parents:
        cursor = 1023
        while cursor is not None:
            route.append(cursor)
            cursor = parents[cursor]
        route.reverse()
    costs = [worksheet(name, program, plan['declared_paths'][name], match)
             for name, program in all_programs.items() for match in (True, False)]
    assert len(costs) == 10
    arithmetic = []
    H = 2 ** 64
    for dose in (1, 8):
        cycles, rem = divmod(H, 3100)
        counts = [cycles * dose + max(0, min(dose, rem - 100 * k)) for k in range(31)]
        p_mut = Fraction(sum(counts), H)
        # Actual specified nonzero offsets for each fixed word, no seed hashes.
        p_route = (1 - p_mut) ** 17
        for edit in edits:
            delta = (edit['after'] - edit['before']) % 32
            assert 1 <= delta <= 31
            p_route *= Fraction(counts[delta - 1], H)
        arithmetic.append(dict(dose=dose, p_exact_ten_specified_edits_and_no_others=float(p_route),
                               exact_fraction=str(p_route), uniform_independent_hash_assumption_only=True))
    peak = peak_working_set()
    elapsed = time.monotonic() - started
    assert peak <= plan['budget']['observed_peak_working_set_bytes'] and elapsed < 60
    assert all(row['paid_birth'] for row in costs if row['name'] == 'candidate')
    return dict(schema='ORA-EKA0-SOURCE-CERTIFICATE-v1', plan_sha256=PLAN_HASH,
                source_sha256=plan['source_sha256'], worlds=0, vm_steps=0, seed_queries=0, model_calls=0,
                conditional_expressibility_cost='PASS', mutation_viability='UNKNOWN',
                ecological_advantage='UNKNOWN', population_execution='NO_GO',
                truth_rows=truth, edits=edits, genotype_subcube=nodes,
                structural_nodes=sum(n['necessary_structural_condition'] for n in nodes),
                structural_one_edit_route_masks=route, cost_rows=costs,
                conditional_mutation_arithmetic=arithmetic,
                limits=plan['conditional_cost_assumptions'] + [
                    'All programs are developer-authored; none was discovered by evolution or tested in a World.',
                    'CFG overapproximates register branches. A structural route is not viable or neutral.',
                    'Ten-edit subcube is targeted, not an exhaustive or unbiased mutation neighbourhood.',
                    'Stationary candidate cannot demonstrate older-site history after intervening travel.',
                    'Shorter references cannot arise from this fixed-length founder by COPY substitution.',
                    'No inherited acquired answer or useful selected mutation-origin learning has been demonstrated.'],
                resources=dict(wall_seconds=elapsed, windows_peak_working_set_bytes=peak,
                               native_hard_containment_qualified=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = analyze(args.root.resolve())
        payload = json.dumps(result, indent=2, sort_keys=True)
        assert len(payload.encode('utf-8')) <= 1048576
        print(payload)
    except Exception:
        print(json.dumps(dict(schema='ORA-EKA0-SOURCE-CERTIFICATE-FAILURE-v1', traceback=traceback.format_exc())))
        raise
