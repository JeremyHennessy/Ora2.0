"""Independent structure, control, replay and analysis tests for AL01-RVCS."""
import json
from pathlib import Path
import tempfile
import unittest

from experiments.network_discovery import Protocol
from experiments.redundancy_probe import (
    VARIANTS, for_variant, network_manifest, run_study, run_world,
    select_structure, signature, summarize,
)


class SelectionTests(unittest.TestCase):
    def test_two_cyclic_incoming_routes_and_third_route_survives(self):
        # (0->2,2->0) and (1->2,2->1) give two different cycles.
        arcs = ((0, 2), (1, 2), (2, 0), (2, 1), (3, 2), (4, 5))
        structure = select_structure(arcs)
        self.assertTrue(structure["structurally_eligible"])
        self.assertEqual(structure["target"], 2)
        self.assertEqual(structure["target_in_degree"], 3)
        self.assertEqual(structure["cut_edges"], ((0, 2), (1, 2)))
        self.assertEqual(len(structure["sham_edges"]), 2)
        graph = {"arcs": arcs, **structure}
        both = for_variant("cut_both", graph)
        self.assertNotIn((0, 2), both)
        self.assertNotIn((1, 2), both)
        self.assertIn((3, 2), both)
        self.assertEqual(len(for_variant("sham_two", graph)), len(arcs)-2)
        self.assertEqual(len(for_variant("cut_first", graph)), len(arcs)-1)
        self.assertEqual(len(for_variant("cut_second", graph)), len(arcs)-1)
        self.assertEqual(len(for_variant("intact", graph)), len(arcs))

    def test_empty_network_remains_noneligible_not_false_positive(self):
        structure = select_structure(())
        self.assertFalse(structure["structurally_eligible"])
        self.assertIsNone(structure["target"])
        graph = {"arcs": (), **structure}
        for variant in VARIANTS:
            self.assertEqual(for_variant(variant, graph), ())

    def test_topology_choice_uses_only_graph_and_is_reproducible(self):
        a = network_manifest(9000)
        self.assertEqual(a, network_manifest(9000))
        self.assertEqual(tuple(a["arcs"]), tuple(sorted(a["arcs"])))
        if a["structurally_eligible"]:
            self.assertGreaterEqual(a["target_in_degree"], 3)
            self.assertEqual(len(a["cut_edges"]), 2)
            self.assertEqual(len(a["sham_edges"]), 2)
            self.assertEqual(len(set(tuple(x) for x in a["cut_edges"])), 2)


class CausalStudyTests(unittest.TestCase):
    def test_same_counterfactual_checkpoint_and_damage(self):
        records, traces = run_world(0, 0)
        records2, traces2 = run_world(0, 0)
        self.assertEqual(records, records2)
        self.assertEqual(traces, traces2)
        self.assertEqual(len(records), len(VARIANTS))
        self.assertEqual(len(traces), len(VARIANTS)*Protocol().followup_steps)
        self.assertEqual(len({r["checkpoint_sha256"] for r in records}), 1)
        for r in records:
            self.assertEqual(r["pre_damage"], records[0]["pre_damage"])
            self.assertEqual(r["post_damage"]["x"], records[0]["post_damage"]["x"])
            self.assertEqual(r["damage_amounts"], records[0]["damage_amounts"])
            self.assertEqual(r["max_abs_mass_residual"], 0)
        self.assertEqual(records[-1]["post_damage"]["s"], 0)
        self.assertTrue(all(t["mass_residual"] == 0 for t in traces))

    def test_no_candidate_yields_nullable_recovery_and_no_signature(self):
        from dataclasses import replace
        p = replace(Protocol(), edge_probability=0.0)
        records, _ = run_world(0, 0, p)
        self.assertTrue(all(not r["eligible"] for r in records))
        self.assertTrue(all(r["sustained_recovery"] is None for r in records))
        self.assertTrue(all(r["cut_noop_due_to_no_structure"] for r in records[1:5]))
        self.assertFalse(signature({r["variant"]: r for r in records}))
        s = summarize(records, [0], 1)
        self.assertEqual(s["sampled_networks"], 1)
        self.assertEqual(s["structurally_eligible_networks"], 0)
        self.assertEqual(s["signature_trajectories"], 0)

    def test_signature_requires_all_controls_not_just_two_cuts(self):
        records, _ = run_world(0, 0)
        by = {r["variant"]: dict(r) for r in records}
        for r in by.values():
            r["eligible"] = True
            r["sustained_recovery"] = False
        for v in ("intact", "cut_first", "cut_second", "sham_two"):
            by[v]["sustained_recovery"] = True
        self.assertTrue(signature(by))
        by["sham_two"]["sustained_recovery"] = False
        self.assertFalse(signature(by))
        by["sham_two"]["sustained_recovery"] = True
        by["cut_both"]["sustained_recovery"] = True
        self.assertFalse(signature(by))

    def test_denominator_exactness_and_hash_replay(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            a = run_study(out, [0, 1], 2, revision="example-sha")
            first = {x.name: x.read_bytes() for x in out.iterdir()}
            b = run_study(out, [0, 1], 2, revision="example-sha")
            second = {x.name: x.read_bytes() for x in out.iterdir()}
            self.assertEqual(a, b)
            self.assertEqual(first, second)
            self.assertEqual(a["sampled_networks"], 2)
            self.assertEqual(a["treatment_runs"], 28)
            self.assertEqual(a["trace_events"], 2*2*7*55)
            self.assertEqual(a["max_mass_residual"], 0)
            self.assertEqual(len((out/"network-manifest.jsonl").read_text().splitlines()), 2)
            self.assertEqual(len((out/"run-records.jsonl").read_text().splitlines()), 28)
            self.assertEqual(len((out/"run-traces.jsonl").read_text().splitlines()), a["trace_events"])
            self.assertEqual(json.loads((out/"summary.json").read_text())["revision"], "example-sha")

    def test_summary_rejects_incomplete_treatments(self):
        records, _ = run_world(0, 0)
        with self.assertRaises(ValueError):
            summarize(records[:-1], [0], 1)
        with self.assertRaises(ValueError):
            summarize(records + [records[0]], [0], 1)


if __name__ == "__main__":
    unittest.main()
