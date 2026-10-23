"""Prospective refusal tests, no processes or Worlds."""
import ast,copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import digital_pilot74_reserved_closure_registration_v1 as r
class Deadline(unittest.TestCase):
 def fixture(self):
  child=dict(pid=123,creation_filetime_decimal='456',expected_intervention='original-owner-soft-stop-1750-hard-deadline-2000',wait_seconds=60)
  before=dict(pid=123,creation_filetime_decimal='456',process_wait=258,pids=[123],observation_errors=[],usage=dict(started_processes=1,active_before_close=1))
  after=dict(pid=123,creation_filetime_decimal='456',process_wait=0,pids=[],observation_errors=[],closure_observed=True,usage=dict(started_processes=1,active_before_close=0))
  e=dict(raw_wait_result=258,wall_limit_ms=2000,started_tick_ms=100,original_deadline_ms=2100,observed_wait_tick_ms=1851,elapsed_at_wait_ms=1751,closure_reserve_ms=250,soft_deadline_ms=1850,closure_wait_result=0,caller_signal_within_original_budget=True,closure_within_original_budget=True,closure_observed_tick_ms=1900,full_closure_observed_tick_ms=1901,phase='wait',caller_exit_code=None,command=['pinned'],before_termination=before,after_termination=after,termination_requested=True,owned_identity_snapshot_before_termination=None,owned_identity_snapshot_skipped='soft deadline reached;reserved closure takes precedence')
  return e,child
 def test_valid_exact_shape(self):
  e,c=self.fixture();r.verify_deadline(e,c,['pinned'])
 def test_birth_pid_and_intervention_refused(self):
  for key,value in [('pid',9),('creation_filetime_decimal','999'),('wait_seconds',1),('expected_intervention','different')]:
   e,c=self.fixture();c[key]=value
   with self.assertRaises(AssertionError):r.verify_deadline(e,c,['pinned'])
 def test_unknown_or_active_closure_refused(self):
  for key,value in [('process_wait',258),('pids',[123]),('closure_observed',False),('observation_errors',['unknown'])]:
   e,c=self.fixture();e['after_termination'][key]=value
   with self.assertRaises(AssertionError):r.verify_deadline(e,c,['pinned'])
 def test_extra_processes_refused(self):
  for phase in ['before_termination','after_termination']:
   e,c=self.fixture();e[phase]['usage']['started_processes']=2
   with self.assertRaises(AssertionError):r.verify_deadline(e,c,['pinned'])
 def test_returned_or_wrong_command_refused(self):
  for key,value in [('caller_exit_code',0),('command',['other']),('phase','identity'),('termination_requested',False)]:
   e,c=self.fixture();e[key]=value
   with self.assertRaises(AssertionError):r.verify_deadline(e,c,['pinned'])
 def test_early_unknown_or_changed_timer_refused(self):
  for key,value in [('raw_wait_result',4294967295),('observed_wait_tick_ms',1849),('elapsed_at_wait_ms',1749),('wall_limit_ms',3000),('original_deadline_ms',2102)]:
   e,c=self.fixture();e[key]=value
   with self.assertRaises(AssertionError):r.verify_deadline(e,c,['pinned'])
 def test_late_or_unknown_full_closure_refused(self):
  for key,value in [('full_closure_observed_tick_ms',2101),('closure_wait_result',258),('closure_within_original_budget',False),('caller_signal_within_original_budget',False),('closure_reserve_ms',0)]:
   e,c=self.fixture();e[key]=value
   with self.assertRaises(AssertionError):r.verify_deadline(e,c,['pinned'])
 def test_global_or_wrong_qualification_lock_refused(self):
  root=Path('D:/OraLab/runs/synthetic')
  for path in [r.PRESERVED_LOCK,root/'wrong.lock',root.parent/'qualification-owner.lock']:
   with self.assertRaises(ValueError):r.qualification_lock(root,path)
 def test_valid_qualification_path_does_not_modify_old_lock(self):
  import tempfile
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   parent=Path(d);old=parent/'failed.lock';old.write_bytes(b'original failed evidence');root=parent/'fresh'
   with patch.object(r,'PRESERVED_LOCK',old):
    self.assertEqual(r.qualification_lock(root,root/'qualification-owner.lock'),root/'qualification-owner.lock')
   self.assertEqual(old.read_bytes(),b'original failed evidence');self.assertFalse(root.exists())
 def test_changed_preserved_lock_rejected_at_postflight(self):
  import tempfile
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   old=Path(d)/'failed.lock';old.write_bytes(b'original');spec=r.pin(old);st=old.stat();spec.update(device=st.st_dev,inode=st.st_ino)
   with patch.object(r,'PRESERVED_LOCK',old):
    r.preserved_failure_check(spec);old.write_bytes(b'changed')
    with self.assertRaises(AssertionError):r.preserved_failure_check(spec)
 def test_modules_parse(self):
  for name in ['digital_pilot74_reserved_closure_probe_v1.py','digital_pilot74_reserved_closure_registration_v1.py']:
   ast.parse((Path(r.__file__).parent/name).read_bytes())
if __name__=='__main__':unittest.main()
