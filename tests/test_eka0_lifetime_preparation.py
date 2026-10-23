"""Pure metadata/literal fixtures: no VM, producer, seeds or live store."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from eka0_lifetime_preparation import validate, genotype_mask, strict_transition


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT/'data/eka0-lifetime-comparison-preparation-20261023.json').read_text(encoding='utf-8'))
        self.old = sum(self.plan['scientific_founder'], [])
        self.new = sum(self.plan['authored_reference_programs']['feedback'], [])

    def test_review_never_grants_admission(self):
        self.assertFalse(validate(self.plan)['scientific_execution_ready'])

    def test_metadata_cannot_enable_execution(self):
        self.plan['execution_ready'] = True
        with self.assertRaises(AssertionError): validate(self.plan)

    def test_scientific_founder_cannot_be_replaced(self):
        self.plan['scientific_founder'] = self.plan['authored_reference_programs']['feedback']
        with self.assertRaises(AssertionError): validate(self.plan)

    def test_realized_meal_matching_rejected(self):
        self.plan['food_matching']['equal_realized_meals'] = True
        with self.assertRaises(AssertionError): validate(self.plan)

    def test_survivor_denominator_rejected(self):
        self.plan['estimand']['denominator'] = 'SURVIVORS'
        with self.assertRaises(AssertionError): validate(self.plan)

    def test_target_selected_fixed_port_rejected(self):
        del self.plan['authored_reference_programs']['fixed1']
        with self.assertRaises(AssertionError): validate(self.plan)

    def test_free_feedback_in_blind_rejected(self):
        self.plan['authored_reference_programs']['nursery_aware_blind'][0] = [1,0,0]
        with self.assertRaises(AssertionError): validate(self.plan)

    def test_genome_length_cost_mismatch_rejected(self):
        self.plan['authored_reference_programs']['blind_alternator'].pop()
        with self.assertRaises(AssertionError): validate(self.plan)

    def test_missing_scientific_gate_rejected(self):
        self.plan['required_gates'].pop()
        with self.assertRaises(AssertionError): validate(self.plan)

    def test_invented_lesion_qualification_rejected(self):
        self.plan['causal_controls']['food_feedback_lesion_and_paid_sham'] = 'PASS'
        with self.assertRaises(AssertionError): validate(self.plan)

    def test_subcube_endpoints_and_outside(self):
        self.assertEqual(genotype_mask(self.old, self.old, self.new), 0)
        self.assertEqual(genotype_mask(self.new, self.old, self.new), 1023)
        outside = self.old[:]; outside[0] = 31
        self.assertIsNone(genotype_mask(outside, self.old, self.new))

    def test_one_edit_is_not_a_multiedit_jump(self):
        one = self.old[:]; i = next(i for i in range(27) if self.old[i] != self.new[i]); one[i] = self.new[i]
        self.assertEqual(strict_transition(self.old,self.old,one,False,self.old,self.new), 'one_added_intended_edit')
        self.assertEqual(strict_transition(self.old,self.old,self.new,False,self.old,self.new), 'multiedit_or_reversion')

    def test_copy_time_change_is_not_birth_genome_edge(self):
        self.assertEqual(strict_transition(self.old,self.new,self.new,False,self.old,self.new), 'copied_source_differs_from_birth')
        self.assertEqual(strict_transition(self.old,self.old,self.old,True,self.old,self.new), 'parent_code_changed')

    def test_reversion_does_not_advance_target_route(self):
        self.assertEqual(strict_transition(self.new,self.new,self.old,False,self.old,self.new), 'multiedit_or_reversion')


if __name__ == '__main__':
    unittest.main()
