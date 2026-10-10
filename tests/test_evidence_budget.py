import copy
import io
import json
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import zipfile
from experiments.evidence_budget import Budget,QuotaError
from experiments.evidence_budget_audit import audit


class EvidenceBudgetTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'case'
    def tearDown(self):self.tmp.cleanup()
    def test_phase_and_combined_refuse_before_mutation(self):
        b=Budget(self.root,{'raw':8,'failure':8},10)
        with b.create('raw','a') as f:
            f.write(b'12345678');before=copy.deepcopy(b.snapshot())
            with self.assertRaises(QuotaError):f.write(b'x')
            self.assertEqual(b.snapshot(),before)
        with self.assertRaises(QuotaError):b.create('failure','new',3)
        self.assertFalse((self.root/'failure/new').exists())
        with b.create('failure','notice') as f:f.write(b'!!')
        self.assertEqual(audit(self.root,b.snapshot(),{'raw':8,'failure':8},10)['logical_bytes'],10)
    def test_sparse_growth_and_header_rewrite(self):
        b=Budget(self.root,{'raw':8},8)
        with b.create('raw','a') as f:
            f.write(b'1234');f.seek(0);f.write(b'XX');self.assertEqual(b.used['raw'],4)
            f.seek(8)
            with self.assertRaises(QuotaError):f.write(b'x')
        self.assertEqual((self.root/'raw/a').read_bytes(),b'XX34')
    def test_failed_write_keeps_charge_and_partial_evidence(self):
        b=Budget(self.root,{'raw':8},8)
        with b.create('raw','a') as f:
            real=f.stream
            class Partial:
                def tell(self):return real.tell()
                def write(self,data):return real.write(data[:2])
                def close(self):return real.close()
            f.stream=Partial()
            with self.assertRaises(OSError):f.write(b'123456')
        self.assertEqual(b.used['raw'],6)
        self.assertEqual((self.root/'raw/a').read_bytes(),b'12')
        self.assertEqual(audit(self.root,b.snapshot(),{'raw':8},8)['reserved_bytes'],6)
    def test_zip_growth_and_restore_are_charged(self):
        limits={'raw':1024,'archive':4096,'restore':1024};b=Budget(self.root,limits,6144)
        with b.create('raw','a') as f:f.write(b'abc'*100)
        with b.create('archive','a.zip') as f:
            with zipfile.ZipFile(f,'w',zipfile.ZIP_DEFLATED) as z:z.write(self.root/'raw/a','a')
        with zipfile.ZipFile(self.root/'archive/a.zip') as z:
            with b.create('restore','a',z.getinfo('a').file_size) as f:f.write(z.read('a'))
        self.assertEqual((self.root/'raw/a').read_bytes(),(self.root/'restore/a').read_bytes())
        result=audit(self.root,b.snapshot(),limits,6144)
        self.assertEqual(result['logical_bytes'],sum(x.stat().st_size for x in self.root.rglob('*') if x.is_file()))
    def test_independent_denominator_and_forged_reservation(self):
        limits={'raw':10};b=Budget(self.root,limits,10)
        with b.create('raw','a') as f:f.write(b'x')
        receipt=copy.deepcopy(b.snapshot());receipt['total_reserved']=0
        with self.assertRaises(ValueError):audit(self.root,receipt,limits,10)
        (self.root/'raw/extra').write_bytes(b'x')
        with self.assertRaises(ValueError):audit(self.root,b.snapshot(),limits,10)
    def test_unsafe_paths_invalid_limits_and_existing_data(self):
        with self.assertRaises(QuotaError):Budget(self.root,{'raw':True},10)
        b=Budget(self.root,{'raw':10},10)
        for p in ('../x','/x','a//x','a/../x','C:/x','a\\x'):
            with self.assertRaises(QuotaError):b.create('raw',p)
        with b.create('raw','a') as f:f.write(b'x')
        with self.assertRaises(QuotaError):b.create('raw','a')
        with patch('experiments.evidence_budget.plain',side_effect=QuotaError('reparse')):
            with self.assertRaises(QuotaError):b.create('raw','b')
        self.assertEqual((self.root/'raw/a').read_bytes(),b'x')
    def test_actual_hard_link_is_refused_before_write(self):
        b=Budget(self.root,{'raw':10},10)
        with b.create('raw','a') as f:
            f.write(b'x');os.link(self.root/'raw/a',self.root/'raw/alias')
            before=copy.deepcopy(b.snapshot())
            with self.assertRaises(QuotaError):f.write(b'y')
            self.assertEqual(b.snapshot(),before)
        self.assertEqual((self.root/'raw/alias').read_bytes(),b'x')
        with self.assertRaises(ValueError):audit(self.root,b.snapshot(),{'raw':10},10)

    def large_inventory(self,b):
        # Finite filesystem fixture whose receipt crosses the former 64 KiB guess.
        for i in range(400):
            with b.create('raw',str(i).zfill(4)+'x'*160) as f:f.write(b'x')

    def test_old_snapshot_pattern_has_valid_live_but_invalid_saved_ledger(self):
        limits={'raw':1024,'failure':262144};b=Budget(self.root,limits,263168)
        self.large_inventory(b)
        with b.create('failure','budget.json',65536) as f:
            f.write(json.dumps(b.snapshot()).encode())
        saved=json.loads((self.root/'failure/budget.json').read_bytes())
        self.assertGreater((self.root/'failure/budget.json').stat().st_size,65536)
        audit(self.root,b.snapshot(),limits,263168)
        with self.assertRaisesRegex(ValueError,'Physical bytes exceed'):
            audit(self.root,saved,limits,263168)

    def test_saved_snapshot_accounts_for_itself_and_refuses_overwrite(self):
        limits={'raw':1024,'failure':262144};b=Budget(self.root,limits,263168)
        self.large_inventory(b)
        path=b.write_snapshot('failure','budget.json')
        saved=json.loads(path.read_bytes())
        self.assertGreater(path.stat().st_size,65536)
        self.assertEqual(saved,b.snapshot())
        audit(self.root,saved,limits,263168)
        before=path.read_bytes()
        with self.assertRaises(QuotaError):b.write_snapshot('failure','budget.json')
        self.assertEqual(path.read_bytes(),before)

    def test_snapshot_capacity_refusal_precedes_content_write(self):
        for limits,total in [({'raw':10,'failure':10},1000),
                             ({'raw':10,'failure':1000},10)]:
            with self.subTest(limits=limits,total=total):
                root=self.root/str(total);self.root.mkdir(exist_ok=True)
                b=Budget(root,limits,total)
                with b.create('raw','a') as f:f.write(b'x')
                with self.assertRaises(QuotaError):b.write_snapshot('failure','budget.json')
                self.assertEqual((root/'failure/budget.json').read_bytes(),b'')
                audit(root,b.snapshot(),limits,total)


if __name__=='__main__':unittest.main()
