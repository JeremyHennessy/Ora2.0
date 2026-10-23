"""New mocked reserve policy only; no native execution."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_pilot74_outer_owner_v1 as base
REQUEST=base.REQUEST
from experiments import digital_pilot74_outer_owner_v1 as o
class Reserve(base.Outer):
 def test_reserved_timeout_waits_only_until_original_deadline(self):
  k,j=self.setup_boundary();k.GetTickCount64.side_effect=[100,101,102,103,104,1850,1851,1852,1900,1901]
  k.WaitForSingleObject.side_effect=[258,258,0,0]
  def invoke(*args):
   with patch.dict(REQUEST,wall_ms=2000,closure_reserve_ms=250):return self.invoke(k,j)
  with self.assertRaises(TimeoutError) as raised:invoke()
  e=raised.exception.guardian_failure_evidence
  self.assertEqual(e['original_deadline_ms'],2100);self.assertEqual(e['soft_deadline_ms'],1850)
  self.assertEqual(e['raw_wait_result'],258);self.assertEqual(e['closure_wait_result'],0)
  self.assertEqual(e['closure_observed_tick_ms'],1900);self.assertTrue(e['closure_within_original_budget'])
  self.assertIn(((222,248),),[tuple([c.args]) for c in k.WaitForSingleObject.call_args_list])
 def test_late_signaling_cannot_claim_budget_pass(self):
  k,j=self.setup_boundary();k.GetTickCount64.side_effect=[100,101,102,103,104,1850,1851,1852,2101,2102]
  k.WaitForSingleObject.side_effect=[258,258,0,0]
  with patch.dict(REQUEST,wall_ms=2000,closure_reserve_ms=250):
   with self.assertRaises(TimeoutError) as raised:self.invoke(k,j)
  e=raised.exception.guardian_failure_evidence
  self.assertFalse(e['closure_within_original_budget']);self.assertEqual(e['closure_observed_tick_ms'],2101)
 def test_full_job_query_past_deadline_cannot_pass(self):
  k,j=self.setup_boundary();k.GetTickCount64.side_effect=[100,101,102,103,104,1850,1851,1852,1900,2101]
  k.WaitForSingleObject.side_effect=[258,258,0,0]
  with patch.dict(REQUEST,wall_ms=2000,closure_reserve_ms=250):
   with self.assertRaises(TimeoutError) as raised:self.invoke(k,j,snapshot_error=AssertionError('optional snapshot must be skipped'))
  e=raised.exception.guardian_failure_evidence
  self.assertTrue(e['caller_signal_within_original_budget']);self.assertFalse(e['closure_within_original_budget'])
  self.assertEqual(e['full_closure_observed_tick_ms'],2101)
 def test_invalid_reserve_refused_before_admission(self):
  for value in [True,-1,2000,2001]:
   k,j=self.setup_boundary()
   with patch.dict(REQUEST,wall_ms=2000,closure_reserve_ms=value):
    with self.assertRaises(ValueError):self.invoke(k,j)
   k.CreateProcessW.assert_not_called()
if __name__=='__main__':unittest.main()
