"""Prospective full-family admission and read-origin predicates; no VM execution."""
import json
from .digital_branch_source30 import candidate
from .digital_candidate_admission26 import programmes as old_programmes
from .digital_admission_roles24 import reactive_reachability
from .digital_affine_admission20_audit import endpoint as ordinary_exploration

VERSION = 'DIGITAL-SOURCE-32-ADMISSION-v1'
SEEDS = (32100, 32101)
MODES = ('intact', 'retained_disabled', 'own_disrupted')
REFERENCES = tuple(f'affine{i}' for i in range(8)) + ('alternating', 'fixed0', 'fixed1')

def manifest():
    old = old_programmes()
    candidates = [candidate(i) for i in range(56)]
    references = [dict(role=r, program=old[r], assistance='authored fixed/reactive comparator') for r in REFERENCES]
    return dict(contract=VERSION, candidates=candidates, references=references,
                seeds=list(SEEDS), controls=list(MODES), horizon=512, checkpoint=64,
                candidate_histories=336, reference_histories=66, total_histories=402,
                structural_order=list(range(56)), performance_selection=False,
                primary=False, stage_credit=False, world_histories_executed=0)

def opportunities(row):
    """Requires complete independently verified history before scientific scoring.

    Availability uses truthful native outcomes. Delivered reachability also
    requires real own samples; unrelated substitutions never become own history.
    Duplicate latch reads count once per actual post-change attempt.
    """
    events = row['final']['events']
    assert events and [e['tick'] for e in events] == list(range(1, len(events)+1))
    assert 1 <= len(events) <= 512 and row['control_mode'] in MODES
    actions = []; reads = []; native_reads = []; last = None
    pre_ports = set(); pre_outcomes = set(); post = []; fresh = set()
    for e in events:
        assert type(e['actor']) is int and e['actor'] == 0
        op = e['decoded'][0]
        if op == 6:
            a = e.get('attempt')
            if a is not None:
                assert all(type(a[k]) is int for k in ('packet', 'port', 'success'))
                assert 0 <= a['packet'] < 32 and a['port'] in (0,1) and a['success'] in (0,1)
                attempt = {k:a[k] for k in ('packet','port','success')}
                if e['tick'] < 64:
                    pre_ports.add(a['port']); pre_outcomes.add(a['success'])
                else:
                    post.append(attempt)
                    if a['success'] and a['packet'] >= 16:
                        assert a['packet'] not in fresh
                        fresh.add(a['packet'])
            else: attempt = None
            last = dict(tick=e['tick'], actor=0, attempt=attempt); actions.append(last)
        elif op == 1:
            sample = e['control']['personal_read']; assert sample is not None
            origin = 'initial' if last is None else 'empty_reset' if last['attempt'] is None else 'own_actual_attempt'
            source = last['tick'] if origin == 'own_actual_attempt' else None
            value = last['attempt']['success'] if source is not None else 0
            assert (sample['own_source_tick'] is None if source is None else type(sample['own_source_tick']) is int)
            assert type(sample['original']) is int and sample['original'] in (0,1)
            assert sample['own_source_tick'] == source and sample['original'] == value
            assert type(sample['value']) is int and sample['value'] in (0,1)
            r = dict(tick=e['tick'], actor=0, origin=origin, source_tick=source, value=value)
            native_reads.append(r)
            if row['control_mode'] != 'own_disrupted':
                assert sample['value'] == value
                reads.append(r)
    alive = not any('death' in e and e['tick'] <= 64 for e in events) and len(events) >= 64
    cold = dict(pre_ports=sorted(pre_ports), pre_outcomes=sorted(pre_outcomes),
                alive_through_change=alive, post_actions=len(post),
                post_successes=sum(a['success'] for a in post), fresh_packets=len(fresh))
    def record(rs): return dict(alive_through_change=alive, actions=actions, reads=rs)
    distinct = {r['source_tick']:r['value'] for r in native_reads if r['source_tick'] is not None and r['source_tick'] >= 64}
    return dict(cold_survival=alive, ordinary_exploration=ordinary_exploration(cold),
                native_reactive_reachability=reactive_reachability(record(native_reads)),
                delivered_own_reactive_reachability=row['control_mode']!='own_disrupted' and reactive_reachability(record(reads)),
                distinct_post_own_attempts=len(distinct), post_own_outcomes=sorted(set(distinct.values())),
                own_read_events=sum(r['source_tick'] is not None for r in native_reads),
                empty_or_initial_reads=sum(r['source_tick'] is None for r in native_reads),
                cold=cold, learning=False, stage_credit=False)

if __name__ == '__main__':
    print(json.dumps(manifest(), sort_keys=True, separators=(',', ':')))
