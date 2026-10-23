"""Read authenticated CLOSED events and calculate scalar cost/supply bounds.

No experiment imports, VM, new seed hashes, policy rollout or live-store access.
Observed targets are analyst metadata, never supplied to a policy or organism.
"""
import argparse
import gc
import hashlib
import json
import time
import traceback
from collections import Counter
from pathlib import Path

PLAN_HASH = '91dc7b1070b2b956f14b27d14645b9b5cc9fc29ac04f73d7ddb37aba9389911e'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, expected, cap):
    assert path.is_file() and not path.is_symlink() and path.stat().st_size <= cap
    raw = path.read_bytes()
    assert sha(raw) == expected
    return json.loads(raw)


def first_child(name, program, path, matching):
    """Algebra on declared contiguous cost groups, not program interpretation."""
    assert len(program) == 9 and all(len(t) == 3 for t in program)
    assert all(0 <= w < 32 for t in program for w in t)
    if name.startswith('fixed') and not matching:
        return dict(name=name, initially_matching=False, status='NO_INTAKE_CANNOT_PAY_MINIMUM67', paid_birth=False)
    energy = 12 - path['startup_dispatches']
    turns = path['startup_dispatches']
    heat = turns
    overflow = captures = 0
    groups = []
    for i in range(path['max_cycles']):
        success = (i % 2 == (0 if matching else 1)) if name == 'blind27' else True
        after_food = energy - 1
        if success:
            loss = max(0, after_food + 20 - 64)
            overflow += loss
            heat += loss
            after_food = min(64, after_food + 20)
            captures += 1
        copy_extra = 3 if i < 9 else 0
        after_copy_base = after_food - path['copy_offset']
        assert not copy_extra or after_copy_base >= 3
        guard = after_food - path['divide_offset'] - copy_extra
        assert after_food > 0 and after_copy_base - copy_extra > 0 and guard > 0
        birth = i >= 8 and guard >= 30
        dispatches = path['cycle_dispatches'] - int(birth)
        energy = after_food - dispatches + 1 - copy_extra - (30 if birth else 0)
        assert energy > 0
        turns += dispatches
        heat += dispatches + copy_extra + (18 if birth else 0)
        groups.append(dict(group=i+1, success=success, dispatches=dispatches, copy_extra=copy_extra,
                           division_guard=guard, division_refused=not birth, end_energy=energy))
        if birth:
            assert turns < 256 and 12 + captures * 20 == energy + 12 + heat
            return dict(name=name, initially_matching=matching, status='CONDITIONAL_FIRST_CHILD_ONLY',
                        paid_birth=True, own_turn=turns, parent_energy=energy, child_energy=12,
                        captures=captures, heat=heat, cap_heat=overflow, mature_material=43,
                        paid_copy_words=27, parent_nursery_child_state_material=86, groups=groups)
    raise AssertionError('No affordable child within frozen reference group limit')


def closed_counts(row):
    c = Counter()
    last_site = {}
    last_actor = {}
    positions = {0: 0}
    for e in row['final']['events']:
        c['dispatches'] += 1
        c['births'] += int('birth' in e)
        c['deaths_or_expiries'] += int('death' in e or 'expiry' in e)
        c['renewal_offers'] += len(e.get('input', []))
        for offer in e.get('input', []):
            c['renewal_' + offer['outcome']] += 1
        c['stock_unlock_events'] += int('release' in e)
        actor = e['actor']
        if e['decoded'][0] == 6:
            c['forages'] += 1
            attempt = e.get('attempt')
            pos = attempt['position'] if attempt else positions[actor]
            present = attempt is not None
            record = dict(present=present, target=attempt['target'] if present else None, pos=pos)
            if present:
                c['nonempty_attempts'] += 1
                c['successes' if attempt['success'] else 'nonempty_failures'] += 1
                packet = attempt['packet']
                c['renewed_attempts' if packet >= 64 else 'special_stock_attempts' if 16 <= packet < 32 else 'ordinary_stock_attempts'] += 1
            else:
                assert e['feedback'] == 0
                c['empty_feedback_zero'] += 1
            previous = last_site.get((actor, pos))
            if previous is not None:
                c['repeated_site_pairs'] += 1
                if previous['present'] and present:
                    label = 'both_nonempty_target_stable' if previous['target'] == record['target'] else 'both_nonempty_target_changed'
                else:
                    label = 'prior_' + ('nonempty' if previous['present'] else 'empty') + '_current_' + ('nonempty' if present else 'empty')
                c['pair_' + label] += 1
                if last_actor[actor]['pos'] != pos:
                    c['other_site_intervened_pairs'] += 1
                    c['other_site_' + label] += 1
            last_site[actor, pos] = record
            last_actor[actor] = record
        if 'after' in e:
            positions[actor] = e['after']['pos']
        if 'birth' in e:
            child = e['birth']['child']
            positions[child['id']] = child['pos']
    assert c['forages'] == c['nonempty_attempts'] + c['empty_feedback_zero']
    assert c['nonempty_attempts'] == c['successes'] + c['nonempty_failures']
    assert c['nonempty_attempts'] == c['renewed_attempts'] + c['special_stock_attempts'] + c['ordinary_stock_attempts']
    assert c['repeated_site_pairs'] == sum(c['pair_' + label] for label in (
        'both_nonempty_target_stable', 'both_nonempty_target_changed', 'prior_empty_current_empty',
        'prior_empty_current_nonempty', 'prior_nonempty_current_empty'))
    assert c['other_site_intervened_pairs'] == sum(c['other_site_' + label] for label in (
        'both_nonempty_target_stable', 'both_nonempty_target_changed', 'prior_empty_current_empty',
        'prior_empty_current_nonempty', 'prior_nonempty_current_empty'))
    assert c['births'] == row['final']['births'] and c['deaths_or_expiries'] == row['final']['deaths']
    assert len(row['final']['entities']) == 1 + c['births'] - c['deaths_or_expiries']
    assert c['successes'] == 64 + row['final']['admitted'] - len(row['final']['food'])
    assert c['dispatches'] == row['final']['tick']
    assert c['renewal_offers'] == row['final']['offered']
    assert c['renewal_admitted'] == row['final']['admitted']
    assert c['renewal_rejected'] == row['final']['rejected']
    return dict(c)


def analyze(root, lab):
    started = time.monotonic()
    plan = load(root/'data/eka0-environment-payoff-plan-20261023.json', PLAN_HASH, 16384)
    prior = load(root/'data/eka0-feasibility-audit-20261023.json', plan['prior_audit_sha256'], 65536)
    certificate = load(root/'data/eka0-source-certificate-20261023.json', plan['prior_certificate_sha256'], 1048576)
    for path, expected in certificate['source_sha256'].items():
        assert sha((root/path).read_bytes()) == expected
    roster = prior['complete_mutating_parent_copy_roster']
    assert len(roster) == len(set(roster)) == 16
    pins = {Path(p['path']).parts[-2]: p for p in prior['input_pins'] if '/raw/data/original/' in p['path'].replace('\\', '/')}
    assert set(pins) == set(roster)
    totals = Counter()
    doses = {1: Counter(), 8: Counter()}
    details = []
    old_counts = {p['closed_role']: p['counts'] for p in prior['details']}
    for name in roster:
        assert time.monotonic() - started < 60
        pin = pins[name]
        row = load(lab/Path(pin['path']), pin['sha256'], plan['budget']['max_raw_bytes_each'])
        c = closed_counts(row)
        assert c['dispatches'] == old_counts[name]['executed_ticks']
        assert c['births'] == old_counts[name]['births']
        totals.update(c)
        doses[row['dose']].update(c)
        details.append(dict(role=name, input_sha256=pin['sha256'], counts=c))
        del row
        gc.collect()
    refs = [first_child(name, program, plan['cost_paths'][name], match)
            for name, program in plan['programs'].items() for match in (True, False)]
    candidate_rows = [r for r in certificate['cost_rows'] if r['name'] == 'candidate']
    assert len(refs) + len(candidate_rows) == 8
    supply = []
    for site, initial in enumerate((32, 16, 16, 0)):
        for T in (64, 256, 2048, 4096):
            packets = initial + 4 * (T // 64)
            birth_upper = (12 + 20 * packets - T) // 45
            supply.append(dict(site=site, global_dispatches=T, stock_plus_offers_upper=packets,
                               completed_birth_upper_if_D_equals_T=birth_upper,
                               specialization='One founder, whole lineage stationary at this site, all dispatches focal, no inbound transfers; not applied to mobile closed histories.'))
    # Exact integer identities; no new reproductive trajectories are generated.
    identities = dict(feedback_nine_cycle_gross_parent_cost=9*6+27+30,
                      feedback_nine_capture_intake=9*20,
                      blind_eighteen_cycle_two_child_cost=18*5+54+60,
                      blind_nine_capture_intake=9*20,
                      blind_extra_full_nursery_two_cycle_intake=20,
                      blind_extra_full_nursery_two_cycle_dispatch_cost=10,
                      site_renewal_energy_per_global_tick='5/4',
                      all_four_sites_renewal_energy_per_global_tick='5',
                      stationary_one_site_renewal_surplus_coefficient='1/180 births/global dispatch in the source bound after separating initial stock; not a realized rate or infinite-horizon qualification (source horizon4096)',
                      supply_guaranteed=False)
    # Read-only Windows process accounting, reused WITHOUT invoking its analysis.
    assert sha((root/'tools/eka0_source_certificate.py').read_bytes()) == 'c40937437d61cdb2d8309ae9b52c2bc0fb8e68108b6c7c774c55fdf63d36b802'
    from eka0_source_certificate import peak_working_set
    peak = peak_working_set()
    elapsed = time.monotonic() - started
    assert elapsed < 60 and peak <= plan['budget']['observed_peak_working_set_bytes']
    return dict(schema='ORA-EKA0-ENVIRONMENT-PAYOFF-v1', plan_sha256=PLAN_HASH,
                source_sha256=certificate['source_sha256'], worlds=0, vm_steps=0, new_seed_queries=0, model_calls=0,
                closed_roles=16, details=details, totals=dict(totals), by_dose={str(k):dict(v) for k,v in doses.items()},
                same27_reference_rows=refs, prior_candidate_rows=candidate_rows,
                accounting_identities=identities, source_supply_upper_bounds=supply,
                repeated_site_opportunity='OBSERVATIONAL_MARKERS_ONLY_NOT_CAUSAL_EVIDENCE',
                ecological_superiority='UNKNOWN', mutation_viability='UNKNOWN', population_execution='NO_GO',
                scope_limits=plan['limits'], resources=dict(wall_seconds=elapsed, windows_peak_working_set_bytes=peak,
                                                            native_hard_containment_qualified=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--lab', type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = json.dumps(analyze(args.root.resolve(), args.lab.resolve()), indent=2, sort_keys=True)
        assert len(payload.encode('utf-8')) <= 1048576
        print(payload)
    except Exception:
        print(json.dumps(dict(schema='ORA-EKA0-ENVIRONMENT-PAYOFF-FAILURE-v1', traceback=traceback.format_exc())))
        raise
