import unittest
from experiments.digital_experience_provenance17 import two_distinct_own_outcomes as endpoint

def sample(tick,source_tick,actor=0,source_actor=0,value=1):
    return dict(actor=actor,tick=tick,value=value,source=dict(actor=source_actor,
                tick=source_tick,packet=16,outcome=value))

class PersonalOutcomeFixtures(unittest.TestCase):
    def test_same_endpoint_distinct_equal_values_and_duplicate(self):
        self.assertTrue(endpoint([sample(5,4),sample(8,7)]))
        self.assertFalse(endpoint([sample(5,4),sample(8,4)]))
    def test_initial_and_donated_are_not_two_own_outcomes(self):
        self.assertFalse(endpoint([dict(actor=0,tick=1,value=0,source=None),sample(5,4)]))
        self.assertFalse(endpoint([sample(5,4),sample(8,7,source_actor=1)]))
    def test_typed_identity_and_causal_order(self):
        self.assertFalse(endpoint([sample(5,4),sample(8,True)]))
        self.assertFalse(endpoint([sample(5,4),sample(8,8)]))
