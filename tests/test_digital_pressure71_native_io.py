"""Mock process dispatcher, actual temporary grants; zero native science/Worlds."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_pressure71_native_io as adapter
from experiments import evidence_write_grant68 as transport
from experiments.evidence_budget import Budget
from experiments.digital_pressure71_runplan import roles, schedule
from experiments.digital_pressure71_admission import digest


def native(output=''):
    return dict(exit_code=0, timed_out=False, output_truncated=False, post_close_processes_exited=True,
                output=output, usage=dict(flags=8716, configured_memory_bytes=768 * 1024**2,
                configured_cpu_ticks=900000000, configured_processes=3, active_before_close=0))


class NativeIOTests(unittest.TestCase):
    def setUp(self):
        root = Path('D:/OraLab/temp') if os.name == 'nt' else None
        self.temp = tempfile.TemporaryDirectory(dir=root, prefix='prepared71-io-')
        self.addCleanup(self.temp.cleanup)
        self.budget = Budget(Path(self.temp.name)/'evidence',
            {k: n * 1024**2 for k, n in dict(raw=24576, archive=24576, restore=24576, failure=8192).items()}, 81920 * 1024**2)
        self.provenance = dict(source_sha256=digest({}), configuration_sha256='b' * 64)
        self.io = adapter.NativeIO(self.budget, {'original': self.temp.name, 'restored': self.temp.name}, {},
                                  self.provenance, lambda: None, ['tests.test_digital_pressure71_controller'], 9)
        # Source checking is explicitly mocked here; separate native handler
        # qualification covers live manifests. These fixtures prove no source truth.
        self.origin = patch.object(adapter, 'verify_source', return_value=self.provenance['source_sha256'])
        self.origin.start(); self.addCleanup(self.origin.stop)

    def precharge(self): self.io.precharge(schedule(), 14976 * 1024**2)

    def test_all416_seals_exist_and_precharged_before_launch(self):
        self.precharge(); self.assertEqual(len(self.io.grants), 416)
        self.assertFalse(self.io.native)
        self.assertEqual(sum(g['limit'] for g, _ in self.io.grants.values()), 14976 * 1024**2)
        for key, (g, seal) in self.io.grants.items():
            self.assertEqual(seal, transport.digest(g)); self.assertEqual(g['role'], ':'.join(key))
            self.assertEqual((Path(g['root'])/g['phase']/g['name']).stat().st_size, 0)
        with self.assertRaises(AssertionError): self.precharge()

    def test_mocked_endpoint_dispatch_actual_record_and_input_binding(self):
        self.precharge(); role = roles()[0]
        def dispatch(command, limits, cwd):
            request = json.loads(Path(command[-1]).read_bytes())
            value = dict(author_fabricated=True, organism_history=False, kind=request['kind'])
            receipt = transport.record(request['grant'], request['grant_seal'], request['source_sha256'],
                                       request['configuration_sha256'], request['role'], value)
            receipt.update(kind=request['kind'], software_only=False, treatment=False, world_constructors=0)
            return native(json.dumps(receipt))
        with patch.object(adapter, 'run', side_effect=dispatch) as run:
            raw, value = self.io.endpoint('original', role, 'raw', None, None)
            proof, value = self.io.endpoint('original', role, 'proof', raw, None)
        self.assertEqual(run.call_count, 2); self.assertIs(value['organism_history'], False)
        self.assertEqual(self.io.receipted_world_constructors, 0)
        request = json.loads((self.budget.root/'raw/requests/original'/role['name']/'proof.json').read_bytes())
        self.assertEqual(request['input'], raw); self.assertEqual(request['dose'], 8)
        self.assertEqual(proof['sha256'], digest(value))

    def test_failed_mock_native_retained_before_refusal_no_retry(self):
        self.precharge(); receipt = native(); receipt['exit_code'] = 1
        with patch.object(adapter, 'run', return_value=receipt) as run:
            with self.assertRaises(AssertionError): self.io.prepared('original')
        self.assertEqual(run.call_count, 1); self.assertEqual(len(self.io.native), 1)
        saved = json.loads((self.budget.root/'raw/native/original/prepared.json').read_bytes())
        self.assertEqual(saved['exit_code'], 1)

    def test_native_timeout_truncation_and_limit_mismatch_refused(self):
        for key in ('timed_out', 'output_truncated'):
            receipt = native(); receipt[key] = True
            with self.assertRaises(AssertionError): self.io.native_check(receipt)
        receipt = native(); receipt['usage']['configured_processes'] = 4
        with self.assertRaises(AssertionError): self.io.native_check(receipt)
        receipt = native(); receipt['usage']['active_before_close'] = 1
        with self.assertRaises(AssertionError): self.io.native_check(receipt)

    def test_forged_seal_and_extent_refused_before_reader(self):
        self.precharge(); key = ('original', roles()[0]['name'], 'raw'); g, seal = self.io.grants[key]
        receipt = transport.record(g, seal, self.provenance['source_sha256'], self.provenance['configuration_sha256'],
                                   ':'.join(key), dict(author_fabricated=True))
        for field, value in (('grant_sha256', 'f' * 64), ('extent', g['limit'] + 1)):
            bad = dict(receipt); bad[field] = value
            with patch.object(adapter, 'read_spec', side_effect=AssertionError('must not read')) as reader:
                with self.assertRaises(AssertionError): self.io.verify(key, bad)
                reader.assert_not_called()

    def test_durable_file_read_binding_and_failure_record(self):
        value = dict(author_fabricated=True, scientific_admission=False)
        spec = self.io.persist_admission(value); self.assertEqual(self.io.read_admission(spec), value)
        bad = dict(spec, sha256='f' * 64)
        with self.assertRaises(AssertionError): self.io.read_admission(bad)
        self.io.failed(dict(error='prepared', attempted_native_calls=0))
        saved = json.loads((self.budget.root/'failure/controller-flow-failure.json').read_bytes())
        self.assertEqual(saved['unreceipted_constructor_count'], 'UNKNOWN_IF_NATIVE_CHILD_FAILED')
        self.assertEqual(saved['receipted_world_constructors'], 0)


if __name__ == '__main__': unittest.main()
