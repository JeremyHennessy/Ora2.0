"""AL03-MAINT: strict regression, debit and resource-conservation controls."""
from pathlib import Path
import json
import tempfile
import unittest

from experiments.niche_selection import Ecology, Protocol
from experiments.maintenance_stress import (
    ARMS, MAINT_INTERVAL, MaintenanceEcology,
    execute_study, summarize,
)


class ExactBaselineTests(unittest.TestCase):
    def test_zero_upkeep_arm_is_byte_identical_to_approved_al03(self):
        seed = 3
        original = Ecology(seed, "heritable")
        control = MaintenanceEcology(seed, "baseline")
        a, original_events, original_traces = original.run()
        b, control_events, control_traces = control.run()
        self.assertEqual(a, b)
        self.assertEqual(original_events, control_events)
        self.assertEqual(original_traces, control_traces)

    def test_upkeep_schedule_and_world_generation_are_not_auto_advanced(self):
        for arm in ARMS:
            w = MaintenanceEcology(0, arm)
            self.assertEqual(w.tick, 0)
            self.assertEqual(len(w.alive), 1)
            self.assertEqual(w.p.material_slots, 40)
            self.assertEqual(w.interval, MAINT_INTERVAL[arm])

    def test_unknown_arm_is_rejected(self):
        with self.assertRaises(ValueError):
            MaintenanceEcology(1, "survive_forever")


class MaintenancePhysicsTests(unittest.TestCase):
    def test_costs_apply_to_idle_and_newborn_entities(self):
        w = MaintenanceEcology(0, "upkeep_8")
        for _ in range(8):
            w.step()
        charged = [e for e in w.events if e["kind"] == "UPKEEP"]
        self.assertTrue(charged)
        self.assertEqual(len(charged), w.upkeep_paid)
        # Multiple participants can be charged on the same tick.
        self.assertGreaterEqual(len(charged), 2)
        self.assertTrue(all(e["tick"] == 8 and
                            e["energy_before"] - e["energy_after"] == 1
                            and e["paid_energy"] == 1 for e in charged))
        self.assertEqual(w.assert_conservation(), (0, 0))
        self.assertEqual(w.traces[-1]["population"], len(w.alive))

    def test_original_world_has_no_upkeep_events(self):
        w = MaintenanceEcology(1, "baseline")
        out, events, _ = w.run_maintenance()
        self.assertEqual(out["paid_upkeep_units"], 0)
        self.assertEqual(out["upkeep_caused_deaths"], 0)
        self.assertFalse(any(e["kind"] == "UPKEEP" for e in events))

    def test_each_charge_is_matched_by_heat_and_recomputed_trace(self):
        w = MaintenanceEcology(4, "upkeep_4")
        for _ in range(40):
            if not w.alive:
                break
            w.step()
            t = w.traces[-1]
            self.assertEqual(t["heat"], w.heat)
            self.assertEqual(t["population"], len(w.alive))
            self.assertEqual(t["mass_residual"], 0)
            self.assertEqual(t["energy_residual"], 0)
        self.assertEqual(w.upkeep_paid, sum(
            1 for e in w.events if e["kind"] == "UPKEEP"
        ))

    def test_no_feed_world_cannot_acquire_food(self):
        w = MaintenanceEcology(2, "upkeep_8_no_inflow")
        result, _, traces = w.run_maintenance()
        self.assertEqual(w.supplied_a, 0)
        self.assertEqual(result["supplied_a"], 0)
        self.assertTrue(all(t["supplied_a"] == 0 for t in traces))
        self.assertEqual(result["max_mass_residual"], 0)

    def test_ordinary_and_upkeep_death_release_body_slots(self):
        w = MaintenanceEcology(4, "upkeep_1")
        out, _, _ = w.run_maintenance()
        self.assertEqual(w.assert_conservation(), (0, 0))
        self.assertEqual(w.occupied_slots,
                         {e.slot: e.id for e in w.alive.values()})
        self.assertLessEqual(len(w.occupied_slots), w.p.material_slots)
        self.assertEqual(out["upkeep_caused_deaths"], w.upkeep_deaths)

    def test_debit_is_never_negative(self):
        for arm in ARMS:
            w = MaintenanceEcology(4, arm)
            out, events, traces = w.run_maintenance()
            self.assertTrue(all(e["energy_after"] >= 0 for e in events
                                if e["kind"] == "UPKEEP"))
            self.assertEqual(out["max_energy_residual"], 0)
            self.assertEqual(len(traces), out["steps"])


class OutputTests(unittest.TestCase):
    def test_complete_smoke_run_and_byte_replay(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = execute_study(root, [0, 1], revision="test-revision")
            stored = {p.name: p.read_bytes() for p in root.iterdir()}
            b = execute_study(root, [0, 1], revision="test-revision")
            self.assertEqual(a, b)
            self.assertEqual(stored, {p.name: p.read_bytes() for p in root.iterdir()})
            self.assertEqual(a["total_worlds"], 10)
            self.assertEqual(a["world_rows"], 10)
            self.assertEqual(len((root / "worlds.jsonl").read_text().splitlines()), 10)
            self.assertEqual(json.loads((root / "summary.json").read_text())
                             ["source_revision"], "test-revision")
            self.assertTrue(all(a["conditions"][arm]["maximum_energy_residual"] == 0
                                for arm in ARMS))

    def test_missing_or_duplicate_conditions_cannot_pass(self):
        p = Protocol()
        records = []
        for arm in ARMS:
            w = MaintenanceEcology(0, arm)
            r, _, _ = w.run_maintenance()
            records.append(r)
        s = summarize(records, [0], p)
        self.assertEqual(s["total_worlds"], len(ARMS))
        with self.assertRaises(AssertionError):
            summarize(records[:-1], [0], p)
        with self.assertRaises(AssertionError):
            summarize(records + [records[0]], [0], p)


if __name__ == "__main__":
    unittest.main()
