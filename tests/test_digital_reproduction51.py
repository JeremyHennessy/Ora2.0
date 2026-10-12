import unittest
from experiments.digital_reproduction51 import gate,PROGRAM

class AdmissionGate(unittest.TestCase):
    def row(self,**changes):
        return dict(dict(seed=51000,mode='faithful',births=2,descendant_food=1,
                         resource_then_birth=1,paid_copy_words=36,first_birth_tick=35),**changes)
    def test_paid_descendant_route(self):self.assertTrue(gate(self.row()))
    def test_first_birth_is_insufficient(self):self.assertFalse(gate(self.row(births=1,resource_then_birth=0)))
    def test_descendant_birth_needs_own_prior_resource(self):self.assertFalse(gate(self.row(resource_then_birth=0)))
    def test_descendant_food_alone_is_insufficient(self):self.assertFalse(gate(self.row(births=1)))
    def test_wrong_orientation_timing(self):self.assertFalse(gate(self.row(seed=51001)))
    def test_other_orientation(self):self.assertTrue(gate(self.row(seed=51001,first_birth_tick=40)))
    def test_boolean_count_refused(self):self.assertFalse(gate(self.row(descendant_food=True)))
    def test_disabled_copy_cannot_have_paid_writes(self):
        self.assertTrue(gate(self.row(mode='copy_disabled',births=0,paid_copy_words=0,first_birth_tick=0)))
        self.assertFalse(gate(self.row(mode='copy_disabled',births=0,paid_copy_words=3,first_birth_tick=0)))
    def test_no_installed_feedback_updating_policy(self):
        self.assertEqual([p[0] for p in PROGRAM],[4,6,5,10,12,7])
