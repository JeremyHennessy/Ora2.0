import copy
import json
import unittest
from fractions import Fraction
from experiments.collision_bridge import World, fixtures
from experiments.collision_bridge_audit import audit, unique


class CollisionBridgeTests(unittest.TestCase):
    def test_raw_formation_is_funded_before_source(self):
        r = World('candidate').run()
        event = r['events'][0]
        self.assertEqual(event['after']['time'], '1')
        self.assertEqual(event['channel'], 'associate')
        self.assertEqual(event['formation_debit'], '1')
        self.assertEqual(event['heat_delta'], '0')
        self.assertEqual(event['after']['first_source_contact'], {})
        self.assertTrue(audit(fixtures())['verified'])

    def test_elastic_load_work_is_actual_kinetic_change(self):
        r = World('direct').run()
        event = next(e for e in r['events'] if 'raw:load' in e['parents'])
        self.assertEqual(event['load_work'], '32/25')
        self.assertEqual(event['heat_delta'], '0')

    def test_full_loss_has_no_energy_or_matter_grant(self):
        r = World('candidate').run()
        e = next(e for e in r['events'] if e['kind'] == 'damage')
        self.assertEqual(e['after']['time'], '128')
        self.assertEqual(e['formation_debit'], '0')
        self.assertEqual(e['load_work'], '0')
        self.assertTrue(all(not p['bonds'] for p in e['after']['objects']))
        self.assertGreater(Fraction(e['heat_delta']), 0)
        self.assertIn('s2', r['score']['unused_sources_at_loss'])

    def test_rehashed_free_formation_is_refused(self):
        f = fixtures()
        f['records'][0]['events'][0]['formation_debit'] = '0'
        with self.assertRaises(ValueError):
            audit(f)

    def test_omitted_contact_is_refused(self):
        f = fixtures()
        f['records'][0]['events'].pop(1)
        with self.assertRaises(ValueError):
            audit(f)

    def test_source_and_success_substitution_are_refused(self):
        f = fixtures()
        altered = copy.deepcopy(f)
        altered['records'][0]['initial']['objects'][0]['v'] = '3'
        with self.assertRaises(ValueError):
            audit(altered)
        f['records'][0]['score']['success'] = True
        with self.assertRaises(ValueError):
            audit(f)

    def test_ambiguous_evidence_is_refused(self):
        with self.assertRaises(ValueError):
            json.loads('{"work":0,"work":1}', object_pairs_hook=unique)


if __name__ == '__main__':
    unittest.main()
