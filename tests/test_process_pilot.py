"""Development-only validation of frozen pilot law and adversarial archives."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.process_pilot import ARMS, run_world, run_study, setup, canonical
from experiments.process_pilot_audit import audit_study, expected_setup, verify_world, exact_p


class PilotTests(unittest.TestCase):
    def test_independent_generator_and_world_law_all_dev_seeds(self):
        for seed in range(8):
            generated = json.loads(canonical(setup(seed)))
            independently = json.loads(canonical(expected_setup(seed)))
            self.assertEqual(generated, independently)
            for regime in (128, 0):
                for arm in ARMS:
                    world = json.loads(canonical(run_world(seed, regime, arm)))
                    result = verify_world(world, expected_setup(seed))
                    self.assertEqual(result["events"], len(world["receipt"]["events"]))

    def test_fixed_table_exact_equivalence_and_seed_replay(self):
        for seed in range(8):
            a = run_world(seed, 128, "constructive")
            b = run_world(seed, 128, "fixed_table")
            self.assertEqual(a["receipt"]["events"], b["receipt"]["events"])
            self.assertEqual(canonical(a), canonical(run_world(seed, 128, "constructive")))

    def test_starvation_and_inert_do_not_restore(self):
        for seed in range(8):
            for arm, resource in (("constructive", 0), ("inert", 128)):
                self.assertFalse(run_world(seed, resource, arm)["result"]["restored"])

    def test_reserved_seeds_cannot_execute(self):
        for seed in (8, 8000, 8063, -1):
            with self.assertRaisesRegex(ValueError, "development panel"):
                run_world(seed, 128, "constructive")

    def test_forged_schedule_and_selector_rejected(self):
        for mutation in (
            lambda w: w["ticks"][0]["draws"].__setitem__(0, 0.5),
            lambda w: w.update(cut=None),
            lambda w: w["receipt"].update(fuel=161),
            lambda w: w["receipt"]["initial_tokens"][0]["genome"].__setitem__(0, 9),
            lambda w: w["ticks"].pop(),
            lambda w: w["receipt"]["events"][0]["state"].update(fuel=160),
        ):
            w = json.loads(canonical(run_world(0, 128, "constructive")))
            mutation(w)
            with self.assertRaises((ValueError, KeyError)):
                verify_world(w, expected_setup(0))

    def test_table_cannot_omit_encountered_entries(self):
        w = json.loads(canonical(run_world(0, 0, "fixed_table")))
        self.assertTrue(w["receipt"]["rules"])
        w["receipt"]["rules"].pop()
        # No precursor means no births; the generic measurement auditor cannot
        # detect this omission. Independent schedule validation must do so.
        with self.assertRaisesRegex(ValueError, "incomplete fixed table"):
            verify_world(w, expected_setup(0))

    def test_archive_rehash_does_not_hide_duplicate_or_forged_history(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "input"
            revision = "a" * 40
            run_study(source, revision)
            first = audit_study(source, root / "verified", revision)
            second = audit_study(source, root / "replayed", revision)
            self.assertEqual(first, second)
            self.assertEqual(first["worlds"], 96)
            with self.assertRaises(ValueError):
                audit_study(source, root / "verified", revision)
            with self.assertRaises(ValueError):
                audit_study(source, root / "wrongrevision", "b" * 40)
            raw = (source / "worlds.jsonl").read_text().splitlines()
            manifest = json.loads((source / "manifest.json").read_text())
            for change in ("duplicate", "schedule"):
                lines = copy.copy(raw)
                if change == "duplicate":
                    lines[1] = lines[0]
                else:
                    w = json.loads(lines[0])
                    w["ticks"][0]["draws"][0] = 0.5
                    lines[0] = canonical(w)
                text = "\n".join(lines) + "\n"
                (source / "worlds.jsonl").write_text(text, encoding="utf-8", newline="\n")
                manifest["worlds_sha256"] = hashlib.sha256(text.encode()).hexdigest()
                (source / "manifest.json").write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    audit_study(source, root / change, revision)

    def test_exact_paired_null_statistics(self):
        self.assertEqual(exact_p(0, 0), 1)
        self.assertEqual(exact_p(4, 0), 0.125)
        self.assertEqual(exact_p(2, 2), 1)

    def test_boolean_panel_identity_rejected(self):
        w = json.loads(canonical(run_world(0, 128, "constructive")))
        w["seed"] = False
        with self.assertRaisesRegex(ValueError, "integer panel"):
            verify_world(w, expected_setup(0))

    def test_authored_control_exposure_fixture_pays_for_suppressed_births(self):
        # Deliberately authored branch-coverage fixture, never a sampled world.
        a, b, c, p, t, d = ((2, 0, 3, 0), (0, 1, 1, 2), (0, 2, 0, 0),
                            (0, 1, 3, 1), (1, 2, 3, 0), (0, 2, 0, 2))
        genesis = [{"id": f"g{i}", "genome": list(g)} for i, g in enumerate((a, b, c, p, t, d))]
        draws = [[0.0, 0.3, 0.9] for _ in range(160)]
        draws[32] = [0.0, 0.0, 0.9]  # A/B => P, paid cut intercept
        draws[33] = [0.9, 0.6, 0.9]  # rebuilt P/C => T in intact arm
        draws[34] = [0.0, 0.45, 0.9]  # A/D => sham product in sham arm
        prepared = (genesis, p, t, (a, b), (a, d), True, draws)
        independent_fixture = json.loads(canonical(prepared))
        with patch("experiments.process_pilot.setup", return_value=prepared):
            for arm in ("cut", "sham", "inert"):
                w = json.loads(canonical(run_world(0, 128, arm)))
                result = verify_world(w, independent_fixture)
                self.assertGreater(result["suppressed_births"], 0)
                self.assertGreaterEqual(result["material_transformed"], 4 * result["suppressed_births"])
