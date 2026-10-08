import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from experiments import substrate_budget as engine
from experiments import substrate_budget_audit as audit


class SubstrateBudgetTests(unittest.TestCase):
    def test_all_frozen_fixtures_independent_reconstruction(self):
        rows = [engine.run_case(c, candidate, arm) for c in engine.cases() for candidate in ("interface", "trace")
                for arm in engine.ARMS + (("external_flux",) if candidate == "interface" else ())]
        self.assertEqual(rows, audit.expected_rows())
        self.assertEqual(len(rows), 63)
        for r in rows:
            self.assertEqual((r["material_residual"], r["potential_residual"]), (0, 0))

    def test_read_processing_affordability_and_occupied_slot(self):
        case = next(engine.cases())
        case["work"] = 1
        ledger = engine.Ledger(case, "trace", "active")
        ledger.contact()
        self.assertEqual([e["kind"] for e in ledger.events], ["read", "processing_unaffordable"])
        self.assertEqual(ledger.state["work"], 0)
        self.assertEqual(ledger.state["sites"], [3, 0])
        case["work"] = 12
        ledger = engine.Ledger(case, "interface", "active")
        ledger.construct("internal")
        first = json.loads(engine.encode(ledger.state))
        ledger.construct("external")
        self.assertEqual(ledger.state, first)
        self.assertEqual(ledger.events[-1]["reason"], "occupied")
        self.assertEqual(ledger.state["carriers"][0]["origin"], "internal")

    def test_construction_erasure_and_no_free_reserve(self):
        ledger = engine.Ledger(next(engine.cases()), "interface", "active")
        ledger.construct("internal")
        ledger.step("erase")
        self.assertEqual((ledger.state["free_material"], ledger.state["waste"], ledger.state["work"]), (4, 4, 9))
        ledger.step("renew")
        self.assertEqual(ledger.events[-1]["moved"], 0)
        ledger.step("withdraw")
        self.assertEqual((ledger.state["sites"], ledger.state["reserve"]), ([0, 0], 3))
        ledger.step("renew")
        self.assertEqual((ledger.state["sites"], ledger.state["reserve"]), ([1, 0], 2))

    def test_strongest_nulls_renewal_and_foreign_state(self):
        index = {(r["case"], r["candidate"], r["arm"]): r for r in audit.expected_rows()}
        for (name, candidate, arm), r in index.items():
            if arm == "active":
                self.assertEqual(audit.normalize(r), audit.normalize(index[name, candidate, "fixed"]))
                if candidate == "interface":
                    self.assertEqual(audit.normalize(r, True), audit.normalize(index[name, candidate, "external_flux"], True))
        active = index["renewal", "trace", "active"]
        ghost = index["renewal", "trace", "ghost"]
        self.assertEqual(sum(e["kind"] == "convert" for e in active["events"]), 1)
        self.assertEqual(sum(e["kind"] == "convert" for e in ghost["events"]), 2)
        foreign = index["foreign_withdrawal", "trace", "active"]
        self.assertEqual(foreign["events"][0]["origin"], "external")
        self.assertFalse(any(e["kind"] == "convert" for e in foreign["events"]))

    def test_pinned_archive_forgery_and_reuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine.calibrate(root / "original", "a" * 40)
            engine.calibrate(root / "replay", "a" * 40)
            for name in ("manifest.json", "calibrations.jsonl"):
                self.assertEqual((root / "original" / name).read_bytes(), (root / "replay" / name).read_bytes())
            audit.audit_calibration(root / "original", root / "audit", "a" * 40)
            with self.assertRaises(ValueError):
                audit.audit_calibration(root / "original", root / "wrong", "b" * 40)
            with self.assertRaises(ValueError):
                engine.calibrate(root / "original", "a" * 40)
            rows = [json.loads(line) for line in (root / "original" / "calibrations.jsonl").read_bytes().splitlines()]
            rows[0]["events"][0]["state"]["work"] += 1
            raw = "".join(engine.encode(r) + "\n" for r in rows).encode()
            (root / "original" / "calibrations.jsonl").write_bytes(raw)
            manifest = json.loads((root / "original" / "manifest.json").read_bytes())
            manifest["raw_sha256"] = hashlib.sha256(raw).hexdigest()
            (root / "original" / "manifest.json").write_text(engine.encode(manifest))
            with self.assertRaisesRegex(ValueError, "reconstruction"):
                audit.audit_calibration(root / "original", root / "forgery", "a" * 40)
