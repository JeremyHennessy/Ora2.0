import copy
from collections import Counter
import json
import unittest
from experiments.adaptation_shuffle_plan import plan
from experiments.adaptation_shuffle_audit import audit, unique


def source():
    return [dict(id=str(i), event_step=i, observed_step=i+1,
                 cue='A' if i % 2 == 0 else 'B', action='encounter',
                 outcome='resource' if i % 2 == 0 else 'empty') for i in range(4)]


class ShufflePlanTests(unittest.TestCase):
    def test_order_preserves_associations_and_source(self):
        records = source()
        before = copy.deepcopy(records)
        result = audit(records, plan(records, 'order', 5, 4, 0))
        self.assertTrue(result['association_multiset_preserved'])
        self.assertEqual(records, before)

    def test_association_is_not_guaranteed_erasure(self):
        records = source()
        result = audit(records, plan(records, 'association', 5, 4, 0))
        self.assertEqual(result['observations'], 4)
        # No derangement search: empty and singleton windows remain valid.
        self.assertEqual(audit(records, plan(records, 'association', 1, 4, 0))['observations'], 0)
        self.assertEqual(audit(records, plan(records, 'association', 2, 4, 0))['fixed_points'], 1)

    def test_future_and_unobserved_data_do_not_select_donors(self):
        records = source()
        records[2]['observed_step'] = None
        first = plan(records, 'association', 3, 4, 7)
        records[2]['outcome'] = 'future-secret'
        records[3]['cue'] = 'future-phase'
        second = plan(records, 'association', 3, 4, 7)
        self.assertEqual(first['eligible_ids'], ['0', '1'])
        self.assertEqual(first['donor_ids'], second['donor_ids'])
        self.assertNotEqual(first['source_sha256'], second['source_sha256'])
        self.assertNotIn('future-secret', str(second))

    def test_observation_order_and_recent_window(self):
        records = source()
        records[0]['observed_step'] = 10
        p = plan(records, 'order', 11, 2, 2**64-1)
        self.assertEqual(p['eligible_ids'], ['3', '0'])
        audit(records, p)

    def test_forged_future_donor_and_source_are_refused(self):
        records = source()
        p = plan(records, 'association', 3, 4, 0)
        p['donor_ids'][0] = '3'
        with self.assertRaises(ValueError):
            audit(records, p)
        p = plan(records, 'association', 3, 4, 0)
        records[0]['outcome'] = 'forged'
        with self.assertRaises(ValueError):
            audit(records, p)

    def test_paid_cost_or_activation_claim_is_refused(self):
        for key, value in [('physical_cost', 0), ('design_only', False), ('planned_reference_reads', True)]:
            p = plan(source(), 'order', 5, 4, 0)
            p[key] = value
            with self.assertRaises(ValueError):
                audit(source(), p)

    def test_strict_source_and_parameters(self):
        for key, value in [('event_step', True), ('observed_step', 0), ('id', True)]:
            records = source()
            records[1][key] = value
            with self.assertRaises(ValueError):
                plan(records, 'order', 5, 4, 0)
        for cutoff, window, seed in [(True, 4, 0), (5, 0, 0), (5, 4, True), (5, 4097, 0), (5, 4, 2**64)]:
            with self.assertRaises(ValueError):
                plan(source(), 'order', cutoff, window, seed)
        records = source()
        records[0]['phase'] = 'privileged'
        with self.assertRaises(ValueError):
            plan(records, 'order', 5, 4, 0)

    def test_replay_and_bounded_all_seed_examples(self):
        # Determinism/control validation, not actors, worlds, seed screening or holdouts.
        records = source()
        for seed in range(16):
            for kind in ('order', 'association'):
                p = plan(records, kind, 5, 4, seed)
                self.assertEqual(p, plan(records, kind, 5, 4, seed))
                result = audit(records, p)
                self.assertTrue(result['verified'])
                by_id = {r['id']: r for r in records}
                old = Counter((r['cue'], r['action'], r['outcome']) for r in records)
                if kind == 'association':
                    changed = Counter((by_id[n]['cue'], by_id[n]['action'], by_id[d]['outcome'])
                                      for n, d in zip(p['eligible_ids'], p['donor_ids']))
                    self.assertEqual(result['association_multiset_preserved'], old == changed)

    def test_duplicate_json_keys_are_refused(self):
        with self.assertRaises(ValueError):
            json.loads('{"design_only":true,"design_only":false}', object_pairs_hook=unique)


if __name__ == '__main__':
    unittest.main()
