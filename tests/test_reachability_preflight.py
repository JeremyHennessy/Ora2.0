import unittest
from unittest.mock import patch
from experiments.reachability_preflight import (
    ROLES, fabrication_targets, check_target_claim, fresh_token_opportunity,
    positive_endpoint_witness, report)


class ReachabilityPreflightTests(unittest.TestCase):
    def test_original_all_role_claim_is_contradicted_by_actual_guards(self):
        observed = fabrication_targets()
        self.assertEqual(check_target_claim(ROLES, observed), ['C', 'F', 'H'])
        self.assertEqual(check_target_claim(('S', 'L'), observed), [])

    def test_mutated_guard_is_visible_to_preflight(self):
        # Removing apparatus prerequisites silently would change the finding.
        with patch('experiments.photofactory.Fixture.required', return_value=None):
            self.assertEqual(check_target_claim(ROLES, fabrication_targets()), [])

    def test_fuel_regeneration_cannot_reset_first_use_ancestry(self):
        touched = [True] * 10
        original = touched.copy()
        result = fresh_token_opportunity(touched)
        self.assertFalse(result['fresh_endpoint_possible'])
        self.assertEqual(touched, original)
        result = fresh_token_opportunity([True] * 9 + [False])
        self.assertTrue(result['fresh_endpoint_possible'])
        self.assertFalse(result['sufficient_for_success'])

    def test_unknown_or_coerced_ancestry_is_refused(self):
        for values in (None, [0], [1], [None], 'true'):
            with self.subTest(values=values), self.assertRaises(ValueError):
                fresh_token_opportunity(values)

    def test_positive_witness_uses_actual_maintenance_endpoint(self):
        from experiments.maintain_world import world
        from experiments.maintain_panel_audit import interpret
        # Existing frozen smoke fixture only: no experimental/reserved seeds.
        r = world(0, 'candidate', 'diagnostic', attempts=2, loss_step=1)
        with self.assertRaises(ValueError):
            positive_endpoint_witness(r, lambda record: interpret(record, 'diagnostic'))

    def test_strict_evaluator_success_and_fixture_scope(self):
        for score in ({'success': 1}, {'success': False}, {}, None):
            with self.subTest(score=score), self.assertRaises(ValueError):
                positive_endpoint_witness({}, lambda _: score)
        original = {'success': True, 'scope': 'controlled'}
        self.assertEqual(positive_endpoint_witness({}, lambda _: original), original)
        r = report()
        self.assertFalse(r['scientific_admission'])
        self.assertEqual(r['natural_worlds'], 0)
        self.assertEqual(r['association']['exported_work'], '0')
        self.assertFalse(r['association']['retained_assembly'])
