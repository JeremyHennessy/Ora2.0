"""Audit retained blind-founder accounting; never execute a controller or World.

Known toy prices only. Unknown costs remain unknown and prohibit qualification.
Terminal copying is a software witness; no offspring executes or is selected.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from census import copy_bits

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT/'data/encoding-accessibility-20261026/funding-upper-bound.json'
INPUT_SHA = 'b46785c15396f2d08e765d58f40677e49067bc5096a06aaea1e1ea8bc84c50a9'
PROTOCOL = dict(schema='ORA-FOUNDER-COST-QUALIFICATION-v1', attempts=1, startup=8,
    genome=0, bits=6, reward=8, full_copy_bill=22,
    scope='48 retained paid-operation ledgers; no controller/environment/population',
    copy_policy='After horizon only, if alive; no environment continuation after copying',
    earned_policy='Copy bill must fit terminal balance minus whole initial8 grant',
    formation='Founder body7 externally supplied at setup; never charge formed offspring twice',
    unknown_costs={'decoder_energy_per_dispatch': None, 'physical_storage_maintenance': None,
        'building_material_acquisition': None, 'copy_clock_and_resource_phase': None,
        'expiry_during_copy': None, 'host_and_fork_energy_mapping': None},
    qualification='All unknown costs and source/clock/custody must be resolved before any full pass',
    population_admission=False)


def replay(operations, startup=8):
    """No debt: debit known price, atomically credit earned reward, then death."""
    energy, heat, earned = startup, 0, 0
    trace = []
    alive = energy > 0
    for i, (cost, gain) in enumerate(operations):
        assert type(cost) is int and cost > 0 and type(gain) is int and gain >= 0
        if not alive or energy < cost:
            alive = False
            break
        before = energy
        energy -= cost
        heat += cost
        energy += gain
        earned += gain
        trace.append(dict(index=i, before=before, charged=cost, earned=gain, after=energy))
        alive = energy > 0
        assert energy + heat == startup + earned
    completed = len(trace) == len(operations)
    qualifies_earned_budget = alive and completed and energy-startup >= 22
    # Even failed boundary cases retain partial copying, but never a child run.
    copying = copy_bits(0, 6, energy) if alive and completed else None
    if copying is not None:
        assert copying['remaining']+copying['heat']+copying['child_energy']==energy
    if qualifies_earned_budget:
        assert copying['complete_fixture_child'] and copying['remaining'] >= startup
    return dict(trace=trace, completed_ledger=completed, alive_at_horizon=alive,
        terminal_balance=energy, total_earned=earned, total_known_heat=heat,
        unspent_initial_grant_required=startup, net_earned_surplus=energy-startup,
        known_cost_earned_copy_witness=qualifies_earned_budget, terminal_copy_fixture=copying,
        full_cost_reproduction_qualified=False)


def first_probe_headroom(delay):
    # Initial attempt1 + feedback2 + delay*1 + paid first probe1, no earlier income.
    known_required = 4+delay
    dispatches = 3+delay
    ceiling = Fraction(8-known_required, dispatches)
    return dict(known_required_before_first_reward=known_required,
        paid_dispatches_to_first_probe=dispatches, unknown_total_cost_headroom=8-known_required,
        necessary_uniform_decoder_extra_ceiling=[ceiling.numerator, ceiling.denominator],
        scope='Necessary only for first probe; not a measured price, sufficient lifetime or fitness bound')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args()
    raw=INPUT.read_bytes();assert hashlib.sha256(raw).hexdigest()==INPUT_SHA
    source=json.loads(raw);cases=source['cases'];assert len(cases)==48
    output=dict(protocol=PROTOCOL,input_sha256=INPUT_SHA,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=[],summary={},
        first_probe_headroom={str(d):first_probe_headroom(d) for d in range(4)},
        full_cost_reproduction_qualified=False, population_executions=0, controller_executions=0)
    for case in cases:
        row=dict(split=case['split'],targets=case['targets'],delay=case['delay'],
                 operations=case['operations'],**replay(case['operations']))
        output['cases'].append(row)
    for split in ('development','reused_validation'):
        rows=[r for r in output['cases'] if r['split']==split]
        output['summary'][split]=dict(cases=len(rows),
            reached_horizon_alive=sum(r['completed_ledger'] and r['alive_at_horizon'] for r in rows),
            known_cost_earned_copy_witnesses=sum(r['known_cost_earned_copy_witness'] for r in rows),
            complete_terminal_copy_fixtures=sum(bool(r['terminal_copy_fixture'] and r['terminal_copy_fixture']['complete_fixture_child']) for r in rows),
            full_cost_qualified=0)
    with args.output.open('x',encoding='utf-8') as f:json.dump(output,f,indent=2)


if __name__=='__main__':main()
