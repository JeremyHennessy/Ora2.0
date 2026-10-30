"""Arithmetic boundary checks; no controller/World/old outcome execution."""
import unittest
from funding_bound import upper


class FundingBound(unittest.TestCase):
    def test_atomic_reward_at_last_unit(self):
        self.assertEqual(upper(((1, 22),), energy=1), 1)

    def test_copy_at_horizon_and_parent_zero(self):
        self.assertEqual(upper((), energy=44), 2)

    def test_no_future_food_or_resurrection(self):
        self.assertEqual(upper(((2, 100),), energy=1), 0)
        self.assertEqual(upper(((1, 0), (1, 100)), energy=1), 0)

    def test_placement_is_optimistic(self):
        self.assertEqual(upper(((1, 8),), energy=22), 1)
        self.assertEqual(upper(((1, 8),)*5, energy=8), 1)


if __name__ == '__main__':
    unittest.main()
