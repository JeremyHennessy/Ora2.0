"""Paid benchmark apparatus boundary only; no registered World or performance."""
import copy
import hashlib
import io
import json
import unittest
from unittest.mock import patch
from experiments import digital_cognitive76_benchmark as bench
from experiments import digital_cognitive76_source as source

def request(kind='generate',export='original'):
    pins={p:'b'*64 for p in bench.REQUIRED};cfg=copy.deepcopy(bench.CONFIG)
    return dict(configuration=cfg,revision='a'*40,source_files=pins,
                source_sha256=hashlib.sha256(bench.boundary.canonical(pins)).hexdigest(),
                configuration_sha256=hashlib.sha256(bench.boundary.canonical(cfg)).hexdigest(),
                seed=77400,kind=kind,export=export,role=f'{export}:77400:benchmark:{kind}',
                input=None if kind=='generate' else {},grant=dict(limit=(1 if kind=='audit' else 16)*1024**2),grant_seal='c'*64)

class BenchmarkBoundary(unittest.TestCase):
    def test_authored_updater_is_explicit_and_not_inserted_in_blind_bank(self):
        before=source.manifest();programme=bench.programme()
        self.assertEqual(programme[16:18],[[18,0,0],[21,0,0]])
        self.assertEqual(3*len(programme)+16,76)
        self.assertEqual(before,source.manifest())
        self.assertNotIn(bench.NAME,source.programmes())
        self.assertFalse(bench.CONFIG['primary_bank_changed'])
    def test_one_context_has_all_three_ordinary_model_controls(self):
        self.assertEqual(bench.ARMS,('intact','model_disabled','history_misbound'))
        for kind,export in (('generate','original'),('generate','restored'),('audit','original')):
            r=request(kind,export)
            with patch.object(bench.boundary,'validate_grant') as checked:
                self.assertEqual(bench.admit(r),r['role']);checked.assert_called_once()
    def test_reserves_scope_and_configuration_refused_before_grant(self):
        for change in (dict(seed=True),dict(seed=77500),dict(seed=77700),dict(role='candidate15'),dict(kind='service'),dict(configuration=dict(bench.CONFIG,formation=0))):
            r=request();r.update(change)
            with patch.object(bench.boundary,'validate_grant',side_effect=RuntimeError('grant reached')):
                with self.assertRaises(AssertionError):bench.admit(r)
    def test_caps_proof_export_and_complete_source_are_bound(self):
        with patch.object(bench.boundary,'validate_grant'):
            with self.assertRaises(AssertionError):bench.admit(request('audit','restored'))
            r=request();r['grant']['limit']+=1
            with self.assertRaises(AssertionError):bench.admit(r)
            r=request();r['source_files'].pop('experiments/digital_cognitive76_benchmark.py')
            with self.assertRaises(AssertionError):bench.admit(r)

    def test_failed_generation_restores_methods_and_primary_route_table(self):
        from experiments import digital_cognitive76_world as kernel
        from experiments import digital_cognitive76_history as producer
        r=request();before=(kernel.World.__init__,kernel.World.step)
        routes=copy.deepcopy(kernel.PROGRAMS);error=io.StringIO()
        with patch.object(bench.sys,'argv',['prepared','D:/OraLab/unused']),patch.object(bench.boundary,'bounded_bytes',return_value=bench.boundary.canonical(r)),patch.object(bench.boundary,'validate_grant'),patch.object(bench.boundary,'verify_source',return_value=r['source_sha256']),patch.object(producer,'history',side_effect=RuntimeError('prepared benchmark stop')),patch.object(bench.sys,'stderr',error):
            with self.assertRaisesRegex(RuntimeError,'prepared benchmark stop'):bench.main()
        self.assertIs(kernel.World.__init__,before[0]);self.assertIs(kernel.World.step,before[1])
        self.assertEqual(kernel.PROGRAMS,routes)
        self.assertEqual(json.loads(error.getvalue())['counts'],dict(genesis=0,ordinary_steps=0))

if __name__=='__main__':unittest.main()
