"""Prepared algebraic edge cases only, no genome or World execution."""
import unittest
from experiments import digital_information41_bounds as b
from experiments.digital_information41_independent import certificate as referee


class InformationBoundsTests(unittest.TestCase):
    def test_actual_port_and_validity_are_required(self):
        for p in (0,1):
            for t in (0,1):self.assertEqual(b.target_identity(p,int(p==t),True),t)
        self.assertIsNone(b.target_identity(0,0,False))
        self.assertNotEqual(b.target_identity(0,0,True),b.target_identity(1,0,True))

    def test_bool_is_not_a_numeric_bill_or_port(self):
        for f,args in ((b.formation,(True,)),(b.gap_energy,(1,True)),
                       (b.strict_tick_bound,(55,True)),(b.target_identity,(True,0,True))):
            with self.assertRaises(ValueError):f(*args)

    def test_state_ceiling_is_not_reachability(self):
        self.assertEqual(b.state_ceiling(13),13*2**41)
        for f in (b.state_ceiling,b.formation):
            for n in (0,33):
                with self.assertRaises(ValueError):f(n)

    def test_release_bound_and_formation_increase(self):
        self.assertEqual(b.earliest_fresh_completion(64,16),79)
        self.assertEqual(b.formation(13)+79,134)
        self.assertEqual(b.formation(32),112)
        self.assertEqual(128-b.formation(32)-16,0)

    def test_success_can_rescue_zero_but_not_prior_death(self):
        self.assertEqual(b.gap_energy(1,1),20)
        self.assertIsNone(b.gap_energy(1,2))
        self.assertEqual(b.gap_energy(12,12),20)
        self.assertIsNone(b.gap_energy(12,13))

    def test_overflow_is_capped_not_future_energy(self):
        self.assertEqual(b.gap_energy(64,1),64)
        self.assertEqual(b.gap_energy(64,21),63)

    def test_shorter_comparator_work_can_bind(self):
        self.assertEqual(b.strict_tick_bound(28,200),172)
        self.assertEqual(b.strict_tick_bound(55,200),199)
        with self.assertRaises(ValueError):b.strict_tick_bound(29,200)
        with self.assertRaises(ValueError):b.strict_tick_bound(28,None)

    def test_independent_checks_do_not_accept_capabilities(self):
        report=b.certificate();self.assertEqual(report,referee())
        for k in ('reachable_capacity_verified','viability_verified','predictive_gain_verified',
                  'probability_model_verified','learning','stage_credit'):self.assertFalse(report[k])
        self.assertEqual(report['strict_comparison_cases'],71840)
        self.assertEqual(report['energy_gap_cases'],4160)
        self.assertEqual(report['seeds_queried'],[])


if __name__=='__main__':unittest.main()
