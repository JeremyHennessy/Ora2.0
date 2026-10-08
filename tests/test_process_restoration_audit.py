"""Authored measurement fixtures; no sampled CLOSURE-03 worlds."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from experiments.process_restoration_audit import CONTRACT, audit, audit_file

A, B, C = [2, 0, 3, 0], [0, 1, 1, 2], [0, 2, 0, 0]
P, T = [0, 1, 3, 1], [1, 2, 3, 0]


def fixture():
    return {"contract": CONTRACT, "law": "splice-v1", "target": T,
            "prerequisite": P, "precursor": 20, "fuel": 20,
            "initial_tokens": [{"id": k, "genome": v} for k, v in
                               (("a", A), ("b", B), ("c", C), ("old_p", P), ("old_t", T))],
            "events": [
                {"seq": 0, "kind": "damage", "removed_ids": ["old_p", "old_t"],
                 "state": {"live_ids": ["a", "b", "c"], "precursor": 20, "fuel": 20, "waste": 8}},
                {"seq": 1, "kind": "collision", "a": "a", "b": "b", "product": {"id": "p", "genome": P},
                 "state": {"live_ids": ["a", "b", "c", "p"], "precursor": 16, "fuel": 19, "waste": 8}},
                {"seq": 2, "kind": "collision", "a": "p", "b": "c", "product": {"id": "t", "genome": T},
                 "state": {"live_ids": ["a", "b", "c", "p", "t"], "precursor": 12, "fuel": 18, "waste": 8}}]}


class MeasurementGate(unittest.TestCase):
    def test_paid_constructive_payload_restoration(self):
        data = fixture()
        before = copy.deepcopy(data)
        result = audit(data)
        self.assertTrue(result["constructive_payload_restoration"])
        self.assertEqual(result["material_total"], 40)
        self.assertFalse(result["scientific_evidence"])
        self.assertEqual(data, before)

    def test_fixed_graph_is_separate_comparator(self):
        data = fixture()
        data["law"] = "fixed-graph-v1"
        data["rules"] = [{"a": A, "b": B, "product": P}, {"a": P, "b": C, "product": T}]
        result = audit(data)
        self.assertTrue(result["restored"])
        self.assertFalse(result["constructive_payload_restoration"])

    def test_passive_failure_and_inert_collision(self):
        data = fixture()
        data["events"] = data["events"][:1]
        self.assertFalse(audit(data)["restored"])
        data["events"].append({"seq": 1, "kind": "collision", "a": "a", "b": "c", "product": None,
                               "state": {"live_ids": ["a", "b", "c"], "precursor": 20, "fuel": 19, "waste": 8}})
        self.assertFalse(audit(data)["restored"])

    def test_external_ancestry_cannot_be_laundered(self):
        data = fixture()
        data["events"][1]["kind"] = "rescue"
        self.assertFalse(audit(data)["restored"])

    def test_malformed_receipts_fail(self):
        mutations = [
            lambda d: d["events"][1].update(a="old_p"),
            lambda d: d["events"][1]["product"].update(id="old_p"),
            lambda d: d["events"][1]["product"].update(genome=T),
            lambda d: d["events"][1]["state"].update(fuel=20),
            lambda d: d["events"][1]["state"].update(precursor=20),
            lambda d: d["events"][0].update(removed_ids=["old_p"]),
            lambda d: d["events"][1].update(seq=True),
            lambda d: d.update(fuel=True),
            lambda d: d["events"][2].update(a="c", b="c"),
            lambda d: d["events"][1]["state"].update(live_ids=["a", "b", "c"]),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                data = fixture()
                mutation(data)
                with self.assertRaises((ValueError, KeyError)):
                    audit(data)

    def test_restored_counts_without_rebuilt_parent_fail(self):
        data = fixture()
        data["initial_tokens"].append({"id": "alternate", "genome": P})
        # Remove all copies, then externally supply a parent: counts alone cannot pass.
        data["events"][0]["removed_ids"] = ["alternate", "old_p", "old_t"]
        for event in data["events"]:
            event["state"]["waste"] = 12
        data["events"].insert(2, {"seq": 2, "kind": "rescue", "product": {"id": "external", "genome": P},
                                  "state": {"live_ids": ["a", "b", "c", "external", "p"], "precursor": 12, "fuel": 18, "waste": 12}})
        data["events"][3].update(seq=3, a="external")
        data["events"][3]["state"].update(live_ids=["a", "b", "c", "external", "p", "t"], precursor=8, fuel=17)
        self.assertFalse(audit(data)["restored"])

    def test_unknown_law_is_indeterminate(self):
        data = fixture()
        data["law"] = "opaque"
        self.assertEqual(audit(data)["status"], "indeterminate")

    def test_clean_counts_without_required_causal_parent_fail(self):
        data = fixture()
        data["initial_tokens"].append({"id": "x", "genome": [0, 1, 3, 2]})
        for event in data["events"]:
            event["state"]["live_ids"].append("x")
        data["events"][2]["a"] = "x"
        self.assertFalse(audit(data)["restored"])

    def test_ineligible_receipt_stays_in_denominator(self):
        data = fixture()
        data["initial_tokens"] = data["initial_tokens"][:-1]
        data["events"][0]["removed_ids"] = ["old_p"]
        for event in data["events"]:
            event["state"]["waste"] = 4
        result = audit(data)
        self.assertFalse(result["eligible"])
        self.assertFalse(result["restored"])

    def test_digest_new_output_and_repeatability(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "input" / "fixture.json"
            source.parent.mkdir()
            source.write_text(json.dumps(fixture()), encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                audit_file(source, root / "bad", "0" * 64)
            with self.assertRaises(ValueError):
                audit_file(source, source.parent / "output", digest)
            audit_file(source, root / "one", digest)
            audit_file(source, root / "two", digest)
            self.assertEqual((root / "one" / "audit.json").read_bytes(), (root / "two" / "audit.json").read_bytes())
            with self.assertRaises(ValueError):
                audit_file(source, root / "one", digest)

    def test_bounds(self):
        for field, value in (("initial_tokens", [{"id": str(i), "genome": A} for i in range(65)]),
                             ("events", [{}] * 4097)):
            data = fixture()
            data[field] = value
            with self.assertRaises(ValueError):
                audit(data)
