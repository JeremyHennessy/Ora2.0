import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from experiments import world_telemetry as reader


class BoundsTests(unittest.TestCase):
    def test_oversized_manifest_rejected_before_content_open(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder)/'manifest.json';path.write_bytes(b'{}')
            native=Path.stat
            def size(p,*args,**kwargs):
                value=native(p,*args,**kwargs)
                if p==path:return SimpleNamespace(st_size=4*1024**2+1,st_mode=value.st_mode,st_file_attributes=getattr(value,'st_file_attributes',0),st_nlink=1)
                return value
            with patch.object(Path,'stat',size),patch.object(Path,'open',side_effect=AssertionError('Oversized evidence was opened')):
                with self.assertRaises(ValueError):reader.hashes(folder)

    def test_valid_checksums_keep_all_files_except_writer_lock(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder)
            for name,data in [('manifest.json',b'{}'),('frames.jsonl',b'frame\n'),('writer.lock',b'L'),('note.txt',b'raw')]:
                (path/name).write_bytes(data)
            before={p.name:p.read_bytes() for p in path.iterdir()}
            expected={name:hashlib.sha256(data).hexdigest() for name,data in before.items() if name!='writer.lock'}
            self.assertEqual(reader.hashes(path),expected)
            self.assertEqual(before,{p.name:p.read_bytes() for p in path.iterdir()})
