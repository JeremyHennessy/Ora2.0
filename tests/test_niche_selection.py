"""Independent AL03 ecology checks: resource ledgers, negative controls and replay."""
import json
from pathlib import Path
import tempfile
import unittest

from experiments.niche_selection import Ecology, Protocol, VARIANTS, Entity, C, P, establish_downstream_lineage, analyze, write_study


class PhysicalTests(unittest.TestCase):
    def test_producer_output_and_sink_energy(self):
        a, b = Ecology(2, "heritable"), Ecology(2, "byproduct_sink")
        a.step()
        b.step()
        self.assertEqual((a.a, a.b, a.w), (17, 1, 0))
        self.assertEqual((b.a, b.b, b.w), (17, 0, 1))
        self.assertEqual(b.heat-a.heat, 8)
        self.assertEqual(a.assert_conservation(), (0, 0))
        self.assertEqual(b.assert_conservation(), (0, 0))

    def test_external_supply_and_no_inflow(self):
        fed = Ecology(2, "heritable")
        for _ in range(12):
            fed.step()
            self.assertEqual(fed.assert_conservation(), (0, 0))
        self.assertEqual(fed.supplied_a, 4)
        starved = Ecology(2, "no_inflow")
        result, _, _ = starved.run()
        self.assertEqual(result["supplied_a"], 0)
        self.assertEqual(result["max_energy_residual"], 0)

    def test_resource_corruption_and_duplicate_body_rejected(self):
        w = Ecology(2, "heritable")
        w.a += 1
        with self.assertRaises(AssertionError):
            w.assert_conservation()
        w = Ecology(2, "heritable")
        w.free_slots.add(0)
        with self.assertRaises(AssertionError):
            w.assert_conservation()

    def test_mutations_disabled_and_sink_cannot_establish_consumers(self):
        for variant in ("mutation_disabled", "byproduct_sink"):
            summary, _, _ = Ecology(4, variant).run()
            self.assertFalse(summary["established_downstream_lineage"])
            self.assertEqual(summary["max_mass_residual"], 0)
            self.assertEqual(summary["max_energy_residual"], 0)

    def test_invalid_probabilities_and_roles(self):
        with self.assertRaises(ValueError):
            Protocol(mutation_probability=1.4)
        with self.assertRaises(ValueError):
            Protocol(producer_energy=13)
        with self.assertRaises(ValueError):
            Ecology(-1, "heritable")
        with self.assertRaises(ValueError):
            Ecology(0, "not-an-arm")


class LineageTests(unittest.TestCase):
    def test_complete_three_event_criterion(self):
        births = [{"parent_role": C, "child_role": C,
                   "parent_fed_b_before_birth": True,
                   "child_lineage_has_p_to_c_switch": True,
                   "child_id": 3}]
        entities = {3: Entity(3, C, 8, 3, 2, 2, 8, True, fed_b=1)}
        self.assertTrue(establish_downstream_lineage(births, entities))
        for item in ("parent_fed_b_before_birth", "child_lineage_has_p_to_c_switch"):
            altered = [dict(births[0], **{item: False})]
            self.assertFalse(establish_downstream_lineage(altered, entities))
        entities[3].fed_b = 0
        self.assertFalse(establish_downstream_lineage(births, entities))

    def test_full_dev_world_byte_replay(self):
        a, b = Ecology(3, "heritable"), Ecology(3, "heritable")
        self.assertEqual(a.run(), b.run())
        self.assertEqual(a.max_energy_residual, 0)
        self.assertEqual(a.max_mass_residual, 0)

    def test_every_variant_emits_ordered_records_and_keeps_failures(self):
        for v in VARIANTS:
            world = Ecology(3, v)
            result, events, traces = world.run()
            self.assertEqual(len(traces), result["steps"])
            self.assertEqual([e["event_id"] for e in events], list(range(len(events))))
            self.assertTrue(all(t["mass_residual"] == 0 and
                                t["energy_residual"] == 0 for t in traces))


class OutputTests(unittest.TestCase):
    def test_fixed_small_sample_byte_for_byte_and_full_denominator(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = write_study(root, [0, 1], revision="test")
            first = {p.name: p.read_bytes() for p in root.iterdir()}
            b = write_study(root, [0, 1], revision="test")
            self.assertEqual(a, b)
            self.assertEqual(first, {p.name: p.read_bytes() for p in root.iterdir()})
            self.assertEqual(a["treatment_worlds"], 2 * len(VARIANTS))
            self.assertEqual(len((root/"worlds.jsonl").read_text().splitlines()), 10)
            self.assertEqual(json.loads((root/"summary.json").read_text())["revision"], "test")

    def test_omitted_or_duplicate_worlds_are_rejected(self):
        rows = [Ecology(0, v).run()[0] for v in VARIANTS]
        self.assertEqual(analyze(rows, [0])["treatment_worlds"], len(VARIANTS))
        with self.assertRaises(AssertionError):
            analyze(rows[:-1], [0])
        with self.assertRaises(AssertionError):
            analyze(rows+[rows[0]], [0])


if __name__ == "__main__":
    unittest.main()
