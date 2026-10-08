"""Post-hoc diagnostic tests using dev-only spatial worlds (not original trial)."""
from pathlib import Path
import json
import tempfile
import unittest

from experiments.closure_spatial import study
from experiments.closure_spatial_diagnostics import analyze, boot_seed_cluster


class IndependentDiagnosticsTests(unittest.TestCase):
    def _dataset(self, td):
        input_dir, output_dir = Path(td)/"worlds", Path(td)/"report"
        study(input_dir, [0], revision="development-only")
        return input_dir, output_dir

    def test_complete_trace_checks_and_report_are_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as td:
            root, destination = self._dataset(td)
            first = analyze(root, destination, original_hashes=False)
            snapshot = (destination/"diagnostic-summary.json").read_bytes()
            second = analyze(root, destination, original_hashes=False)
            self.assertEqual(first, second)
            self.assertEqual(snapshot, (destination/"diagnostic-summary.json").read_bytes())
            self.assertEqual(first["treatment_records"], 18)
            self.assertEqual(first["verified_step_traces"], 1080)
            self.assertTrue(first["world_and_trace_sha256_verified"])
            self.assertFalse(first["hashes_verified"])

    def test_original_only_hash_is_not_bypassed_by_a_replay(self):
        with tempfile.TemporaryDirectory() as td:
            root, destination = self._dataset(td)
            with self.assertRaisesRegex(ValueError, "raw data hash mismatch"):
                analyze(root, destination, original_hashes=True)

    def test_trace_discontinuity_or_mass_leak_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root, destination = self._dataset(td)
            file = root/"traces.jsonl"
            lines = file.read_text().splitlines()
            changed = json.loads(lines[0])
            changed["mass_residual"] = 1
            lines[0] = json.dumps(changed)
            file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ledger breach"):
                analyze(root, destination, original_hashes=False)

    def test_world_specific_event_chain_hash_detects_forgery(self):
        with tempfile.TemporaryDirectory() as td:
            root, destination = self._dataset(td)
            f = root/"worlds.jsonl"
            lines = f.read_text().splitlines()
            altered = json.loads(lines[0])
            altered["trace_sha256"] = "0"*64
            lines[0] = json.dumps(altered, sort_keys=True)
            f.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "world-specific SHA256"):
                analyze(root, destination, original_hashes=False)

    def test_missing_world_cannot_be_hidden(self):
        with tempfile.TemporaryDirectory() as td:
            root, destination = self._dataset(td)
            f = root/"worlds.jsonl"
            f.write_text("\n".join(f.read_text().splitlines()[:-1]) + "\n")
            with self.assertRaisesRegex(ValueError, "Incomplete origin/treatment"):
                analyze(root, destination, original_hashes=False)

    def test_bootstrap_is_clustered_by_seed_not_individual_frame(self):
        world_differences = {0: [1, 1], 1: [-1], 2: [0]}
        a = boot_seed_cluster(world_differences)
        b = boot_seed_cluster(world_differences)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 2)
        self.assertTrue(-1 <= a[0] <= a[1] <= 1)


if __name__ == "__main__":
    unittest.main()
