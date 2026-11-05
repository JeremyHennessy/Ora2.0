"""NEW offline synthetic counter/custody checks. No World or native launcher."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reservations', ROOT/'tools/eka1_cumulative_reservations.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LedgerChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.path = Path(self.tmp.name)/'new.jsonl'
        self.fd = os.open(self.path, os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_BINARY, 0o600)
        self.ledger = module.Reservations(self.fd)

    def tearDown(self):
        self.ledger.close()
        os.close(self.fd)
        self.tmp.cleanup()

    def test_duplicate_role_and_failed_attempt_never_refunded(self):
        self.ledger.role(1, 0)
        self.ledger.process_birth(1, 0)  # Later spawn failure does not refund.
        with self.assertRaises(ValueError): self.ledger.role(1, 0)
        for _ in range(55): self.ledger.process_birth(1, 0)
        with self.assertRaises(ValueError): self.ledger.process_birth(1, 0)

    def test_both_strata_and_genesis_ceiling(self):
        for dose in (1, 8):
            self.ledger.role(dose, 0)
            for index in range(32): self.ledger.genesis(dose, index)
            with self.assertRaises(ValueError): self.ledger.genesis(dose, 31)
            with self.assertRaises(ValueError): self.ledger.genesis(dose, 32)

    def test_dispatch_ceiling_and_unreserved_rejection(self):
        with self.assertRaises(ValueError): self.ledger.dispatch(1, 0)
        self.ledger.role(1, 0); self.ledger.genesis(1, 0)
        # Synthetic file-write checks, not 4096 actual VM dispatches.
        with patch.object(module.os, 'fsync'):
            for _ in range(4096): self.ledger.dispatch(1, 0)
        with self.assertRaises(ValueError): self.ledger.dispatch(1, 0)

    def test_exact_types_and_missing_role(self):
        for dose in (True, 2, '1'):
            with self.assertRaises(ValueError): self.ledger.role(dose, 0)
        with self.assertRaises(ValueError): self.ledger.role(1, True)
        with self.assertRaises(ValueError): self.ledger.process_birth(1, 0)

    def test_short_write_preserves_partial_and_poison(self):
        original = os.write
        def short(fd, raw): return original(fd, raw[:7])
        with patch.object(module.os, 'write', side_effect=short):
            with self.assertRaises(OSError): self.ledger.role(1, 0)
        partial = self.path.read_bytes()
        self.assertEqual(len(partial), 7)
        with self.assertRaises(RuntimeError): self.ledger.role(1, 0)
        self.assertEqual(self.path.read_bytes(), partial)

    def test_fsync_failure_preserves_record_and_poison(self):
        with patch.object(module.os, 'fsync', side_effect=OSError('synthetic fsync failure')):
            with self.assertRaises(OSError): self.ledger.role(1, 0)
        raw = self.path.read_bytes(); self.assertTrue(raw.endswith(b'\n'))
        with self.assertRaises(RuntimeError): self.ledger.role(8, 0)
        self.assertEqual(raw, self.path.read_bytes())

    def test_chain_close_and_nonempty_restart_refusal(self):
        self.ledger.role(1, 0); self.ledger.genesis(1, 0)
        previous = '0'*64
        for seq, raw in enumerate(self.path.read_bytes().splitlines(keepends=True)):
            row = json.loads(raw)
            self.assertEqual(row['sequence'], seq)
            self.assertEqual(row['previous_sha256'], previous)
            self.assertIs(row['execution_authenticated'], False)
            previous = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError): module.Reservations(self.fd)
        self.ledger.close()
        with self.assertRaises(RuntimeError): self.ledger.role(8, 0)

    def test_external_extent_change_refuses_without_overwrite(self):
        os.write(self.fd, b'external')
        with self.assertRaises(OSError): self.ledger.role(1, 0)
        self.assertEqual(self.path.read_bytes(), b'external')


if __name__ == '__main__': unittest.main()
