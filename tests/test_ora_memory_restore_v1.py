"""Restore refuses rollback, unfinished snapshots and active owners."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from experiments.ora_task_store_v1 import Store
from experiments.ora_memory_restore_v1 import restore


class Restore(unittest.TestCase):
    def setup_snapshot(self,root,pending=False):
        with Store(root) as store:
            store.submit(1,'remember','fixture','retained')
            if not pending: store.complete(store.claim())
            store.backup(root/'backups')
        snapshot=root/'backups/snapshot-0.sqlite3'
        return snapshot,hashlib.sha256(snapshot.read_bytes()).hexdigest()

    def test_corrupt_primary_restores_only_matching_complete_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); snapshot,digest=self.setup_snapshot(root)
            (root/'memory.sqlite3').write_bytes(b'disclosed corruption fixture')
            result=restore(root,snapshot,digest,1)
            self.assertFalse(result['automatic'])
            self.assertEqual((root/'memory.corrupt.sqlite3').read_bytes(),b'disclosed corruption fixture')
            with Store(root) as store:
                store.submit(2,'recall','fixture')
                self.assertEqual(store.complete(store.claim()),'retained')

    def test_old_cursor_or_pending_snapshot_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); snapshot,digest=self.setup_snapshot(root,pending=True)
            with self.assertRaises(ValueError): restore(root,snapshot,digest,1)
            with self.assertRaises(ValueError): restore(root,snapshot,digest,2)

    def test_healthy_or_active_primary_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); snapshot,digest=self.setup_snapshot(root)
            with self.assertRaises(ValueError): restore(root,snapshot,digest,1)
            with Store(root):
                with self.assertRaises(OSError): restore(root,snapshot,digest,1)

    def test_newer_mailbox_and_bad_digest_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); snapshot,digest=self.setup_snapshot(root)
            (root/'memory.sqlite3').write_bytes(b'corrupt')
            (root/'inbox.json').write_text(json.dumps([dict(sequence=2,kind='recall',key='fixture',value='')]))
            with self.assertRaises(ValueError): restore(root,snapshot,digest,1)
            with self.assertRaises(ValueError): restore(root,snapshot,'0'*64,1)
            self.assertEqual((root/'memory.sqlite3').read_bytes(),b'corrupt')

    def test_unreconciled_journal_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); snapshot,digest=self.setup_snapshot(root)
            (root/'memory.sqlite3').write_bytes(b'corrupt')
            (root/'memory.sqlite3-journal').write_bytes(b'unreconciled transaction')
            with self.assertRaises(ValueError): restore(root,snapshot,digest,1)
            self.assertEqual((root/'memory.sqlite3-journal').read_bytes(),b'unreconciled transaction')


if __name__=='__main__': unittest.main()
