"""Bounded filesystem regressions; no World or scientific history."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from experiments.evidence_budget import Budget
from experiments.evidence_budget_audit import audit

class StreamingEvidenceAuditTests(unittest.TestCase):
    def test_large_evidence_hash_uses_bounded_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'evidence';limits={'raw':4*1024**2}
            b=Budget(root,limits,limits['raw']);payload=b'0123456789abcdef'*(3*1024**2//16)+b'end'
            with b.create('raw','archive-like.bin') as f:f.write(payload)
            original_open=Path.open;sizes=[]
            class Tracked:
                def __init__(self,stream):self.stream=stream
                def __enter__(self):return self
                def __exit__(self,*args):self.stream.close()
                def read(self,size=-1):
                    if not 0<size<=1024**2:raise AssertionError('unbounded evidence read')
                    sizes.append(size);return self.stream.read(size)
            def opened(path,*args,**kwargs):return Tracked(original_open(path,*args,**kwargs))
            with patch.object(Path,'read_bytes',side_effect=AssertionError('whole-file read')),patch.object(Path,'open',opened):
                result=audit(root,b.snapshot(),limits,limits['raw'])
            self.assertEqual(result['sha256']['raw/archive-like.bin'],hashlib.sha256(payload).hexdigest())
            self.assertEqual(result['logical_bytes'],len(payload));self.assertGreaterEqual(len(sizes),5)

    def test_empty_file_and_reserved_partial_extent_keep_semantics(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'evidence';b=Budget(root,{'raw':16},16)
            with b.create('raw','empty') as f:pass
            with b.create('raw','partial',reserve=10) as f:f.write(b'abc')
            result=audit(root,b.snapshot(),{'raw':16},16)
            self.assertEqual(result['logical_bytes'],3);self.assertEqual(result['reserved_bytes'],10)
            self.assertEqual(result['sha256'],{'raw/empty':hashlib.sha256(b'').hexdigest(),'raw/partial':hashlib.sha256(b'abc').hexdigest()})

    def test_changed_bytes_change_digest_without_changing_accounting(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'evidence';b=Budget(root,{'raw':16},16)
            with b.create('raw','a') as f:f.write(b'abc')
            first=audit(root,b.snapshot(),{'raw':16},16)
            (root/'raw/a').write_bytes(b'abd')
            second=audit(root,b.snapshot(),{'raw':16},16)
            self.assertNotEqual(first['sha256'],second['sha256'])
            self.assertEqual(first['logical_bytes'],second['logical_bytes'])
