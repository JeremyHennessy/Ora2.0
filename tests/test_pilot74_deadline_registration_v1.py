"""Prospective refusal tests, no processes or Worlds."""
import ast,copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import digital_pilot74_deadline_registration_v1 as r
class Deadline(unittest.TestCase):
 def fixture(self):
  child=dict(pid=123,creation_filetime_decimal='456',expected_intervention='original-owner-two-second-deadline',wait_seconds=60)
  before=dict(pid=123,creation_filetime_decimal='456',process_wait=258,pids=[123],observation_errors=[],usage=dict(started_processes=1,active_before_close=1))
  after=dict(pid=123,creation_filetime_decimal='456',process_wait=0,pids=[],observation_errors=[],closure_observed=True,usage=dict(started_processes=1,active_before_close=0))
  e=dict(raw_wait_result=258,wall_limit_ms=2000,started_tick_ms=100,original_deadline_ms=2100,observed_wait_tick_ms=2101,elapsed_at_wait_ms=2001,phase='wait',caller_exit_code=None,command=['pinned'],before_termination=before,after_termination=after,termination_requested=True,owned_identity_snapshot_before_termination=None,owned_identity_snapshot_skipped='absolute deadline exhausted;termination takes precedence')
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
  for key,value in [('raw_wait_result',4294967295),('observed_wait_tick_ms',2099),('elapsed_at_wait_ms',1999),('wall_limit_ms',3000),('original_deadline_ms',2102)]:
   e,c=self.fixture();e[key]=value
   with self.assertRaises(AssertionError):r.verify_deadline(e,c,['pinned'])
 def test_modules_parse(self):
  for name in ['digital_pilot74_deadline_probe_v1.py','digital_pilot74_deadline_registration_v1.py']:
   ast.parse((Path(r.__file__).parent/name).read_bytes())
if __name__=='__main__':unittest.main()
