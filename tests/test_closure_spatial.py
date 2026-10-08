"""CLOSURE-01-SPATIAL: physically explicit toy-world and control checks.

These tests use only development seed worlds (0-7), NOT held-out 6100-6135.
No result here may be described as living protocell evidence.
"""
from dataclasses import replace
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.closure_spatial import (
    SIDE, CELLS, ORIGINS, ARMS, NEIGH4, NEIGH8,
    Protocol, World, initialize, catalyst_hop_probability,
    checked, step, select_target, region, damage, run_world,
    summarize, study,
)


class GenesisAndLatticeTests(unittest.TestCase):
    def test_neighbor_graph_is_wrapped_and_lacks_self(self):
        self.assertEqual(SIDE, 9)
        self.assertEqual(CELLS, 81)
        self.assertEqual(len(NEIGH4), CELLS)
        self.assertEqual(len(NEIGH8), CELLS)
        for pos in range(CELLS):
            self.assertEqual(len(set(NEIGH4[pos])), 4)
            self.assertEqual(len(set(NEIGH8[pos])), 8)
            self.assertNotIn(pos, NEIGH4[pos])
            self.assertNotIn(pos, NEIGH8[pos])

    def test_three_initializations_equal_mass_without_prebuilt_shell(self):
        p = Protocol()
        for origin in ORIGINS:
            w = initialize(origin, random.Random(0), p)
            self.assertEqual(w.mass(), 4 * CELLS)
            self.assertEqual(w.inflow, 0)
            self.assertEqual(sum(w.m), 0)
            self.assertEqual(checked(w, 4 * CELLS), 0)
            if origin == "nutrient_only":
                self.assertEqual((sum(w.a), sum(w.r)), (0, 0))
            else:
                self.assertEqual((sum(w.a), sum(w.r)), (12, 12))
        seed = initialize("clustered", random.Random(0), p)
        self.assertEqual(seed.a[40], 12)
        self.assertEqual(seed.r[40], 12)
        self.assertEqual(seed.m[40], 0)

    def test_shell_is_functional_transport_parameter_not_a_protected_object(self):
        p = Protocol()
        self.assertEqual(catalyst_hop_probability(0, 0, p, shell_has_effect=True), .24)
        self.assertLess(catalyst_hop_probability(2, 3, p, shell_has_effect=True), .05)
        self.assertEqual(catalyst_hop_probability(2, 3, p, shell_has_effect=False), .24)

    def test_invalid_physics_parameters_rejected(self):
        with self.assertRaises(ValueError):
            Protocol(basal_p=2)
        with self.assertRaises(ValueError):
            Protocol(shell_impedance=-1)
        with self.assertRaises(ValueError):
            Protocol(required_ring_after=9)
        with self.assertRaises(ValueError):
            initialize("living creature", random.Random(0), Protocol())


class ReactionControls(unittest.TestCase):
    def test_mass_ledger_survives_diffusion_degradation_and_feed(self):
        p = Protocol()
        w = initialize("dispersed", random.Random(4), p)
        rng = random.Random(12)
        for _ in range(15):
            step(w, rng, p)
            self.assertEqual(checked(w, 4 * CELLS), 0)
        self.assertEqual(w.inflow, 8 * 15)
        self.assertEqual(w.mass(), 4 * CELLS + 8 * 15)
        self.assertEqual(w.reaction_events, w.synth_r + w.synth_a + w.synth_m)

    def test_deactivated_chemistry_does_not_rebuild_machinery(self):
        p = replace(
            Protocol(), basal_p=0, reaction_rate=0, added_s_per_step=0
        )
        w = initialize("clustered", random.Random(0), p)
        initial_a, initial_r = sum(w.a), sum(w.r)
        rng = random.Random(3)
        for _ in range(25):
            step(w, rng, p)
            self.assertEqual(checked(w, 4 * CELLS), 0)
        self.assertLessEqual(sum(w.a), initial_a)
        self.assertLessEqual(sum(w.r), initial_r)
        self.assertEqual(sum(w.m), 0)
        self.assertEqual(w.synth_m, 0)
        self.assertEqual(w.synth_r + w.synth_a, 0)

    def test_reaction_specific_ablations_do_not_fake_missing_synthesis(self):
        for arm, forbidden in [
            ("no_R_to_A", "synth_a"),
            ("no_A_to_R", "synth_r"),
            ("no_M_synthesis", "synth_m"),
        ]:
            p = Protocol()
            w = initialize("clustered", random.Random(0), p)
            rng = random.Random(2)
            for _ in range(25):
                step(w, rng, p, arm)
            self.assertEqual(getattr(w, forbidden), 0)
            self.assertEqual(w.mass(), 4 * CELLS + 25 * p.added_s_per_step)

    def test_resource_denial_consumes_existing_S_with_mass_conversion(self):
        p = Protocol()
        w = initialize("clustered", random.Random(2), p)
        center = select_target(w)
        before = region(w, center)
        removed = damage(w, center, p, "resource_denied")
        self.assertGreaterEqual(removed["s_denied"], 0)
        self.assertEqual(sum(w.s), 0)
        self.assertEqual(checked(w, 4 * CELLS), 0)
        rng = random.Random(2)
        for _ in range(10):
            step(w, rng, p, "resource_denied")
        self.assertEqual(sum(w.s), 0)
        self.assertEqual(w.inflow, 0)
        self.assertEqual(checked(w, 4 * CELLS), 0)

    def test_nonprivileged_damage_preserves_total_mass(self):
        p = Protocol()
        w = initialize("clustered", random.Random(3), p)
        target = select_target(w)
        before_mass = w.mass()
        damage(w, target, p, "intact")
        self.assertEqual(w.mass(), before_mass)
        self.assertEqual(checked(w, 4 * CELLS), 0)


class ForkAndEvaluationTests(unittest.TestCase):
    def test_complete_development_seed_replay_and_equal_interventions(self):
        first, traces = run_world(0, "clustered")
        second, second_traces = run_world(0, "clustered")
        self.assertEqual(first, second)
        self.assertEqual(traces, second_traces)
        self.assertEqual(len(first), len(ARMS))
        self.assertEqual(len(traces), len(ARMS) * 60)
        self.assertEqual([r["arm"] for r in first], list(ARMS))
        self.assertEqual(len({r["checkpoint_sha256"] for r in first}), 1)
        self.assertEqual(len({r["target"] for r in first}), 1)
        self.assertEqual(len({r["eligible"] for r in first}), 1)
        self.assertEqual(len({(
            r["post_damage_region"]["core_a"],
            r["post_damage_region"]["core_r"],
            r["post_damage_region"]["ring_coverage"]
        ) for r in first}), 1)
        for record in first:
            self.assertEqual(record["max_mass_residual"], 0)
            self.assertEqual(len(record["final_grid"]["m"]), CELLS)
        self.assertEqual(first[-1]["final_global_counts"]["s"], 0)

    def test_inevaluable_world_remains_in_denominator_without_fake_success(self):
        p = replace(Protocol(), min_pre_a=100000, min_pre_r=100000)
        records, _ = run_world(1, "nutrient_only", p)
        self.assertEqual(len(records), len(ARMS))
        self.assertTrue(all(r["dual_recovery"] is None for r in records))
        self.assertTrue(all(not r["eligible"] for r in records))

    def test_replayed_complete_smoke_archive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output1 = study(root, [0], revision="smoke")
            first_bytes = {f.name: f.read_bytes() for f in root.iterdir()}
            output2 = study(root, [0], revision="smoke")
            second_bytes = {f.name: f.read_bytes() for f in root.iterdir()}
            self.assertEqual(output1, output2)
            self.assertEqual(first_bytes, second_bytes)
            self.assertEqual(output1["world_record_count"], 3 * 6)
            self.assertEqual(output1["trace_event_count"], 3 * 6 * 60)
            self.assertEqual(len((root/"worlds.jsonl").read_text().splitlines()), 18)
            self.assertEqual(len((root/"traces.jsonl").read_text().splitlines()), 1080)
            self.assertEqual(json.loads((root/"summary.json").read_text())
                             ["source_revision"], "smoke")

    def test_summary_cannot_select_only_recovered_or_drop_controls(self):
        records = []
        for origin in ORIGINS:
            world_rows, _ = run_world(0, origin)
            records.extend(world_rows)
        out = summarize(records, [0])
        self.assertEqual(out["total_treatment_runs"], 18)
        with self.assertRaises(AssertionError):
            summarize(records[:-1], [0])
        with self.assertRaises(AssertionError):
            summarize(records + [records[0]], [0])

    def test_no_living_actor_object_or_host_execution_primitive(self):
        world = initialize("clustered", random.Random(0), Protocol())
        self.assertFalse(hasattr(world, "organisms"))
        self.assertFalse(hasattr(world, "genomes"))
        self.assertFalse(hasattr(world, "execute_shell"))


if __name__ == "__main__":
    unittest.main()
