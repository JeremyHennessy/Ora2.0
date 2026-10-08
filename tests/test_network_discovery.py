"""AL01-DISCOVERY simulation invariants and independent negative controls."""
from dataclasses import replace
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.network_discovery import (
    ALL_ARCS, N, VARIANTS, Protocol, State, assert_mass, damage,
    graph_manifest, path_exists, run_world, sample_graph, step,
    summarize, variant_arcs, write_results,
)


class GraphTests(unittest.TestCase):
    def test_graph_generation_exact_replay_and_no_self_arc(self):
        a = sample_graph(7000, Protocol())
        b = sample_graph(7000, Protocol())
        self.assertEqual(a, b)
        self.assertTrue(all(i != j for i, j in a))
        self.assertEqual(a, tuple(sorted(a)))
        self.assertEqual(len(ALL_ARCS), 30)

    def test_cycle_edge_detection_and_no_false_positive(self):
        edges = ((0, 1), (1, 2), (2, 0), (3, 4))
        self.assertTrue(path_exists(1, 0, edges))
        self.assertFalse(path_exists(4, 3, edges))
        self.assertFalse(path_exists(2, 0, ((0, 1), (1, 2))))
        # A graph with no cycle does not invent an intervention.
        empty = graph_manifest(4, replace(Protocol(), edge_probability=0.0))
        self.assertEqual(empty["arcs"], ())
        self.assertIsNone(empty["cycle_edge"])
        self.assertIsNone(empty["target"])
        self.assertEqual(variant_arcs("cycle_edge_removed", empty), ())

    def test_rewire_preserves_edge_count_and_removes_self_loops(self):
        graph = graph_manifest(7022, Protocol())
        self.assertEqual(len(graph["arcs"]), len(graph["rewired_arcs"]))
        self.assertTrue(all(i != j for i, j in graph["rewired_arcs"]))
        self.assertEqual(graph, graph_manifest(7022, Protocol()))


class ChemistryTests(unittest.TestCase):
    def test_no_ex_nihilo_creation_except_inflow(self):
        p = Protocol()
        s = State(30, [0] * N)
        rng = random.Random(3)
        for _ in range(100):
            step(s, rng, ((0, 1), (1, 2)), p, fed=True, starting_mass=30)
            self.assertEqual(assert_mass(s, 30), 0)
        self.assertEqual(s.mass(), 30 + 100 * p.supply_per_step)
        self.assertEqual(s.inflow, 500)

    def test_no_food_means_no_growth_or_repair(self):
        p = Protocol()
        state = State(30, [8] * N)
        total = state.mass()
        damage(state, p, deny_resource=True)
        self.assertEqual(state.s, 0)
        before = state.x.copy()
        for _ in range(55):
            step(state, random.Random(12), ALL_ARCS, p, fed=False, starting_mass=total)
        self.assertTrue(all(a <= b for a, b in zip(state.x, before)))
        self.assertEqual((state.catalytic_events, state.basal_events, state.inflow), (0, 0, 0))

    def test_no_graph_no_catalytic_events(self):
        p = replace(Protocol(), basal_probability=0.0)
        state = State(30, [10] * N)
        mass = state.mass()
        step(state, random.Random(2), (), p, fed=True, starting_mass=mass)
        self.assertEqual(state.catalytic_events, 0)
        self.assertEqual(state.basal_events, 0)

    def test_damage_is_only_molecule_conversion(self):
        p = Protocol()
        state = State(30, [10] * N)
        before_mass = state.mass()
        removed = damage(state, p, deny_resource=False)
        self.assertEqual(removed, [6] * N)
        self.assertEqual(state.x, [4] * N)
        self.assertEqual(state.w, 36)
        self.assertEqual(assert_mass(state, before_mass), 0)


class ReproducibilityTests(unittest.TestCase):
    def test_forked_state_rng_and_integrity(self):
        records, traces = run_world(2, 1)
        same_records, same_traces = run_world(2, 1)
        self.assertEqual(records, same_records)
        self.assertEqual(traces, same_traces)
        self.assertEqual(len(records), len(VARIANTS))
        self.assertEqual(len(traces), len(VARIANTS) * Protocol().followup_steps)
        self.assertEqual({r["checkpoint_sha256"] for r in records},
                         {records[0]["checkpoint_sha256"]})
        for r in records:
            self.assertEqual(r["pre_damage"], records[0]["pre_damage"])
            self.assertEqual(r["post_damage"]["x"], records[0]["post_damage"]["x"])
            self.assertEqual(r["damage_amounts"], records[0]["damage_amounts"])
            self.assertEqual(r["max_abs_mass_residual"], 0)
        self.assertEqual(records[-1]["post_damage"]["s"], 0)
        self.assertEqual(records[4]["final"]["catalytic_events"],
                         records[4]["post_damage"]["catalytic_events"])
        self.assertTrue(all(t["residual"] == 0 for t in traces))

    def test_zero_graphs_are_recorded_as_inevaluable(self):
        params = replace(Protocol(), edge_probability=0.0)
        r, _ = run_world(3, 0, params)
        self.assertTrue(all(not x["eligible"] for x in r))
        self.assertTrue(all(x["sustained_recovery"] is None for x in r))
        self.assertTrue(r[1]["intervention_no_op"])
        s = summarize(r, [3], 1)
        self.assertEqual(s["networks_without_cycle"], 1)
        self.assertEqual(s["eligible_trajectories"], 0)
        self.assertIsNone(s["paired_intact_minus_cycle_edge_removed"])
        self.assertIsNone(s["paired_network_cluster_bootstrap_95"])

    def test_summary_rejects_missing_or_duplicate_records(self):
        records, _ = run_world(2, 0)
        with self.assertRaises(ValueError):
            summarize(records[:-1], [2], 1)
        with self.assertRaises(ValueError):
            summarize(records + [records[0]], [2], 1)

    def test_output_is_byte_replayable_and_full_denominator(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = Protocol()
            x = write_results(root, [0, 1], 2, p, "frozen-revision")
            first = {path.name: path.read_bytes() for path in root.iterdir()}
            y = write_results(root, [0, 1], 2, p, "frozen-revision")
            second = {path.name: path.read_bytes() for path in root.iterdir()}
            self.assertEqual(x, y)
            self.assertEqual(first, second)
            self.assertEqual(x["total_sampled_networks"], 2)
            self.assertEqual(x["total_treatment_runs"], 24)
            self.assertEqual(x["trace_events"], 2 * 2 * 6 * 55)
            self.assertEqual(x["max_abs_mass_residual"], 0)
            self.assertEqual(len((root / "network-manifest.jsonl").read_text().splitlines()), 2)
            self.assertEqual(len((root / "run-records.jsonl").read_text().splitlines()), 24)
            self.assertEqual(len((root / "run-traces.jsonl").read_text().splitlines()), x["trace_events"])
            self.assertEqual(json.loads((root / "summary.json").read_text())["source_revision"],
                             "frozen-revision")


if __name__ == "__main__":
    unittest.main()
