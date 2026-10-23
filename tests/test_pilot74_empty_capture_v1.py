"""New data/transport regressions only; no guardian launch, World or role replay."""
import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import digital_pilot74_guardian_v1 as g
from experiments import digital_pilot74_publication_reader_v2 as p

class EmptyCapture(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
 def tearDown(self):self.tmp.cleanup()
 def pin(self,name,raw):
  path=self.root/name;path.write_bytes(raw)
  return dict(path=str(path),extent=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 def test_empty_capture_is_authenticated(self):
  self.assertEqual(g.captured_output(self.pin('empty.bin',b'')),b'')
 def test_nonempty_capture_keeps_exact_bytes(self):
  raw=b'{"ok":true}\n';self.assertEqual(g.captured_output(self.pin('out.bin',raw)),raw)
 def test_empty_proof_document_is_still_refused(self):
  with self.assertRaises(AssertionError):p.external(self.pin('proof.json',b''),65536)
 def test_wrong_empty_hash_refused(self):
  spec=self.pin('empty.bin',b'');spec['sha256']='0'*64
  with self.assertRaises(AssertionError):g.captured_output(spec)
 def test_nonempty_file_claimed_empty_refused(self):
  spec=self.pin('out.bin',b'x');spec['extent']=0
  with self.assertRaises(AssertionError):g.captured_output(spec)
 def test_missing_file_refused(self):
  spec=self.pin('empty.bin',b'');Path(spec['path']).unlink()
  with self.assertRaises(FileNotFoundError):g.captured_output(spec)
 def test_hard_link_refused(self):
  spec=self.pin('empty.bin',b'');os.link(spec['path'],self.root/'other.bin')
  with self.assertRaises(AssertionError):g.captured_output(spec)
 def test_client_retains_exit78_and_empty_output(self):
  raw=self.pin('empty.bin',b'');seal='a'*64;source='b'*64;config='c'*64;command=['fixture-only']
  capture=dict(schema='PILOT74-NATIVE-CAPTURE-v2',capture_complete=True,eof=True,errors=[],grant_sha256=seal,overflow=raw,raw=raw,received_bytes=0,retained_bytes=0,stdout_limit_exceeded=False)
  wire=dict(schema='PILOT74-GUARDIAN-NATIVE-v1',command=command,source_sha256=source,configuration_sha256=config,role='crash/fixture',start=dict(path=str(self.root/'start.json'),extent=1,sha256='d'*64),stdout_capture=capture,pid=1,creation_filetime_decimal='1',user_cpu_ticks=0,elapsed_ms=1,exit_code=78,active_before_close=0,started_processes=1,peak_job_memory_bytes=1,post_close_processes_exited=True,timed_out=False)
  native=self.pin('native.json',p.encode(wire));client=g.Client.__new__(g.Client)
  client.is_ready=True;client.archiving=False;client.ordinal=0;client.results={};client.r=dict(source_sha256=source,configuration_sha256=config)
  client.exchange=lambda *args,**kwargs:dict(schema='PILOT74-GUARDIAN-ROLE-RESULT-v1',ordinal=0,role='crash/fixture',native=native)
  limits=SimpleNamespace(memory_bytes=1024*g.MIB,cpu_seconds=180,processes=3,wall_seconds=300)
  result=client.run(command,limits,self.root,capture_grant={},capture_seal=seal,source_sha256=source,configuration_sha256=config,role='crash/fixture',request={})
  self.assertEqual(result['exit_code'],78);self.assertEqual(result['output'],'');self.assertEqual(client.ordinal,1)

if __name__=='__main__':unittest.main()
