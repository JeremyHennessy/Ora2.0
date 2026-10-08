import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from experiments import laboratory_status as observer


class LaboratoryStatusTests(unittest.TestCase):
    def receipt(self, root, name, value):
        directory = root/'runs'/name
        directory.mkdir(parents=True)
        path = directory/'manifest.json'
        path.write_text(json.dumps(value),encoding='utf-8')
        return path

    def test_mixed_receipts_preserve_failures_inputs_and_stable_page(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            self.receipt(root,'old',{'run_id':'legacy','status':'verified','source_revision':'a'*40})
            self.receipt(root,'new',{'status':'passed','revision':'b'*40,'passed_tests':260})
            self.receipt(root,'negative',{'status':'failed','revision':'c'*40,'error':'preserved failure'})
            before={str(p):p.read_bytes() for p in (root/'runs').rglob('*.json')}
            r=observer.refresh(root,{'Ora2.0':'d'*40},'2026-10-08T00:00:00+00:00')
            first=(root/'observer/index.html').read_bytes()
            observer.refresh(root,{'Ora2.0':'d'*40},'2026-10-08T00:00:00+00:00')
            self.assertEqual(first,(root/'observer/index.html').read_bytes())
            self.assertEqual(before,{str(p):p.read_bytes() for p in (root/'runs').rglob('*.json')})
            rows={r['run_id']:r for r in r['runs']}
            self.assertEqual(rows['new']['source_revision'],'b'*40)
            self.assertEqual(rows['new']['label_source'],'directory')
            self.assertEqual(rows['negative']['reported_status'],'failed')
            self.assertTrue(all(not row['independently_audited'] and row['process_health']=='unverified' for row in rows.values()))

    def test_malformed_ambiguous_and_unknown_sources_remain_visible(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            bad=self.receipt(root,'bad',{})
            bad.write_text('{"status":"passed","status":"failed"}',encoding='utf-8')
            self.receipt(root,'ambiguous',{'source_revision':'a'*40,'revision':'b'*40,'status':'passed'})
            self.receipt(root,'unknown',{'revision':['x'],'status':True,'passed_tests':True})
            rows={r['run_id']:r for r in observer.collect(root)}
            self.assertEqual(rows['bad']['reported_status'],'unreadable_receipt')
            self.assertIsNone(rows['ambiguous']['source_revision'])
            self.assertEqual(rows['unknown']['reported_status'],'unknown')
            self.assertIsNone(rows['unknown']['reported_passed_tests'])

    def test_all_labels_are_escaped_and_cannot_supply_paths_or_commands(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            self.receipt(root,'safe',{'run_id':'<script>alert(1)</script>','status':'<img src=x onerror=bad>','revision':'a'*40,'output_dir':'../../escape'})
            r=observer.report(root,{},'fixed')
            page=observer.render(r)
            self.assertNotIn('<script>',page)
            self.assertNotIn('<img',page)
            self.assertIn('&lt;script&gt;',page)
            self.assertEqual(r['runs'][0]['receipt_path'],str(root/'runs/safe/manifest.json'))
            self.assertFalse((root.parent/'escape').exists())

    def test_size_count_and_reparse_guards_are_bounded(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            p=self.receipt(root,'large',{})
            p.write_bytes(b' '*(observer.MAX_RECEIPT+1))
            rows=observer.collect(root)
            self.assertEqual(rows[0]['reported_status'],'unreadable_receipt')
            with patch.object(observer,'MAX_RUNS',0), self.assertRaises(ValueError):
                observer.collect(root)
            with patch.object(Path,'lstat',return_value=SimpleNamespace(st_mode=0,st_file_attributes=1024)), patch.object(observer.stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024,create=True), self.assertRaises(ValueError):
                observer.regular(p)


if __name__ == '__main__':
    unittest.main()
