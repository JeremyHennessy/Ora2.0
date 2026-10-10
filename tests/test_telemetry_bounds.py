import hashlib
import io
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

    def test_aggregate_and_entry_bounds_refuse_before_reading(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder)
            for i in range(3):(path/str(i)).write_bytes(b'123')
            with patch.object(reader,'HASH_TOTAL_BYTES',8),patch.object(Path,'open',side_effect=AssertionError('Preflight bypass')):
                with self.assertRaises(ValueError):reader.hashes(path)
            with patch.object(reader,'HASH_ENTRIES',2),patch.object(Path,'open',side_effect=AssertionError('Preflight bypass')):
                with self.assertRaises(ValueError):reader.hashes(path)

    def test_growth_during_streaming_is_bounded(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder)/'note.txt';path.write_bytes(b'x')
            with patch.object(reader,'HASH_FILE_BYTES',3),patch.object(Path,'open',return_value=io.BytesIO(b'1234')):
                with self.assertRaises(ValueError):reader.hashes(folder)
