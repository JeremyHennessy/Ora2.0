"""One bounded custody review of fixed-target paths in CLOSED histories only.

No VM/experiment imports, mutation draws, new seeds, genotype search or launcher.
Tracked code values are read from retained COPY/SELFWRITE/birth records, never
computed by interpreting organism instructions or generating a new history.
"""
import argparse
from collections import Counter
import gc
import hashlib
import json
from pathlib import Path
import time
import traceback

PLAN_HASH = 'b381bdcdf2cca7b07b274e49096cb4df1d502d332eeeaec3301e75e8493629f6'
CORE_HASH = '73ff613663221c5b158e9d3b5d1c03e794989e2ccee9c1081d4f5a9657035c81'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, expected, cap):
    assert path.is_file() and not path.is_symlink() and path.stat().st_size <= cap
    raw = path.read_bytes()
    assert sha(raw) == expected
    return json.loads(raw)


def review_role(row, founder, target, genotype_mask, strict_transition):
    assert sum(row['genesis_program'], []) == founder and row['inheritance_mode'] == 'parent_copy'
    codes = {0: [[v,i] for i,v in enumerate(founder)]}
    born = {0: dict(code=founder[:], parent=None, tick=0, mask=0)}
    positions = {0: 0}
    changed = set()
    dead = set()
    stable_reproduced = set()
    all_reproduced = set()
    contiguous = {0: True}
    writes = {}
    consumed_writes = set()
    own_turns = Counter()
    endings = {}
    records = []
    c = Counter(founders=1, births=0, inside_subcube_births=0, outside_subcube_births=0,
                target_births=0, complete_intended_paths_with_target_reproduction=0,
                one_added_edit_children_later_reproducing_unchanged=0)
    for tick, event in enumerate(row['final']['events'], 1):
        assert event['tick'] == tick
        actor = event['actor']
        assert actor in born and actor not in dead
        own_turns[actor] += 1
        code = codes[actor]
        if 'self_write' in event:
            s = event['self_write']; index = s['index']
            assert code[index] == [s['old'],s['unit']]
            code[index][0] = s['value']
            if s['old'] != s['value']:
                changed.add(actor)
                c['effective_selfwrite_events'] += 1
        for w in event.get('writes', []):
            index = w['index']; wid = w['write_id']
            assert wid not in writes and index in range(27)
            assert w['effective_source'] == 'parent_copy'
            assert code[index] == [w['source_value'], w['source_unit']]
            assert w['source_value'] == w['effective_source_value']
            assert w['mutated'] == (w['value'] != w['effective_source_value'])
            writes[wid] = dict(w, writer=actor)
            c['paid_copy_words'] += 1
            c['mutated_copy_words'] += int(w['mutated'])
        if 'birth' in event:
            b = event['birth']; child = b['child']; cid = child['id']
            assert cid not in born and child['parent'] == actor
            assert len(b['write_ids']) == len(set(b['write_ids'])) == 27
            assert not consumed_writes.intersection(b['write_ids'])
            consumed_writes.update(b['write_ids'])
            copied = [writes[i] for i in b['write_ids']]
            assert [w['index'] for w in copied] == list(range(27))
            assert all(w['writer'] == actor for w in copied)
            assert [[w['value'],w['unit']] for w in copied] == child['code']
            assert child['energy'] == 12 and child['pc'] == 0
            assert child['registers'] == [0,0] and child['memory'] == [0]*8
            assert child['feedback'] == 0 and child['inbox'] is None and child['nursery'] == []
            assert len(child['state_units']) == 16 and child['pos'] == positions[actor]
            values = [w[0] for w in child['code']]
            assert all(type(w) is int and 0 <= w < 32 for w in values)
            source = [w['effective_source_value'] for w in copied]
            parent_birth = born[actor]['code']
            at_division = [w[0] for w in code]
            status = strict_transition(parent_birth, source, values, actor in changed, founder, target)
            path_ok = contiguous[actor] and status in ('faithful','one_added_intended_edit')
            mask = genotype_mask(values, founder, target)
            born[cid] = dict(code=values[:], parent=actor, tick=tick, mask=mask)
            codes[cid] = [pair[:] for pair in child['code']]
            positions[cid] = child['pos']
            contiguous[cid] = path_ok
            all_reproduced.add(actor)
            if actor not in changed:
                stable_reproduced.add(actor)
            c['births'] += 1
            c['inside_subcube_births' if mask is not None else 'outside_subcube_births'] += 1
            c['target_births'] += int(mask == 1023)
            c['transition_' + status] += 1
            c['copied_source_differs_from_parent_birth'] += int(source != parent_birth)
            c['copied_source_differs_from_division_code'] += int(source != at_division)
            records.append(dict(child=cid, parent=actor, generation=child['generation'], birth_tick=tick,
                                position=child['pos'], live_bodies_before_birth=len(born)-1-len(dead),
                                newborn_code=values, parent_birth_code=parent_birth[:],
                                copied_source_vector=source, parent_division_code=at_division,
                                mask=mask, parent_birth_mask=born[actor]['mask'],
                                copied_source_mask=genotype_mask(source, founder, target),
                                parent_effective_selfwrite_before_birth=actor in changed,
                                mutated_words_in_birth=sum(w['mutated'] for w in copied),
                                transition=status, contiguous_intended_ancestry=path_ok,
                                initial_blank_state_verified=True, initial_energy=12))
        if 'after' in event:
            assert codes[actor] == event['after']['code']
            positions[actor] = event['after']['pos']
        if 'death' in event or 'expiry' in event:
            assert actor not in dead
            dead.add(actor)
            endings[actor] = dict(tick=tick, reason='own_turn_expiry' if 'expiry' in event else 'energy_death')
            c['deaths_or_expiries'] += 1
    complete = []
    for record in records:
        child = record['child']
        record.update(later_paid_child=child in all_reproduced,
                      later_paid_child_before_any_effective_code_change=child in stable_reproduced,
                      died_or_expired=child in dead, own_dispatches_observed=own_turns[child],
                      terminal=endings.get(child, dict(alive_at_closed_horizon=True, tick=row['final']['tick'])))
        c['newborns_with_later_paid_child'] += int(child in all_reproduced)
        c['newborns_with_later_paid_child_before_code_change'] += int(child in stable_reproduced)
        if record['transition'] == 'one_added_intended_edit' and child in stable_reproduced:
            c['one_added_edit_children_later_reproducing_unchanged'] += 1
        if record['mask'] == 1023 and record['contiguous_intended_ancestry'] and child in stable_reproduced:
            c['complete_intended_paths_with_target_reproduction'] += 1
            complete.append(child)
    assert c['births'] == row['final']['births']
    assert c['deaths_or_expiries'] == row['final']['deaths']
    assert len(born) - len(dead) == len(row['final']['entities'])
    assert c['paid_copy_words'] == row['final']['writes']
    assert all(own_turns[actor] == row['final']['turns'][str(actor)] for actor in born)
    return dict(counts=dict(c), founder_record=dict(code=founder, initial_energy=12,
                initial_position=0, later_paid_child=0 in all_reproduced,
                later_paid_child_before_any_effective_code_change=0 in stable_reproduced,
                died_or_expired=0 in dead, own_dispatches_observed=own_turns[0],
                terminal=endings.get(0, dict(alive_at_closed_horizon=True, tick=row['final']['tick']))),
                births=records, complete_target_children=complete)


def analyze(root, lab):
    started = time.monotonic()
    plan = load(root/'data/eka0-lifetime-comparison-preparation-20261023.json', PLAN_HASH, 32768)
    assert sha((root/'tools/eka0_lifetime_preparation.py').read_bytes()) == CORE_HASH
    from eka0_lifetime_preparation import validate, genotype_mask, strict_transition
    validation = validate(plan)
    scope = plan['closed_path_review']
    audit = load(root/'data/eka0-feasibility-audit-20261023.json', scope['prior_audit_sha256'], 65536)
    certificate = load(root/'data/eka0-source-certificate-20261023.json', scope['prior_certificate_sha256'], 1048576)
    prior_plan = load(root/'data/eka0-certificate-plan-20261023.json', scope['prior_plan_sha256'], 16384)
    for path, expected in certificate['source_sha256'].items():
        assert sha((root/path).read_bytes()) == expected
    founder = sum(plan['scientific_founder'], [])
    target = sum(plan['authored_reference_programs']['feedback'], [])
    assert prior_plan['founder'] == plan['scientific_founder'] and sum(prior_plan['candidate'], []) == target
    assert genotype_mask(founder, founder, target) == 0 and genotype_mask(target, founder, target) == 1023
    roster = audit['complete_mutating_parent_copy_roster']
    assert len(roster) == len(set(roster)) == 16
    pins = {Path(p['path']).parts[-2]:p for p in audit['input_pins'] if '/raw/data/original/' in p['path'].replace('\\','/')}
    assert set(pins) == set(roster)
    old_counts = {v['closed_role']:v['counts'] for v in audit['details']}
    details = []
    totals = Counter()
    for name in roster:
        assert time.monotonic() - started < 60
        pin = pins[name]
        row = load(lab/Path(pin['path']), pin['sha256'], scope['budget']['max_raw_bytes_each'])
        reviewed = review_role(row, founder, target, genotype_mask, strict_transition)
        c = reviewed['counts']
        assert c['births'] == old_counts[name]['births'] and c['paid_copy_words'] == old_counts[name]['paid_copy_words']
        assert c.get('mutated_copy_words',0) == old_counts[name]['mutations']
        totals.update(c)
        details.append(dict(role=name, input_sha256=pin['sha256'], **reviewed))
        del row
        gc.collect()
    assert sha((root/'tools/eka0_source_certificate.py').read_bytes()) == 'c40937437d61cdb2d8309ae9b52c2bc0fb8e68108b6c7c774c55fdf63d36b802'
    from eka0_source_certificate import peak_working_set
    peak = peak_working_set()
    elapsed = time.monotonic() - started
    assert elapsed < 60 and peak <= scope['budget']['observed_peak_working_set_bytes']
    return dict(schema='ORA-EKA0-CLOSED-MUTATION-PATH-REVIEW-v1', plan_sha256=PLAN_HASH,
                core_sha256=CORE_HASH, source_sha256=certificate['source_sha256'], preparation_validation=validation,
                closed_roles=16, totals=dict(totals), details=details, founder=founder, fixed_target=target,
                evolutionary_path_qualification='UNKNOWN', scientific_execution_ready=False,
                population_execution='NO_GO', worlds=0, vm_steps=0, new_seed_queries=0, model_calls=0,
                limits=['Every actor and paid birth retained; no outcome-selected genotype or new seed.',
                        'This is one targeted ten-edit subcube, not an exhaustive genotype or viable-path search.',
                        'Copied-source vectors may span code changes; they are not necessarily a simultaneous genotype.',
                        'Later paid reproduction before code change is contextual expression, not neutrality or relative fitness.',
                        'No observed target/path is not a global impossibility result; no new search is authorized.',
                        'No authored genotype may be installed as scientific founder by this preparation.'],
                resources=dict(wall_seconds=elapsed, windows_peak_working_set_bytes=peak, native_hard_containment_qualified=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--lab', type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = json.dumps(analyze(args.root.resolve(), args.lab.resolve()), indent=2, sort_keys=True)
        assert len(payload.encode('utf-8')) <= 2097152
        print(payload)
    except Exception:
        print(json.dumps(dict(schema='ORA-EKA0-CLOSED-PATH-FAILURE-v1', traceback=traceback.format_exc())))
        raise
