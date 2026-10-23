import sys,unittest,tempfile,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.digital_pilot74_continuation_preflight_v1 import *
class Preflight(unittest.TestCase):
    def packet(self,d):
        p=Path(d)/'source.py';p.write_bytes(b'# synthetic source only\n');s=dict(path=str(p),extent=p.stat().st_size,sha256=digest(p.read_bytes()))
        pins={'experiments/fixture.py':s}
        return dict(configuration=CONFIG,revision='a'*40,source_files=pins,source_sha256=digest(encode({n:x['sha256'] for n,x in pins.items()})),reviews={},preserve_closed_results=True,world_launches=0)
    def test_missing_gates_are_not_permission(self):
        with tempfile.TemporaryDirectory() as d:
            r=inspect(self.packet(d));self.assertEqual(r['gate_receipts_missing'],list(GATES));self.assertFalse(r['qualification_request_ready']);self.assertFalse(r['execution_authorized'])
    def test_changed_source_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.packet(d);Path(p['source_files']['experiments/fixture.py']['path']).write_bytes(b'changed')
            with self.assertRaises(ValueError):inspect(p)
    def test_wider_horizon_or_mutation_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.packet(d);p['configuration']=dict(CONFIG,horizon=20000)
            with self.assertRaises(ValueError):inspect(p)
    def test_ci_for_other_revision_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.packet(d);r=dict(schema='PILOT74-EXTERNAL-GATE-REVIEW-v2',kind='whole_source_ci',revision='b'*40,source_sha256=p['source_sha256'],configuration_sha256=digest(encode(CONFIG)),scope='new_pilot74_whole_source_only',verdict='PASS')
            f=Path(d)/'ci.json';f.write_bytes(encode(r));p['reviews']['whole_source_ci']=dict(path=str(f),extent=f.stat().st_size,sha256=digest(f.read_bytes()))
            with self.assertRaises(ValueError):inspect(p)
    def test_template_pass_cannot_replace_native_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.packet(d);r=dict(schema='PILOT74-EXTERNAL-GATE-REVIEW-v2',kind='custody',revision=p['revision'],source_sha256=p['source_sha256'],configuration_sha256=digest(encode(CONFIG)),scope='new_pilot74_whole_source_only',verdict='PASS',native_records=[],archive_restore_exact=True)
            f=Path(d)/'review.json';f.write_bytes(encode(r));p['reviews']['custody']=dict(path=str(f),extent=f.stat().st_size,sha256=digest(f.read_bytes()))
            with self.assertRaises(ValueError):inspect(p)
    def test_preparation_cannot_launch_or_rescore(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.packet(d);p['world_launches']=1
            with self.assertRaises(ValueError):inspect(p)
if __name__=='__main__':unittest.main()
