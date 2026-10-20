"""New independent receipt rejection fixtures. No native or World creation."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pilot74_physical_fixture',ROOT/'experiments/digital_pilot74_publication_reader_v2.py')
physical=importlib.util.module_from_spec(spec);spec.loader.exec_module(physical)
tree=ast.parse((ROOT/'experiments/digital_pilot74_guardian_v1.py').read_bytes())
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('normalize_native','verify_native')]
ns=dict(physical=physical,MIB=1024**2)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-guardian-receipt-functions','exec'),ns)


class ReceiptConformance(unittest.TestCase):
    def fixture(self,root):
        def limits(memory,cpu,count):
            return dict(memory_bytes=memory*1024**2,cpu_ticks=cpu*10_000_000,processes=count,flags=0x220c)
        start=dict(schema='PILOT74-GUARDIAN-START-v1',root_member=True,child_member=True,
                   pid=42,creation_filetime_decimal='123',command=['python','fixture'],role='new-conformance',
                   source_sha256='a'*64,configuration_sha256='b'*64,
                   root_limits=limits(2048,2400,4),child_limits=limits(1024,180,3))
        path=root/'new-conformance.start.json';path.write_bytes(physical.encode(start))
        s=dict(path=str(path),extent=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        capture=dict(schema='PILOT74-NATIVE-CAPTURE-v2',capture_complete=True,eof=True,errors=[],
                     grant_sha256='c'*64,received_bytes=3,retained_bytes=3,stdout_limit_exceeded=False,
                     raw=dict(path=str(root/'stdout.bin'),extent=3,sha256=hashlib.sha256(b'abc').hexdigest()),
                     overflow=dict(path=str(root/'overflow.bin'),extent=0,sha256=hashlib.sha256(b'').hexdigest()))
        wire=dict(schema='PILOT74-GUARDIAN-NATIVE-v1',command=start['command'],role=start['role'],
                  source_sha256=start['source_sha256'],configuration_sha256=start['configuration_sha256'],
                  elapsed_ms=10,exit_code=0,pid=42,creation_filetime_decimal='123',start=s,
                  stdout_capture=capture,user_cpu_ticks=100,peak_job_memory_bytes=1024**2,
                  active_before_close=0,started_processes=1,post_close_processes_exited=True,timed_out=False)
        return start,wire

    def saved(self,root,wire):
        path=root/'new-conformance.json';path.write_bytes(physical.encode(wire))
        spec=dict(path=str(path),extent=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        slots={}
        for name,path,limit in [('raw/native/new-conformance.json',path,1024**2),
                                ('raw/native/new-conformance.start.json',root/'new-conformance.start.json',65536)]:
            st=path.stat();slots[name]=dict(path=str(path),limit=limit,device=st.st_dev,inode=st.st_ino)
        normalized=ns['normalize_native'](wire);normalized['native_spec']=spec
        return slots,normalized

    def test_valid_complete_native_and_physical_start_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);start,wire=self.fixture(root)
            slots,n=self.saved(root,wire)
            self.assertEqual(ns['verify_native'](slots,'new-conformance',n),n['native_spec'])

    def test_rehashed_wrong_start_birth_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);start,wire=self.fixture(root)
            start['creation_filetime_decimal']='124'
            path=root/'new-conformance.start.json';path.write_bytes(physical.encode(start))
            wire['start'].update(extent=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            slots,n=self.saved(root,wire)
            with self.assertRaises(AssertionError):ns['verify_native'](slots,'new-conformance',n)

    def test_capture_byte_totals_must_match_retained_files(self):
        with tempfile.TemporaryDirectory() as folder:
            _,wire=self.fixture(Path(folder))
            wire['stdout_capture']['received_bytes']=wire['stdout_capture']['retained_bytes']=10
            with self.assertRaises(AssertionError):ns['normalize_native'](wire)

    def test_complete_capture_cannot_hide_output_limit_crossing(self):
        with tempfile.TemporaryDirectory() as folder:
            _,wire=self.fixture(Path(folder));c=wire['stdout_capture']
            c.update(received_bytes=1024**2+1,retained_bytes=1024**2+1)
            c['raw']['extent']=1024**2;c['overflow']['extent']=1
            with self.assertRaises(AssertionError):ns['normalize_native'](wire)

    def test_rehashed_breakaway_limit_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);start,wire=self.fixture(root)
            start['child_limits']['flags']|=0x800
            path=root/'new-conformance.start.json';path.write_bytes(physical.encode(start))
            wire['start'].update(extent=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            slots,n=self.saved(root,wire)
            with self.assertRaises(AssertionError):ns['verify_native'](slots,'new-conformance',n)


if __name__=='__main__':unittest.main()
