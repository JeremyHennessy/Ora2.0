import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from experiments import cold_restore as restore
from experiments import cold_restore_audit as audit


class ColdRestoreTests(unittest.TestCase):
    def test_zip_members_cannot_escape(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            root=Path(folder); archive=root/'input.zip'
            with zipfile.ZipFile(archive,'w') as z: z.writestr('runtime/../escape','forged')
            with zipfile.ZipFile(archive) as z:
                with self.assertRaisesRegex(ValueError,'escape'): restore.restore_members(z,'runtime/',root/'restored')
            self.assertFalse((root/'escape').exists())

    def test_wrong_archive_refused_before_output(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            root=Path(folder); bad=root/'bad.zip'; bad.write_bytes(b'forged'); output=root/'output'
            with patch.object(restore,'BACKUP',bad):
                with self.assertRaisesRegex(ValueError,'archive changed'): restore.verify_backup()
            self.assertFalse(output.exists())

    def test_incomplete_evidence_refused(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            with self.assertRaises(OSError): audit.audit(folder,folder,'0'*40)
