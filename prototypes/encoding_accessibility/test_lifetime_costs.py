import unittest
from lifetime_costs import replay,first_probe_headroom,PROTOCOL


class LifetimeCosts(unittest.TestCase):
    def test_no_future_food(self):
        row=replay([(2,8)],startup=1)
        self.assertFalse(row['completed_ledger'])
        self.assertEqual(row['total_earned'],0)

    def test_reward_atomic_before_death(self):
        self.assertTrue(replay([(1,8)],startup=1)['alive_at_horizon'])
        self.assertFalse(replay([(1,0),(1,8)],startup=1)['completed_ledger'])

    def test_earned_bill_cannot_reuse_startup(self):
        self.assertFalse(replay([(1,15)])['known_cost_earned_copy_witness'])  #22 available, not22 earned
        row=replay([(1,23)])  #30 available, net22 earned
        self.assertTrue(row['known_cost_earned_copy_witness'])
        self.assertEqual(row['terminal_copy_fixture']['remaining'],8)
        self.assertEqual(row['terminal_copy_fixture']['child_memory'],0)
        self.assertFalse(row['full_cost_reproduction_qualified'])

    def test_all_energy_conserved(self):
        row=replay([(1,8),(2,0),(1,8)])
        self.assertEqual(row['terminal_balance']+row['total_known_heat'],8+row['total_earned'])

    def test_missing_costs_never_default_to_free(self):
        self.assertTrue(all(v is None for v in PROTOCOL['unknown_costs'].values()))
        self.assertFalse(PROTOCOL['population_admission'])

    def test_delayed_probe_headroom(self):
        self.assertEqual(first_probe_headroom(2)['necessary_uniform_decoder_extra_ceiling'],[2,5])
        self.assertEqual(first_probe_headroom(3)['necessary_uniform_decoder_extra_ceiling'],[1,6])


if __name__=='__main__':unittest.main()
