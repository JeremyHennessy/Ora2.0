"""Natural development validation and separately labeled authored control fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.process_natural import simulate, run_world, run_study
from experiments.process_natural_audit import verify_world, audit_study


def encoded(data):
    return json.loads(json.dumps(data))


class NaturalTests(unittest.TestCase):
    def test_all_fresh_development_histories_independently_verify(self):
        for seed in range(32, 48):
            for regime in (128, 0):
                data = encoded(run_world(seed, regime))
                before = json.dumps(data, sort_keys=True)
                rows = verify_world(data)
                self.assertEqual(len(rows), len(data["branches"]))
                self.assertEqual(json.dumps(data, sort_keys=True), before)

    def test_resource_absence_cannot_trigger_paid_birth_or_counterfactual(self):
        for seed in range(32, 48):
            data = run_world(seed, 0)
            self.assertEqual(len(data["branches"]), 1)
            self.assertEqual(data["branches"][0]["P_births"], 0)
            self.assertFalse(data["branches"][0]["primary"])

    def test_old_reserved_and_boolean_seeds_rejected(self):
        for seed in (True, 0, 16, 8000, 8063, 48):
            with self.assertRaises(ValueError):
                simulate(seed, 128)

    def test_authored_trigger_fixture_removes_only_once_with_equal_costs(self):
        # Explicit software fixture; no archive or scientific sample is created.
        a, b, c, p, t, d = ((2, 0, 3, 0), (0, 1, 1, 2), (0, 2, 0, 0),
                            (0, 1, 3, 1), (1, 2, 3, 0), (0, 2, 0, 1))
        initial = [{"id": f"g{i}", "genome": list(g)} for i, g in enumerate((a, b, c, p, t, d))]
        draws = [[0.0, 0.3, 0.9] for _ in range(160)]
        draws[32] = [0.0, 0.0, 0.9]
        draws[33] = [0.9, 0.6, 0.9]
        engine_setup = (initial, p, t, None, None, True, draws)
        observer_setup = (initial, list(p), list(t), None, None, True, draws)
        with patch("experiments.process_natural.setup", return_value=engine_setup), patch("experiments.process_natural_audit.expected_setup", return_value=observer_setup):
            data = encoded(run_world(32, 128))
            verify_world(data)
            self.assertEqual(len(data["branches"]), 3)
            self.assertEqual(data["branches"][0]["first"]["tick"], 32)
            self.assertEqual(data["branches"][0]["first"]["match_id"], "g5")
            birth = data["branches"][0]["first"]["birth_event"]
            baseline = data["branches"][0]["receipt"]["events"][:birth + 1]
            states = []
            for branch in data["branches"][1:]:
                self.assertEqual(branch["receipt"]["events"][:birth + 1], baseline)
                self.assertEqual(branch["intervention_removals"], 1)
                states.append(branch["receipt"]["events"][birth + 1]["state"])
            for key in ("fuel", "precursor", "waste"):
                self.assertEqual(states[0][key], states[1][key])
            forged = copy.deepcopy(data)
            forged["branches"][1]["first"]["match_id"] = "g0"  # forbidden parent
            with self.assertRaises(ValueError):
                verify_world(forged)

    def test_invented_exposure_or_continuation_rejected(self):
        data = encoded(run_world(32, 0))
        data["branches"][0]["first"] = {"tick": 40, "match_id": "g1"}
        with self.assertRaises(ValueError):
            verify_world(data)
        data = encoded(run_world(32, 128))
        data["branches"].append(copy.deepcopy(data["branches"][0]))
        with self.assertRaises(ValueError):
            verify_world(data)

    def test_repeatability_source_checks_and_coherently_rehashed_forgery(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            revision = "a" * 40
            run_study(root / "original", revision)
            run_study(root / "replay", revision)
            self.assertEqual((root / "original/worlds.jsonl").read_bytes(), (root / "replay/worlds.jsonl").read_bytes())
            summary = audit_study(root / "original", root / "verified", revision)
            self.assertEqual(summary["baseline_worlds"], 32)
            with self.assertRaises(ValueError):
                audit_study(root / "original", root / "verified", revision)
            with self.assertRaises(ValueError):
                audit_study(root / "original", root / "badrevision", "b" * 40)
            lines = (root / "original/worlds.jsonl").read_text().splitlines()
            data = json.loads(lines[0])
            data["branches"][0]["P_attempts"] += 1
            lines[0] = json.dumps(data, sort_keys=True)
            raw = ("\n".join(lines) + "\n").encode()
            (root / "original/worlds.jsonl").write_bytes(raw)
            manifest = json.loads((root / "original/manifest.json").read_bytes())
            manifest["worlds_sha256"] = hashlib.sha256(raw).hexdigest()
            (root / "original/manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "natural schedule"):
                audit_study(root / "original", root / "forged", revision)
