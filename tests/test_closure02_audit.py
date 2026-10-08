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


    def _rebuild_manifest(self, input_dir, edit):
        """Adversarial archive with coherent hashes: checks must inspect values."""
        import hashlib
        from experiments.closure02_functional import canonical
        wf, tf = input_dir/"worlds.jsonl", input_dir/"traces.jsonl"
        worlds = [json.loads(x) for x in wf.read_text().splitlines()]
        traces = [json.loads(x) for x in tf.read_text().splitlines()]
        edit(worlds, traces)
        for w in worlds:
            lines = [canonical(t)+"\n" for t in traces
                     if (t["seed"],t["origin"],t["arm"]) ==
                        (w["seed"],w["origin"],w["arm"])]
            w["trace_sha256"] = hashlib.sha256("".join(lines).encode()).hexdigest()
        wf.write_text("".join(canonical(w)+"\n" for w in worlds), encoding="utf-8")
        tf.write_text("".join(canonical(t)+"\n" for t in traces), encoding="utf-8")
        sf = input_dir/"summary.json"
        s = json.loads(sf.read_text())
        s["worlds_sha256"] = hashlib.sha256(wf.read_bytes()).hexdigest()
        s["traces_sha256"] = hashlib.sha256(tf.read_bytes()).hexdigest()
        sf.write_text(json.dumps(s), encoding="utf-8")

    def test_forged_core_flag_rejected_even_with_valid_rebuilt_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = self._fixture(Path(td))
            def forge(worlds, traces):
                traces[0]["core_ok"] = not traces[0]["core_ok"]
            self._rebuild_manifest(src, forge)
            with self.assertRaisesRegex(ValueError, "threshold flag"):
                audit(src, out, first_run=False)

    def test_forged_mass_rejected_even_when_residual_flag_is_zero(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = self._fixture(Path(td))
            def forge(worlds, traces):
                traces[0]["counts"]["w"] += 1
            self._rebuild_manifest(src, forge)
            with self.assertRaisesRegex(ValueError, "particle ledger"):
                audit(src, out, first_run=False)

    def test_false_cost_ledger_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = self._fixture(Path(td))
            def forge(worlds, traces):
                traces[0]["cumulative_flow"]["catalytic_s_consumed"] += 1
            self._rebuild_manifest(src, forge)
            with self.assertRaisesRegex(ValueError, "reaction debit"):
                audit(src, out, first_run=False)

    def test_execution_revision_and_source_checksum_verified(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = self._fixture(Path(td))
            with self.assertRaisesRegex(ValueError, "revision mismatch"):
                audit(src, out, first_run=False, expected_revision="wrong")
            sf = src/"summary.json"
            s = json.loads(sf.read_text())
            s["source_sha256"] = "0"*64
            sf.write_text(json.dumps(s), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source checksum"):
                audit(src, out, first_run=False)

    def test_audit_cannot_write_into_or_above_input(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = self._fixture(Path(td))
            for target in (src, src/"analysis", src.parent):
                with self.subTest(target=target):
                    with self.assertRaisesRegex(ValueError, "separate"):
                        audit(src, target, first_run=False)


if __name__=="__main__":
    unittest.main()
