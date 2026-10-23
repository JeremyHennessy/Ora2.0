"""Pure source-contract/bound fixtures; never run an organism or a World."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from eka1_capability_preparation import validate, resource_bounds


class CapabilityPreparationTests(unittest.TestCase):
    def setUp(self):
        self.p = json.loads((ROOT/'data/eka1-capability-proposal-20261023.json').read_text(encoding='utf-8'))

    def reject(self):
        with self.assertRaises(AssertionError): validate(self.p)

    def test_valid_draft_never_authorizes_world(self):
        self.assertFalse(validate(self.p)['scientific_execution_ready'])

    def test_target_genome_not_an_evolutionary_goal(self):
        self.p['exact_target_genome'] = [0]*27
        self.reject()

    def test_founder_cannot_be_authored_learner(self):
        self.p['ordinary_founder'][0] = [1,0,0]
        self.reject()

    def test_no_best_dose_selection(self):
        self.p['discovery']['best_dose_selection'] = True
        self.reject()

    def test_no_replacement_with_promising_mutant(self):
        self.p['discovery']['origin_sampling'] = 'BEST_SURVIVING_MUTANT'
        self.reject()

    def test_no_clone_pseudoreplication(self):
        self.p['discovery']['unit'] = 'DIAGNOSTIC_CLONE'
        self.reject()

    def test_equal_realized_food_is_not_matching(self):
        self.p['resource_matching']['equal_realized_meals'] = True
        self.reject()

    def test_missing_forks_cannot_be_free(self):
        self.p['diagnostics']['max_proposed_forks_per_discovery_world'] = 0
        self.reject()

    def test_missing_causal_qualification_cannot_be_marked_pass(self):
        self.p['gates']['nonlethal_paid_causal_information_assay'] = 'PASS'
        self.reject()

    def test_unjustified_sample_size_rejected(self):
        self.p['registration']['discovery_world_count'] = 100
        self.reject()

    def test_opcode_count_not_capability(self):
        self.p['functional_claim']['opcode_presence_is_acceptance'] = True
        self.reject()

    def test_metadata_cannot_enable_launch(self):
        self.p['execution_ready'] = True
        self.reject()

    def test_conservation_excludes_constructor_and_new_child_energy(self):
        r = resource_bounds(self.p)
        self.assertEqual(r['maximum_organism_accessible_energy'],21772)
        self.assertEqual(r['constructor_energy_credited_as_organism_input'],0)
        self.assertEqual(r['completed_birth_energy_ceiling_at_full_4096_dispatch_horizon'],392)
        self.assertEqual(r['simultaneous_mature_material_ceiling'],11)

    def test_mutation_upper_bound_never_becomes_useful_origin_lower_bound(self):
        r = resource_bounds(self.p)
        self.assertFalse(r['mutation_opportunity_qualified'])
        self.assertTrue(all(v['useful_paid_origin_lower_bound']==0 for v in r['hypothetical_mutation_supply']))
        self.assertFalse(r['resource_affordability_qualified'])


if __name__ == '__main__':
    unittest.main()
