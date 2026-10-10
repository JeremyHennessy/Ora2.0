"""Partial-success backend faults must not acknowledge authoritative records."""
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
from dataclasses import asdict
from experiments import checkpoint_pilot as worker
from experiments import chemical_calibration as cal


class ShortWriteBackend:
    def __init__(self, handle):
        self.handle=handle

    def __enter__(self):
        return self

    def __exit__(self,*args):
        return self.handle.__exit__(*args)

    def write(self, raw):
        # Store real partial bytes, rather than only forging a return count.
        return self.handle.write(raw[:len(raw)//2])

    def __getattr__(self,name):
        return getattr(self.handle,name)


class RuntimeShortWriteTests(unittest.TestCase):
    def inject(self, mode):
        original=Path.open
        def open_file(path, requested='r', *args, **kwargs):
            handle=original(path,requested,*args,**kwargs)
            return ShortWriteBackend(handle) if requested==mode else handle
        return patch.object(Path,'open',open_file)

    def test_checkpoint_short_write_preserves_previous_committed_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'checkpoint.json'
            worker.atomic_json(path,{'committed':'prior'})
            prior=path.read_bytes()
            with self.inject('xb'):
                with self.assertRaisesRegex(OSError,'Incomplete authoritative write'):
                    worker.atomic_json(path,{'replacement':'not committed'})
            self.assertEqual(path.read_bytes(),prior)
            self.assertEqual(list(path.parent.glob('checkpoint.json.tmp-*')),[])

    def test_journal_short_write_preserves_checkpoint_and_rejects_tail(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            identity=worker.make_identity(1000,'intact',12,4,'a'*40)
            manifest=worker.begin_run(root,identity)
            checkpoint=(root/'checkpoint.json').read_bytes()
            state,rng,mass=worker.initial_state(identity)
            cal.tick(state,rng,cal.Protocol(),'intact',mass)
            with self.inject('ab'):
                with self.assertRaisesRegex(OSError,'Incomplete authoritative write'):
                    worker.record_step(root,manifest,state,rng,worker.ZERO_HASH)
            self.assertEqual((root/'checkpoint.json').read_bytes(),checkpoint)
            self.assertFalse((root/'receipt.json').exists())
            broken=(root/'journal.jsonl').read_bytes()
            self.assertGreater(len(broken),0)
            self.assertFalse(broken.endswith(b'\n'))
            with self.assertRaisesRegex(worker.IntegrityError,'Truncated journal tail'):
                worker.restored(root,identity,full_verify=True)
            self.assertEqual((root/'journal.jsonl').read_bytes(),broken)
