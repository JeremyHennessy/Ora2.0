import copy
import unittest
from experiments.shelter_gate import panel,decision
from experiments.shelter_audit import audit


class ShelterGateTests(unittest.TestCase):
    def test_all_controls_and_early_stop(self):
        rows=panel();result=decision(rows)
        self.assertEqual(audit(rows)['ledgers'],80)
        self.assertEqual(set(result['positive_funded_bound_by_arm'].values()),{16})
        self.assertEqual(result['shared_strict_advantage_cases'],14)
        self.assertFalse(result['registered_gate_pass'])

    def test_unpaid_cost_and_energy_rejected(self):
        for field in ('repair','construction','total_heat','input'):
            rows=copy.deepcopy(panel());rows[0]['arms']['shared'][field]='0'
            with self.assertRaises(ValueError):audit(rows)

    def test_shuffle_is_expectation_and_bare_self_shields(self):
        for row in panel():
            self.assertEqual(row['arms']['independent'],row['arms']['compact'])
            self.assertTrue(row['arms']['shuffle']['ensemble_moments'])
            self.assertEqual(row['arms']['shuffle']['lost_armor'],'192/5')
            self.assertEqual(row['arms']['shuffle']['lost_workers'],'178/5')
