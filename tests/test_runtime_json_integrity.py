"""Ambiguous authoritative JSON must fail closed without rewriting evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from experiments import checkpoint_pilot as worker


class RuntimeJSONIntegrityTests(unittest.TestCase):
    def fixture(self, root):
        return worker.run_pilot(root, seed=1000, variant='intact', steps=4,
                                checkpoint_every=2, revision='a'*40)

    def test_duplicate_fields_rejected_without_mutation(self):
        # First conflicting value is ignored by ordinary json.loads; the final
        # value and all existing digests remain intact. Test nested objects too.
        cases = [('manifest.json', 'seed'), ('manifest.json', 'body'),
                 ('checkpoint.json', 'step'), ('checkpoint.json', 'sha256'),
                 ('receipt.json', 'final_step'), ('journal.jsonl', 'step'),
                 ('journal.jsonl', 'state'), ('journal.jsonl', 'sha256')]
        for filename, key in cases:
            with self.subTest(filename=filename, key=key), tempfile.TemporaryDirectory() as td:
                root=Path(td); self.fixture(root)
                path=root/filename; raw=path.read_bytes()
                token=('"'+key+'":').encode()
                corrupted=raw.replace(token, token+b'null,'+token, 1)
                self.assertNotEqual(raw, corrupted)
                path.write_bytes(corrupted)
                before={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()}
                with self.assertRaisesRegex(worker.IntegrityError, 'invalid JSON|Invalid journal JSON'):
                    worker.run_pilot(root, seed=1000, variant='intact', steps=4,
                                     checkpoint_every=2, revision='a'*40, verify_only=True)
                self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir() if p.is_file()})

    def test_valid_completed_history_remains_exactly_replayable(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); result=self.fixture(root)
            before={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()}
            checked=worker.run_pilot(root, seed=1000, variant='intact', steps=4,
                                    checkpoint_every=2, revision='a'*40, verify_only=True)
            self.assertEqual(result,checked)
            self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir() if p.is_file()})


if __name__=='__main__': unittest.main()
