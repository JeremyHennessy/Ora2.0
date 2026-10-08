import copy
import itertools
import unittest

from experiments import template_neutral as worker
from experiments import template_neutral_audit as audit


def tokens(actor, count):
    return [dict(unit=f'fixture-{actor}:{i}', origin='genesis', actor=actor, nutrient=None, tick=-1) for i in range(count)]


def fixture(x, y, left, right, mode='active'):
    # Explicit authored reactants, not a fresh monomer-only experimental world.
    s, _ = worker.genesis(1, 0, mode)
    for i, bit in enumerate(x+y):
        aid = f'a{i:03d}'
        s['atoms'][aid]['bit'] = bit
        s['history']['g'+str(i)]['bits'] = bit
        del s['objects']['g'+str(i)]
    for oid, bits, start, work in (('x', x, 0, left), ('y', y, len(x), right)):
        obj = worker.birth(bits, [f'a{i:03d}' for i in range(start, start+len(bits))],
                           [] if mode == 'shared' else tokens(oid, work), -1, 'fixture')
        s['objects'][oid] = obj
        s['history'][oid] = copy.deepcopy(obj)
    if mode == 'shared':
        s['bank'] = tokens('x', left)+tokens('y', right)
    return s


def request(s, action, owner, partner=None):
    ids = sorted(s['objects'])
    other = [k for k in ids if k != owner]
    return [action, ids.index(owner), other.index(partner) if partner else 0, 0, 0]


class NeutralTemplateTests(unittest.TestCase):
    def test_all_added_ligation_ledgers_and_actual_executors(self):
        sequences = [''.join(b) for n in (1, 2, 3) for b in itertools.product('01', repeat=n)]
        count = 0
        for x, y in itertools.product(sequences, repeat=2):
            if len(x+y) > 4:
                continue
            for left, right, mode in itertools.product(range(4), range(4), ('active', 'shared')):
                s = fixture(x, y, left, right, mode)
                draw = request(s, 0, 'x', 'y')
                actual, opp, result = worker.step(s, mode, 0, draw)
                expected, op, receipt = audit.transition(s, mode, 0, draw)
                self.assertEqual((actual, opp, result), (expected, op, receipt))
                self.assertEqual(audit.ledger(actual), audit.ledger(s))
                self.assertEqual(result['outcome'] == 'ligated', left+right >= 2)
                count += 1
        self.assertEqual(count, 2176)

    def test_authored_own_capture_funds_functional_and_renewed_descendants(self):
        s = fixture('00', '1', 2, 0)
        for aid in s['nutrients']:
            s['atoms'][aid]['bit'] = '1'
        budget = audit.ledger(s)
        initial = copy.deepcopy(s)
        events = []
        owners = ['x']*6+['o5']*6+['o11']
        for tick, owner in enumerate(owners):
            action = 2 if tick in (5, 11) else 3
            draw = request(s, action, owner)
            before = audit.sha(s)
            expected, opp, result = audit.transition(s, 'active', tick, draw)
            actual, op, receipt = worker.step(s, 'active', tick, draw)
            self.assertEqual((actual, op, receipt), (expected, opp, result))
            self.assertEqual(audit.ledger(actual), budget)
            events.append(dict(tick=tick, draw=draw, opportunities=opp, result=result, before=before, after=audit.sha(actual)))
            s = actual
        stats = worker.statistics(initial, events, s)
        self.assertEqual(stats, audit.measure(initial, events, s))
        self.assertEqual(stats['primary_children'], 2)
        self.assertEqual(stats['renewed_children'], 1)
        self.assertTrue(all(s['history'][k]['own_funded'] for k in ('o5', 'o11')))
        self.assertTrue(set(s['objects']['x']['atoms']).isdisjoint(s['objects']['o5']['atoms']))

    def test_initial_or_other_actor_work_does_not_count_as_self_funding(self):
        for source in ('genesis', 'other'):
            s = fixture('00', '1', 7, 0)
            if source == 'other':
                for t in s['objects']['x']['tokens']:
                    t.update(origin='nutrient', actor='y', nutrient='external-fixture', tick=-1)
            draw = request(s, 2, 'x')
            state, opp, result = worker.step(s, 'active', 0, draw)
            self.assertEqual((state, opp, result), audit.transition(s, 'active', 0, draw))
            self.assertEqual(result['outcome'], 'copied')
            self.assertFalse(result['own_funded'])
            self.assertFalse(state['history']['o0']['own_funded'])

    def test_starvation_and_ghost_prices_do_not_create_free_material(self):
        for mode in worker.ARMS:
            s = fixture('00', '1', 0, 0, mode)
            for action in (0, 2, 3, 5):
                draw = request(s, action, 'x', 'y')
                state, opp, receipt = worker.step(s, mode, 0, draw)
                self.assertEqual((state, opp, receipt), audit.transition(s, mode, 0, draw))
                self.assertEqual(audit.ledger(s), audit.ledger(state))
                self.assertEqual(receipt['charged'], 0)
        s = fixture('00', '1', 7, 0)
        state, opp, receipt = worker.step(s, 'ghost', 0, request(s, 2, 'x'))
        self.assertEqual(receipt['charged'], 7)
        self.assertEqual(receipt['heat'], 7)
        self.assertEqual(state['ready'], s['ready'])
        self.assertNotIn('o0', state['objects'])

    def test_existing_development_stream_and_rehashed_forgeries(self):
        # Existing development seed 1 only; never run fresh 128..143 here.
        for work in (2, 0):
            record = worker.simulate(1, work)
            audit.verify_record(record, 1, work)
            if work == 0:
                for arm in record['arms']:
                    self.assertEqual(arm['statistics']['copies'], 0)
                    self.assertEqual(arm['statistics']['ligations'], 0)
        for field in ('cost', 'token', 'endpoint', 'noise', 'origin'):
            r = copy.deepcopy(record)
            arm = r['arms'][0]
            if field == 'cost':
                arm['events'][0]['result']['charged'] += 1
                arm['events'][0]['sha256'] = audit.sha({k: v for k, v in arm['events'][0].items() if k != 'sha256'})
            elif field == 'token':
                arm['terminal']['bank'] = tokens('invented', 1)
            elif field == 'endpoint':
                arm['statistics']['primary_children'] += 1
            elif field == 'noise':
                r['draws'][0][0] = (r['draws'][0][0]+1) % 8
            else:
                arm['initial']['atoms']['a000']['origin'] = 'internal'
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit.verify_record(r, 1, 0)

    def test_material_and_work_duplicate_ownership_reject(self):
        s, _ = worker.genesis(1, 2, 'active')
        for field in ('material', 'work'):
            bad = copy.deepcopy(s)
            if field == 'material':
                bad['ready'].append('a000')
            else:
                bad['bank'] += bad['objects']['g0']['tokens']
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit.ledger(bad)


if __name__ == '__main__':
    unittest.main()
