import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('cost', Path(__file__).resolve().parents[1]/'tools/eka1_feedback_cost_preflight.py')
cost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cost)


class CostPreflightTests(unittest.TestCase):
    def test_probe_at_expiry_is_observable_not_guaranteed_survivor(self):
        r = cost.probe_floor(252, 4092, 4)
        self.assertTrue(r['age_permits_probe'])
        self.assertTrue(r['probe_on_expiry_boundary'])
        self.assertTrue(r['energy_floor_permits_probe_without_incoming_gain'])
        self.assertFalse(r['energy_positive_after_no_intake_probe_before_expiry_if_path_completes'])
        self.assertFalse(r['age_permits_survival_past_probe'])
        self.assertTrue(cost.probe_floor(252, 4092, 5)['energy_positive_after_no_intake_probe_before_expiry_if_path_completes'])
        self.assertFalse(cost.probe_floor(252, 4092, 5)['age_permits_survival_past_probe'])
        self.assertFalse(r['path_or_opportunity_qualified'])

    def test_one_less_turn_energy_or_global_slot_fails_necessary_floor(self):
        self.assertFalse(cost.probe_floor(253, 4092, 4)['age_permits_probe'])
        self.assertFalse(cost.probe_floor(252, 4093, 4)['global_floor_permits_probe'])
        self.assertFalse(cost.probe_floor(252, 4092, 3)['energy_floor_permits_probe_without_incoming_gain'])

    def test_extra_cost_cannot_be_hidden_in_base_charge(self):
        r = cost.probe_floor(0, 100, 6, extra_spend=3)
        self.assertFalse(r['energy_floor_permits_probe_without_incoming_gain'])
        self.assertTrue(cost.probe_floor(0, 100, 8, extra_spend=3)['energy_positive_after_no_intake_probe_before_expiry_if_path_completes'])

    def test_replay_is_charged_three_times_not_one(self):
        r = cost.three_replay_bill(100, 20)
        self.assertEqual(r['prefix_replay_dispatches'], 300)
        self.assertEqual(r['total_dispatch_ceiling'], 360)
        self.assertEqual(r['genesis_formation_heat_component_all_worlds'], 129)
        self.assertEqual(r['genesis_energy_stock_all_worlds'], 4260)
        self.assertFalse(r['pricing_qualified'])
        self.assertFalse(r['checkpoint_authority_granted'])

    def test_full_horizon_and_shortcut_refusals(self):
        self.assertEqual(cost.three_replay_bill(4092, 4)['total_dispatch_ceiling'], 12288)
        for prefix, suffix in [(4093, 4), (100, 0), (100, 3), (-1, 4)]:
            with self.assertRaises(ValueError): cost.three_replay_bill(prefix, suffix)

    def test_boolean_and_out_of_range_are_not_budgets(self):
        for age, tick, energy in [(True, 0, 4), (0, False, 4), (0, 0, True), (256, 0, 4), (0, 4097, 4), (0, 0, 65)]:
            with self.assertRaises(ValueError): cost.probe_floor(age, tick, energy)


if __name__ == '__main__':
    unittest.main()
