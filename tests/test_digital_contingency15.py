import unittest
from experiments.digital_contingency15_endpoint import endpoint
class ContingencyFixtures(unittest.TestCase):
    def test_same_endpoint_prepared_positive_and_missing_opportunity(self):
        row=dict(verified=True,post_food=12,fresh_attempts=16,ticks=300)
        self.assertTrue(endpoint(row,12))
        self.assertFalse(endpoint(dict(row,fresh_attempts=15),12))
        self.assertFalse(endpoint(dict(row,ticks=271),12))
        self.assertFalse(endpoint(dict(row,post_food=11),12))
    def test_aliased_boolean_counts_are_not_measurements(self):
        row=dict(verified=True,post_food=True,fresh_attempts=16,ticks=300)
        self.assertFalse(endpoint(row,1))
        self.assertFalse(endpoint(dict(row,post_food=12),True))
