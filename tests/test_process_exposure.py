"""Development diagnostic validation; no restoration/held-out outcome tests."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from experiments.process_exposure import diagnose, snapshot, select, run_study
from experiments.process_exposure_audit import verify, audit_study, unique


class ExposureTests(unittest.TestCase):
    def test_all_fresh_snapshots_and_coupons_independently_verify(self):
        for seed in range(16, 24):
            for regime in (128, 0):
                data = json.loads(json.dumps(diagnose(seed, regime)))
                before = json.dumps(data, sort_keys=True)
                row = verify(data)
                self.assertEqual(row["coupons"], len(data["coupons"]))
                self.assertFalse(row["spontaneous_repair_evidence"])
                self.assertEqual(row["coupon_material_used"], 4 * row["coupon_fuel_used"])
                self.assertEqual(json.dumps(data, sort_keys=True), before)

    def test_selector_all_failure_categories_with_authored_genomes(self):
        # Structural fixtures only, not sampled worlds or restoration successes.
        a, b, c, d = (2, 0, 3, 0), (0, 1, 1, 2), (0, 2, 0, 0), (0, 2, 0, 2)
        p, t = [0, 1, 3, 1], [1, 2, 3, 0]
        live = dict(a=a, b=b, c=c, d=d)
        state = {"precursor": 4, "fuel": 1}
        args = (p, t, (a, b))
        self.assertEqual(select(live, *args, False, state)["status"], "no_motif")
        self.assertEqual(select({"a": a, "c": c}, *args, True, state)["status"], "no_cut_opportunity")
        self.assertEqual(select({"a": a, "b": b, "c": c}, *args, True, state)["status"], "no_sham_match")
        self.assertEqual(select(live, *args, True, {"precursor": 0, "fuel": 1})["status"], "unaffordable")
        ready = select(live, *args, True, state)
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(ready["cut"], ("a", "b"))
        self.assertEqual(ready["sham"], ("a", "d"))

    def test_reserved_and_old_seeds_cannot_execute(self):
        for seed in (0, 7, 8000, 8063, 24, True):
            with self.assertRaises(ValueError):
                snapshot(seed, 128)

    def test_raw_replay_and_coherent_selector_forgery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            revision = "a" * 40
            run_study(root / "one", revision)
            run_study(root / "two", revision)
            self.assertEqual((root / "one" / "snapshots.jsonl").read_bytes(), (root / "two" / "snapshots.jsonl").read_bytes())
            result = audit_study(root / "one", root / "audit", revision)
            self.assertEqual(result["snapshots"], 16)
            with self.assertRaises(ValueError):
                audit_study(root / "one", root / "audit", revision)
            with self.assertRaises(ValueError):
                audit_study(root / "one", root / "wrong", "b" * 40)
            lines = (root / "one" / "snapshots.jsonl").read_text().splitlines()
            forged = json.loads(lines[0])
            forged["selection"]["producer_pairs"] += 1
            lines[0] = json.dumps(forged, sort_keys=True)
            raw = ("\n".join(lines) + "\n").encode()
            (root / "one" / "snapshots.jsonl").write_bytes(raw)
            manifest = json.loads((root / "one" / "manifest.json").read_bytes())
            manifest["snapshots_sha256"] = hashlib.sha256(raw).hexdigest()
            (root / "one" / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "opportunity/selector"):
                audit_study(root / "one", root / "forged", revision)

    def test_coupon_and_snapshot_corruption_rejected(self):
        for seed in range(16, 24):
            data = json.loads(json.dumps(diagnose(seed, 128)))
            forged = json.loads(json.dumps(data))
            forged["ticks"][0]["draws"][0] = 0.5
            with self.assertRaises(ValueError):
                verify(forged)
            if data["coupons"]:
                for change in ("cost", "prefix", "label"):
                    forged = json.loads(json.dumps(data))
                    coupon = forged["coupons"][0]
                    if change == "cost":
                        coupon["receipt"]["events"][-1]["state"]["fuel"] += 1
                    elif change == "prefix":
                        coupon["receipt"]["events"][0]["a"] = "missing-parent"
                    else:
                        coupon["externally_scheduled"] = False
                    with self.assertRaises((ValueError, KeyError)):
                        verify(forged)

    def test_duplicate_json_and_boolean_panel_ids_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"seed":16,"seed":17}', object_pairs_hook=unique)
        data = json.loads(json.dumps(diagnose(16, 128)))
        data["regime"] = False
        with self.assertRaises(ValueError):
            verify(data)
