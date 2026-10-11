import copy
import json
from fractions import Fraction
import unittest
from experiments.association_channel import State, step, fixtures
from experiments.association_channel_audit import audit_event, audit_fixture, unique_object


class AssociationChannelTests(unittest.TestCase):
    def test_registered_history_and_exact_reversal(self):
        r = fixtures()
        proof = audit_fixture(r)
        self.assertEqual(proof['cycle_recipient_net'], '0')
        self.assertFalse(proof['retained_assembly'])
        self.assertEqual(r['events'][0]['after'], r['events'][1]['before'])
        self.assertEqual(r['events'][1]['after'], r['events'][0]['before'])
        self.assertEqual([e['outcome'] for e in r['events']],
                         ['associate', 'release', 'recipient-full', 'recipient-empty', 'no-contact'])

    def test_scale_independence_and_finite_boundaries(self):
        # Arithmetic fixtures, not a scientific parameter search or price calibration.
        for b in (Fraction(1, 7), Fraction(3, 2), Fraction(10)):
            for bound, n in ((False, 0), (False, 1), (True, 1), (True, 2), (False, 2), (True, 0)):
                s = State(('a', 'b'), 'r', b, 2, n, bound, True)
                event = step(s)
                audit_event(event)
                q = event['after']
                returned = step(State(tuple(q['members']), q['recipient'], Fraction(q['binding']),
                                      q['capacity'], q['excitation'], q['bound'], q['contact']))
                self.assertEqual(returned['after'], s.record())

    def test_independent_interpreter_rejects_seven_corruptions(self):
        for field, value in [('excitation', 2), ('recipient', 'substitute'),
                             ('contact', False), ('capacity', 3)]:
            r = copy.deepcopy(fixtures())
            r['events'][0]['after'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit_fixture(r)
        for field, value in [('recipient_transfer', '0'), ('useful_work', '3/2'), ('outcome', 'release')]:
            r = copy.deepcopy(fixtures())
            r['events'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit_fixture(r)

    def test_invalid_material_and_capacity_states(self):
        for args in [(('a', 'b'), 'a', Fraction(1), 2, 0, False, True),
                     (('a', 'b'), 'r', Fraction(0), 2, 0, False, True),
                     (('a', 'b'), 'r', Fraction(1), 2, 3, False, True),
                     (('a', 'b'), 'r', Fraction(1), True, 0, False, True)]:
            with self.assertRaises(ValueError):
                State(*args)

    def test_ambiguous_json_is_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"after":{"excitation":0,"excitation":1}}', object_pairs_hook=unique_object)


if __name__ == '__main__':
    unittest.main()
