"""AL01-CAL: invariants, intervention controls and exact replay tests."""
from dataclasses import replace
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.chemical_calibration import (
    Protocol, Reactor, VARIANTS, analyze, assert_valid, damage,
    passes_recovery, run_world, tick, write_results,
)


class ProtocolAndMassTests(unittest.TestCase):
    def test_invalid_probability(self):
        with self.assertRaises(ValueError):
            Protocol(decay_probability=1.1)

    def test_nutrient_is_accounted_for(self):
        state = Reactor(35, 10, 10)
        initial_mass = state.mass
        rng = random.Random(8)
        for _ in range(70):
            tick(state, rng, Protocol(), "intact", initial_mass)
            self.assertEqual(assert_valid(state, initial_mass), 0)
            self.assertEqual(state.mass, initial_mass + state.cumulative_supply)
        self.assertEqual(state.cumulative_supply, 4 * 70)

    def test_damage_is_mass_conserving_and_does_not_respawn(self):
        state = Reactor(35, 20, 20)
        initial_mass = state.mass
        removed = damage(state, Protocol())
        self.assertEqual(removed, {"a_removed": 15, "b_removed": 7})
        self.assertEqual((state.a, state.b, state.w), (5, 13, 22))
        self.assertEqual(assert_valid(state, initial_mass), 0)

    def test_knockout_cannot_regenerate_a(self):
        rng = random.Random(17)
        state = Reactor(35, 15, 10)
        initial_a, mass = state.a, state.mass
        for _ in range(60):
            tick(state, rng, Protocol(), "feedback-knockout", mass)
            self.assertLessEqual(state.a, initial_a)
        self.assertEqual(state.conversions_b_to_a, 0)

    def test_starvation_denies_catalytic_reactions(self):
        state = Reactor(35, 20, 20)
        mass = state.mass
        damage(state, Protocol(), starve=True)
        self.assertEqual(state.s, 0)
        rng = random.Random(1)
        for _ in range(60):
            tick(state, rng, Protocol(), "starved", mass)
        self.assertEqual((state.conversions_b_to_a, state.conversions_a_to_b), (0, 0))
        self.assertEqual(state.cumulative_supply, 0)

    def test_recovery_threshold_and_no_zero_denominator(self):
        self.assertFalse(passes_recovery(20, 12, 14, 10, .75))
        self.assertTrue(passes_recovery(20, 12, 15, 9, .75))
        self.assertFalse(passes_recovery(0, 0, 0, 0, .75))


class ExperimentTests(unittest.TestCase):
    def test_deterministic_replay_and_forked_state(self):
        records, traces = run_world(5)
        replay_records, replay_traces = run_world(5)
        self.assertEqual(records, replay_records)
        self.assertEqual(traces, replay_traces)
        self.assertEqual([r["variant"] for r in records], list(VARIANTS))
        self.assertEqual(len({r["pristine_checkpoint_sha256"] for r in records}), 1)
        self.assertEqual(len(traces), 4 * Protocol().observation_steps)
        for record in records:
            self.assertEqual(record["pre_damage"], records[0]["pre_damage"])
            self.assertEqual(record["post_intervention"]["a"], records[0]["post_intervention"]["a"])
            self.assertEqual(record["post_intervention"]["b"], records[0]["post_intervention"]["b"])
            self.assertEqual(record["max_abs_ledger_residual"], 0)
        self.assertEqual(records[3]["post_intervention"]["s"], 0)
        self.assertEqual(records[2]["post_conversions_a_to_b"], 0)
        self.assertEqual(records[2]["post_conversions_b_to_a"], 0)

    def test_zero_initial_constituents_remain_in_denominator(self):
        params = replace(Protocol(), initial_a=0, initial_b=0)
        records, _ = run_world(4, params)
        summary = analyze(records, [4])
        self.assertEqual(summary["pre_damage_zero_constituent_worlds"], 1)
        self.assertTrue(all(not r["sustained_recovery"] for r in records))

    def test_analysis_rejects_duplicates(self):
        records, _ = run_world(2)
        with self.assertRaises(ValueError):
            analyze(records + [records[0]], [2])

    def test_full_artifact_output_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            a = write_results(target, [0, 1], Protocol(), "test-source")
            files_a = {f.name: f.read_bytes() for f in target.iterdir()}
            b = write_results(target, [0, 1], Protocol(), "test-source")
            files_b = {f.name: f.read_bytes() for f in target.iterdir()}
            self.assertEqual(a, b)
            self.assertEqual(files_a, files_b)
            self.assertEqual(len((target / "run-records.jsonl").read_text().splitlines()), 8)
            self.assertEqual(len((target / "run-traces.jsonl").read_text().splitlines()), 480)
            self.assertEqual(json.loads((target / "summary.json").read_text())["max_mass_conservation_residual"], 0)


if __name__ == "__main__":
    unittest.main()
