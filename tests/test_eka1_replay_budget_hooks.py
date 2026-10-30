"""NEW offline ledger and AST checks; replay modules are never imported."""
import ast
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('budget_ledger_new_checks', ROOT/'tools/eka1_cumulative_reservations.py')
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class ReplayBudgetChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.path = Path(self.tmp.name)/'new.jsonl'
        self.fd = os.open(self.path, os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_BINARY, 0o600)
        self.budget = ledger.Reservations(self.fd)
        self.budget.role(1, 0)
        self.budget.genesis(1, 0)

    def tearDown(self):
        self.budget.close(); os.close(self.fd); self.tmp.cleanup()

    def test_full_block_burns_on_later_failure(self):
        self.budget.dispatches(1, 0, 4096)
        # No simulated World call: a later failure must not return this credit.
        raw = self.path.read_bytes()
        with self.assertRaises(ValueError): self.budget.dispatch(1, 0)
        self.assertEqual(raw, self.path.read_bytes())

    def test_mixed_blocks_cannot_exceed_cap(self):
        self.budget.dispatch(1, 0)
        self.budget.dispatches(1, 0, 4094)
        with self.assertRaises(ValueError): self.budget.dispatches(1, 0, 2)
        self.budget.dispatch(1, 0)
        with self.assertRaises(ValueError): self.budget.dispatch(1, 0)

    def test_invalid_counts_do_not_write(self):
        raw = self.path.read_bytes()
        for count in (0, -1, 4097, True, 1.0, '4096'):
            with self.assertRaises(ValueError): self.budget.dispatches(1, 0, count)
        self.assertEqual(raw, self.path.read_bytes())

    def test_block_fsync_failure_poison_retains_record(self):
        with patch.object(ledger.os, 'fsync', side_effect=OSError('synthetic sync failure')):
            with self.assertRaises(OSError): self.budget.dispatches(1, 0, 4096)
        raw = self.path.read_bytes()
        self.assertIn(b'"count":4096', raw)
        with self.assertRaises(RuntimeError): self.budget.dispatch(1, 0)
        self.assertEqual(raw, self.path.read_bytes())

    def test_replay_AST_mandatory_precharge_before_runtime(self):
        for filename, target, runtime in (
            ('digital_eka1_selection_replay_v1.py', 'replay_original_selection', 'metadata_inputs'),
            ('digital_eka1_derived_reconstruction_v1.py', 'reconstruct_and_verify', 'runtime_sources')):
            tree = ast.parse((ROOT/'experiments'/filename).read_bytes())
            fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == target)
            self.assertEqual([n.arg for n in fn.args.kwonlyargs], ['reservations', 'genesis_index', 'owner'])
            self.assertEqual(fn.args.kw_defaults, [None, None, None])
            calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)]
            debit = next(n for n in calls if isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'owner' and n.func.attr == 'replay')
            load = next(n for n in calls if isinstance(n.func, ast.Name) and n.func.id == runtime)
            self.assertLess(debit.lineno, load.lineno)
            self.assertFalse(any(isinstance(n, ast.Try) for n in fn.body[:next(i for i, n in enumerate(fn.body) if n.lineno >= load.lineno)+1]))
            self.assertIn("type(reservations) is not Reservations", ast.unparse(fn))
            self.assertIn("type(owner) is not owner_class()", ast.unparse(fn))
            self.assertNotIn('stop_tick', [k.arg for k in debit.keywords])
            self.assertIn('request', [k.arg for k in debit.keywords])

    def test_selection_raw_dependency_pin_matches(self):
        tree = ast.parse((ROOT/'experiments/digital_eka1_selection_replay_v1.py').read_bytes())
        pins = ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'INPUT_PINS' for t in n.targets)))
        name = 'experiments/digital_eka1_derived_reconstruction_v1.py'
        self.assertEqual(pins[name], hashlib.sha256((ROOT/name).read_bytes()).hexdigest())


if __name__ == '__main__': unittest.main()
