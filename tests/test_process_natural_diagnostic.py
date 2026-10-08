"""Read-only exploratory census validated against designed ledger fixtures."""
import copy
import unittest
from experiments.process_natural_diagnostic import census


class CensusTests(unittest.TestCase):
    def test_removal_of_parent_eliminates_potential_production(self):
        # A/B produces P; damage eliminates A (which is also the frozen T).
        a, b, p = [2, 0, 3, 0], [0, 1, 1, 2], [0, 1, 3, 1]
        state = {"live_ids": ["b"], "precursor": 4, "fuel": 2, "waste": 8}
        branch = {"receipt": {"initial_tokens": [{"id": "a", "genome": a}, {"id": "b", "genome": b}, {"id": "p", "genome": p}],
                              "prerequisite": p, "precursor": 4, "fuel": 2,
                              "events": [{"kind": "damage", "removed_ids": ["a", "p"], "seq": 0, "state": state}]},
                  "ticks": [{"tick": 32, "event_start": 1, "event_end": 1}]}
        before = copy.deepcopy(branch)
        result = census(branch)
        self.assertGreater(result["pre_damage_P_pairs"], 0)
        self.assertEqual(result["post_damage_P_pairs"], 0)
        self.assertEqual(result["funded_opportunity_ticks"], 0)
        self.assertEqual(branch, before)

    def test_starvation_is_distinct_from_missing_pair(self):
        a, b, p = [2, 0, 3, 0], [0, 1, 1, 2], [0, 1, 3, 1]
        branch = {"receipt": {"initial_tokens": [{"id": "a", "genome": a}, {"id": "b", "genome": b}],
                              "prerequisite": p, "precursor": 0, "fuel": 1,
                              "events": [{"kind": "damage", "removed_ids": [], "seq": 0,
                                          "state": {"live_ids": ["a", "b"], "precursor": 0, "fuel": 1, "waste": 0}}]},
                  "ticks": [{"tick": 32, "event_start": 1, "event_end": 1}]}
        result = census(branch)
        self.assertEqual(result["opportunity_ticks"], 1)
        self.assertEqual(result["funded_opportunity_ticks"], 0)
        self.assertEqual(result["starved_opportunity_ticks"], 1)
        self.assertEqual(result["first_starved_tick"], 32)
