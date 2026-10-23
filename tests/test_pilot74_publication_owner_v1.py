"""New owner-body tests; no publication writes, native role or World replay."""
import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import digital_pilot74_publication_v2 as p
from experiments import digital_pilot74_guardian_v1 as g

class Kernel:
 def __init__(self,wait=258):self.wait=wait;self.closed=False
 def OpenProcess(self,*args):return 1
 def WaitForSingleObject(self,*args):return self.wait
 def CloseHandle(self,*args):self.closed=True;return True

class Owners(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
 def tearDown(self):self.tmp.cleanup()
 def grant(self,body):
  path=self.root/'qualification-owner.lock';raw=p.enc(body);path.write_bytes(raw);i=path.stat()
  return dict(operator_lock=dict(path=str(path),extent=len(raw),sha256=hashlib.sha256(raw).hexdigest(),device=i.st_dev,inode=i.st_ino))
 def body(self):return dict(schema='PILOT74-QUALIFICATION-OWNER-LOCK-v1',pid=123,creation_filetime_decimal='456')
 def check(self,grant,birth=456,wait=258,allowed=True):
  kernel=Kernel(wait)
  with patch.object(p,'allowed_owner_lock',return_value=allowed),patch.object(g,'_kernel',return_value=kernel),patch.object(g,'_birth',return_value=birth):p.owner(grant)
  self.assertTrue(kernel.closed)
 def test_exact_live_qualification_body(self):self.check(self.grant(self.body()))
 def test_native_bound_scope_still_required(self):
  with self.assertRaises(AssertionError):self.check(self.grant(self.body()),allowed=False)
 def test_legacy_body_not_accepted_as_qualification(self):
  with self.assertRaises(AssertionError):self.check(self.grant(dict(pid=123,started_utc='fixture')))
 def production(self,body):
  raw=p.enc(body);grant=dict(operator_lock=dict(path='D:/OraLab/state/operator.lock',extent=len(raw),sha256=hashlib.sha256(raw).hexdigest(),device=1,inode=2))
  with patch.object(p,'read_slot',return_value=raw):p.owner(grant)
 def test_existing_production_body_unchanged(self):self.production(dict(pid=123,started_utc='fixture'))
 def test_qualification_body_cannot_replace_production_body(self):
  with self.assertRaises(AssertionError):self.production(self.body())
 def test_wrong_birth_refused_and_handle_closed(self):
  grant=self.grant(self.body());kernel=Kernel()
  with patch.object(p,'allowed_owner_lock',return_value=True),patch.object(g,'_kernel',return_value=kernel),patch.object(g,'_birth',return_value=457):
   with self.assertRaises(AssertionError):p.owner(grant)
  self.assertTrue(kernel.closed)
 def test_exited_owner_refused(self):
  with self.assertRaises(AssertionError):self.check(self.grant(self.body()),wait=0)
 def test_noncanonical_birth_refused(self):
  body=self.body();body['creation_filetime_decimal']='0456'
  with self.assertRaises(AssertionError):self.check(self.grant(body))
 def test_unexpected_body_field_refused(self):
  body=self.body();body['started_utc']='fixture'
  with self.assertRaises(AssertionError):self.check(self.grant(body))
 def test_tampered_lock_hash_refused(self):
  grant=self.grant(self.body());grant['operator_lock']['sha256']='0'*64
  with self.assertRaises(AssertionError):self.check(grant)
 @unittest.skipUnless(os.name=='nt','Actual Windows process identity')
 def test_real_current_owner_birth(self):
  k=g._kernel();handle=k.OpenProcess(0x1000|0x100000,False,os.getpid());g.checked(handle)
  try:birth=g._birth(k,handle)
  finally:g.checked(k.CloseHandle(handle))
  grant=self.grant(dict(schema='PILOT74-QUALIFICATION-OWNER-LOCK-v1',pid=os.getpid(),creation_filetime_decimal=str(birth)))
  with patch.object(p,'allowed_owner_lock',return_value=True):p.owner(grant)

if __name__=='__main__':unittest.main()
