"""Native admission/precharge regressions with NON-PHYSICS fixtures only."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from experiments import digital_inheritance83_custody as old
from experiments import digital_inheritance83_remaining as remaining
from experiments import digital_inheritance83_remaining_child as child
from experiments import digital_inheritance83_remaining_cache as cache
from experiments.evidence_budget import Budget


class RemainingController(unittest.TestCase):
    def test_precharge_every_output_before_mock_launcher(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORALAB_TEST_TMP')) as tmp:
            b=Budget(Path(tmp)/'case',dict(raw=12288*old.M),12288*old.M)
            pins={'fixture_only':'a'*64};slots,cached_grants=cache.precharge(b,pins)
            self.assertEqual(len(slots),209);self.assertEqual(len(cached_grants),3)
            self.assertEqual(sum(k.startswith('raw/native/') for k in b.files),213)
            self.assertEqual(sum(b.files.values()),sum(remaining.allocations().values()))
            # Invented final arithmetic fixtures, never relabelled organism data.
            from tests.test_digital_inheritance83_acceptance import invented_receipts
            cached={}
            for value in invented_receipts()[:3]:
                p=Path(tmp)/('invented-'+str(value['seed'])+'.json');p.write_bytes(old.canonical(value))
                cached[value['seed']]=remaining.spec(p)
            calls=[]
            def launch(role,inputs):calls.append((role,inputs));return {},{}
            def consume(role,inputs,*args):
                if role=='final:acceptance':self.assertEqual(inputs[:3],list(cached.values()))
                token=role.replace('restored:','original:')
                return dict(path='NON-PHYSICS/'+token,extent=1,sha256=old.digest(token))
            with patch.object(old,'consume',consume):
                result=remaining.pipeline(launch,pins,{r:s[0] for r,s in slots.items()},cached)
            self.assertEqual(len(calls),209);self.assertFalse(result['execution_admission'])
            self.assertTrue(all((b.root/'raw'/s[0]['name']).stat().st_size==0 for s in slots.values()))

    def test_new_entry_refuses_cached_metric_software_reserve_source_and_config(self):
        import sys
        before='experiments.digital_inheritance83_world' in sys.modules
        req=dict(configuration=copy.deepcopy(old.CONFIG),source_files={n:'a'*64 for n in (
            'experiments/digital_inheritance83_remaining_child.py','experiments/digital_inheritance83_remaining.py',
            'experiments/digital_inheritance83_remaining_cache.py')},source_sha='',config_sha=old.digest(old.CONFIG),
            role=remaining.plan()[0],kind='generate',input=None,grant={},seal='')
        req['source_sha']=old.digest(req['source_files'])
        with patch.object(child.boundary,'verify_source',return_value=req['source_sha']):child.admit(req)
        for seed in (*remaining.CACHED,2100080,2140080,1009000,1009200):
            bad=copy.deepcopy(req);bad['role']=f'original:{seed}:variation:generate'
            with self.subTest(seed=seed),self.assertRaises(AssertionError):child.admit(bad)
        for seed in remaining.CACHED:
            bad=copy.deepcopy(req);bad.update(role=f'original:{seed}:metrics',kind='metrics',input=[])
            with self.assertRaisesRegex(AssertionError,'cached'):child.admit(bad)
        bad=copy.deepcopy(req);bad['source_sha']='0'*64
        with self.assertRaisesRegex(AssertionError,'source/config'):child.admit(bad)
        bad=copy.deepcopy(req);bad['configuration']['horizon']=1
        with self.assertRaisesRegex(AssertionError,'configuration'):child.admit(bad)
        self.assertEqual(before,'experiments.digital_inheritance83_world' in sys.modules)

    def test_archive_member_tamper_and_escape_refused(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORALAB_TEST_TMP')) as tmp:
            root=Path(tmp);p=root/'data.txt';p.write_bytes(b'NON-PHYSICS')
            archive=root/'source.zip'
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:z.write(p,'data.txt')
            spec=remaining.spec(archive)
            self.assertEqual(cache.archive_members(spec,root,[p])[str(p)],remaining.spec(p))
            p.write_bytes(b'CHANGED')
            with self.assertRaisesRegex(AssertionError,'archive membership'):cache.archive_members(spec,root,[p])
            with self.assertRaises(ValueError):cache.archive_members(spec,root/'foreign',[p])

    def test_changed_manifest_stops_cache_before_native_or_world(self):
        bundle=dict(manifest={'changed':True},interface_report={},interface_archive={},interface_chains={})
        with self.assertRaises(AssertionError):cache.authenticate(bundle)


if __name__=='__main__':unittest.main()
