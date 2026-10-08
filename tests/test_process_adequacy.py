import hashlib
import json
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest

from experiments import process_adequacy as producer
from experiments import process_adequacy_audit as auditor


class AdequacyTests(unittest.TestCase):
    def test_full_table_constraint_and_installed_law(self):
        from experiments.process_pilot import FIXED_TABLE
        table = producer.table_reference()
        self.assertEqual(table["all_target_counts"], auditor.expected_assessment()["table"]["all_target_counts"])
        self.assertTrue(all(r["recipes"] == 64 for r in table["all_target_counts"]))
        self.assertEqual(len(FIXED_TABLE), table["gated_pairs"])
        for (a, b), g in FIXED_TABLE.items():
            self.assertEqual(producer.splice(a, b), g)

    def test_reference_counts_and_budget_controls(self):
        cases = producer.fixtures()
        dense = producer.measure(cases["dense_match"], 128)
        self.assertEqual((dense["recipe_pairs"], dense["matched_recipe_pairs"]), (64, 64))
        self.assertTrue(dense["paid_matched_rate"]["throughput_reference_pass"])
        sparse = producer.measure(cases["sparse_match"], 128)
        self.assertEqual((sparse["recipe_pairs"], sparse["matched_recipe_pairs"]), (1, 1))
        self.assertFalse(sparse["paid_matched_rate"]["throughput_reference_pass"])
        self.assertEqual(producer.measure(cases["sparse_unmatched"], 128)["matched_recipe_pairs"], 0)
        self.assertEqual(producer.measure(cases["absent"], 128)["recipe_pairs"], 0)
        self.assertFalse(producer.measure(cases["dense_match"], 0)["paid_recipe_rate"]["throughput_reference_pass"])
        self.assertEqual(producer.measure(cases["dense_match"], 128, fuel=0)["paid_recipe_rate"]["at_least_one_reference"], 0)

    def test_distinct_ids_duplicate_genomes_and_parent_exclusion(self):
        # A can itself have the matched endpoints; it cannot match its own birth.
        a, b = (0, 0, 2, 3), (1, 1, 3, 0)
        pool = producer.tokens([a, b])
        self.assertEqual(producer.measure(pool, 128)["recipe_pairs"], 1)
        self.assertEqual(producer.measure(pool, 128)["matched_recipe_pairs"], 0)
        pool = producer.tokens([a, b, a])
        measured = producer.measure(pool, 128)
        self.assertEqual((measured["recipe_pairs"], measured["matched_recipe_pairs"]), (2, 2))
        self.assertEqual(measured, auditor.expected_measure(pool, 128))
        # Same-genome self-pair needs distinct IDs; here both parents can create P.
        pool = producer.tokens([(0, 0, 2, 0)] * 3)
        self.assertEqual(producer.measure(pool, 128), auditor.expected_measure(pool, 128))
        removed = producer.tokens([producer.P, producer.T])
        self.assertEqual(producer.measure(removed, 128)["ordered_distinct_id_pairs"], 0)

    def test_exact_threshold_and_panel(self):
        self.assertEqual(producer.assess(), auditor.expected_assessment())
        for q in (Fraction(0), Fraction(1), Fraction(1, 992), Fraction(64, 992), Fraction(1, 1024)):
            minimum = producer.minimum_draws(q)
            self.assertEqual(minimum, auditor.expected_rate(q.numerator, q.denominator)["minimum_static_draws_for_four_fifths"])
            if minimum:
                self.assertTrue(producer.reaches(q, minimum))
                self.assertFalse(producer.reaches(q, minimum - 1))
        report = producer.assess()
        seeds = {c["seed"] for c in report["cases"] if c["panel"] == "structural_calibration"}
        self.assertEqual(seeds, set(range(48, 80)))
        self.assertEqual(report["new_dynamical_worlds"], 0)

    def test_archive_replay_forgery_source_and_reuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            producer.run_assessment(root / "original", "a" * 40)
            producer.run_assessment(root / "replay", "a" * 40)
            for name in ("manifest.json", "assessment.json"):
                self.assertEqual((root / "original" / name).read_bytes(), (root / "replay" / name).read_bytes())
            auditor.audit_assessment(root / "original", root / "audit", "a" * 40)
            with self.assertRaises(ValueError):
                auditor.audit_assessment(root / "original", root / "wrong", "b" * 40)
            with self.assertRaises(ValueError):
                producer.run_assessment(root / "original", "a" * 40)
            raw = json.loads((root / "original" / "assessment.json").read_bytes())
            raw["cases"][0]["recipe_pairs"] += 1
            data = (producer.encode(raw) + "\n").encode()
            (root / "original" / "assessment.json").write_bytes(data)
            manifest = json.loads((root / "original" / "manifest.json").read_bytes())
            manifest["report_sha256"] = hashlib.sha256(data).hexdigest()
            (root / "original" / "manifest.json").write_text(producer.encode(manifest))
            with self.assertRaisesRegex(ValueError, "reconstruction"):
                auditor.audit_assessment(root / "original", root / "forgery", "a" * 40)
