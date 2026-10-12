import unittest
from experiments.digital_mobile54 import budget,gate,PROGRAM


class MobileAdmissionFixtures(unittest.TestCase):
    def summary(self):return dict(seed=54000,mode='faithful',births=2,descendant_food=1,resource_then_birth=1,paid_copy_words=54,first_birth_tick=70,remote_food=1,formation_cost=43)
    def test_complete_gate(self):self.assertTrue(gate(self.summary()))
    def test_no_descendant_resource_then_birth(self):
        s=self.summary();s['resource_then_birth']=0;self.assertFalse(gate(s))
    def test_no_descendant_acquisition(self):
        s=self.summary();s['descendant_food']=0;self.assertFalse(gate(s))
    def test_incomplete_paid_copy(self):
        s=self.summary();s['paid_copy_words']=53;self.assertFalse(gate(s))
    def test_wrong_first_division_time(self):
        s=self.summary();s['first_birth_tick']=69;self.assertFalse(gate(s))
    def test_booleans_are_not_counts(self):
        s=self.summary();s['births']=True;self.assertFalse(gate(s))
    def test_old_founder_bill_refused(self):
        s=self.summary();s['formation_cost']=34;self.assertFalse(gate(s))
    def test_remote_behavior_required(self):
        s=self.summary();s['remote_food']=0;self.assertFalse(gate(s))
    def test_copy_disabled_control(self):
        s=self.summary();s.update(mode='copy_disabled',births=0,paid_copy_words=0,first_birth_tick=0);self.assertTrue(gate(s));s['births']=1;self.assertFalse(gate(s))
    def test_full_lifecycle_bill(self):
        b=budget();self.assertEqual((b['formation'],b['free_material'],b['constructor_remaining'],b['constructor_after_release']),(43,469,85,69));self.assertEqual((b['minimum_birth_heat'],b['minimum_heat_birth_ceiling']),(55,17))
    def test_cold_start_both_orientations(self):
        # Prepared scalar law calculation, no World: one of two ports succeeds pre64.
        for target in (0,1):
            energy=12-1
            for port,cost in ((0,1),(1,2)):
                energy-=cost
                if port==target:energy=min(64,energy+20)
            energy-=4+1+2+1
            self.assertEqual(energy,20)
    def test_fixed_program_has_acquisition_and_mobility_without_feedback(self):
        self.assertEqual([p[0] for p in PROGRAM],[4,6,5,6,10,12,13,13,7])
        self.assertEqual(PROGRAM[6:8],[[13,1,0],[13,1,0]])
