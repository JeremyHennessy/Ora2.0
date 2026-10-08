import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import interface_opportunity as model
from experiments import interface_opportunity_audit as audit


class InterfaceOpportunityTests(unittest.TestCase):
    def test_frozen_panel_differential_and_strong_nulls(self):
        for seed in range(80, 96):
            for material in (32, 0):
                world = model.run_world(seed, material)
                self.assertEqual(world, audit.expected_world(seed, material))
                active, _, fixed, _, yoked = world["arms"]
                self.assertEqual(audit.normalize(active), audit.normalize(fixed))
                self.assertEqual(audit.normalize(active, True), audit.normalize(yoked, True))
                for r in world["arms"]:
                    ids = [e["carrier_id"] for e in r["events"] if e["kind"] == "construct"]
                    self.assertEqual(len(ids), len(set(ids)))
                    self.assertLessEqual(len(ids), material // 4)
                    self.assertEqual(len(r["ticks"]), 64)
                    self.assertEqual(sum(r["initial_sites"]), 16)

    def test_panel_and_external_schedule_guards(self):
        for seed, material in ((79, 32), (8000, 32), (True, 32), (80, False), (80, 33)):
            with self.assertRaises(ValueError):
                model.run_world(seed, material)
        with self.assertRaises(ValueError):
            model.simulate(80, 32, "active", [(0, 0)])
        with self.assertRaises(ValueError):
            model.simulate(80, 32, "external_yoked", [(64, 0)])

    def test_authored_decay_and_rebuild_fixture_not_sampled_evidence(self):
        stock = [16] + [0] * 7
        stream = [[0, 0, 0], [0, 1, 31], [0, 0, 31], [0, 1, 31]] + [[0, 0, 31]] * 60
        with patch.object(model, "setup", return_value=(stock.copy(), stream)), patch.object(audit, "initial", return_value=(stock.copy(), stream)):
            # Return fresh stock for each simulator: it consumes local nutrient.
            with patch.object(model, "setup", side_effect=lambda _: (stock.copy(), stream)):
                r = model.simulate(80, 32, "active")
            self.assertEqual(r, audit.expected_arm(80, 32, "active"))
            self.assertEqual([e["carrier_id"] for e in r["events"] if e["kind"] == "construct"], ["c0", "c1"])
            self.assertEqual([e["carrier_id"] for e in r["events"] if e["kind"] == "decay"], ["c0"])
            self.assertEqual(sum(e["kind"] == "convert" for e in r["events"]), 1)
            self.assertTrue(any(e["kind"] == "construct_unavailable" and e["reason"] == "occupied" for e in r["events"]))

    def test_unfunded_material_cannot_capture_through_yoke(self):
        world = model.run_world(80, 0)
        for r in world["arms"]:
            self.assertFalse(any(e["kind"] in ("construct", "convert") for e in r["events"]))
            self.assertEqual(sum(r["terminal"]["sites"]), 16)
        self.assertEqual(world["arms"][-1]["source_schedule"], [])

    def test_archive_replay_source_opportunity_and_yoke_forgery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model.run_study(root / "original", "a" * 40)
            model.run_study(root / "replay", "a" * 40)
            for name in ("worlds.jsonl", "manifest.json"):
                self.assertEqual((root / "original" / name).read_bytes(), (root / "replay" / name).read_bytes())
            audit.audit_study(root / "original", root / "audit", "a" * 40)
            with self.assertRaises(ValueError):
                audit.audit_study(root / "original", root / "wrong", "b" * 40)
            with self.assertRaises(ValueError):
                model.run_study(root / "original", "a" * 40)
            original = (root / "original" / "worlds.jsonl").read_bytes()
            original_manifest = json.loads((root / "original" / "manifest.json").read_bytes())
            for corruption in ("opportunity", "yoke", "material"):
                rows = [json.loads(line) for line in original.splitlines()]
                if corruption == "opportunity":
                    flags = rows[0]["arms"][0]["ticks"][0]["opportunities"]
                    flags["funded_carrier_contact"] = not flags["funded_carrier_contact"]
                elif corruption == "yoke":
                    rows[0]["arms"][-1]["source_schedule"] = [[64, 0]]
                else:
                    rows[0]["arms"][0]["events"][0]["state"]["free_material"] += 4
                raw = "".join(model.encode(r) + "\n" for r in rows).encode()
                (root / "original" / "worlds.jsonl").write_bytes(raw)
                manifest = dict(original_manifest, raw_sha256=hashlib.sha256(raw).hexdigest())
                (root / "original" / "manifest.json").write_text(model.encode(manifest))
                with self.assertRaisesRegex(ValueError, "reconstruction"):
                    audit.audit_study(root / "original", root / corruption, "a" * 40)
