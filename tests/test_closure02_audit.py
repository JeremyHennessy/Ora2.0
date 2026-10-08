"""Independent archive validation tests for CLOSURE-02 (dev-only seeds 0..7)."""
import json
from pathlib import Path
import tempfile
import unittest

from experiments.closure02_functional import run_study
from experiments.closure02_audit import audit, FROZEN


class IndependentArchivedRecords(unittest.TestCase):
    def _fixture(self, root):
        input_dir=root/"input"
        output_dir=root/"verified"
        run_study(input_dir,[0],revision="dev-only")
        return input_dir,output_dir

    def test_dev_records_and_trace_chains_pass(self):
        with tempfile.TemporaryDirectory() as td:
            input_dir,output=self._fixture(Path(td))
            verified=audit(input_dir,output,first_run=False)
            self.assertEqual(verified["worlds"],15)
            self.assertEqual(verified["verified_steps"],900)
            self.assertTrue(verified["all_world_event_chains_valid"])
            self.assertFalse(verified["match_original_run"])
            self.assertEqual(len((output/"verified-worlds.jsonl").read_text().splitlines()),15)
            self.assertEqual(json.loads((output/"audit-summary.json").read_text())["worlds"],15)

    def test_new_data_cannot_impersonate_original_holdout(self):
        with tempfile.TemporaryDirectory() as td:
            input_dir,output=self._fixture(Path(td))
            with self.assertRaisesRegex(ValueError,"original CLOSURE-02 raw SHA256"):
                audit(input_dir,output,first_run=True)
            self.assertEqual(set(FROZEN),{"worlds.jsonl","traces.jsonl"})

    def test_manifest_and_per_world_hash_cannot_be_silently_changed(self):
        with tempfile.TemporaryDirectory() as td:
            input_dir,output=self._fixture(Path(td))
            trace_file=input_dir/"traces.jsonl"
            lines=trace_file.read_text().splitlines()
            first=json.loads(lines[0])
            first["core_a"]+=1
            lines[0]=json.dumps(first,sort_keys=True)
            trace_file.write_text("\n".join(lines)+"\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"SHA256 manifest"):
                audit(input_dir,output,first_run=False)

    def test_dropped_condition_refused_even_with_rebuilt_summary_hash(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            input_dir,output=self._fixture(Path(td))
            f=input_dir/"worlds.jsonl"
            rows=f.read_text().splitlines()
            f.write_text("\n".join(rows[:-1])+"\n",encoding="utf-8")
            summary_f=input_dir/"summary.json"
            summary=json.loads(summary_f.read_text())
            summary["worlds_sha256"]=hashlib.sha256(f.read_bytes()).hexdigest()
            summary_f.write_text(json.dumps(summary),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Incomplete or extra treatment"):
                audit(input_dir,output,first_run=False)


if __name__=="__main__":
    unittest.main()
