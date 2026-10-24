"""Synthetic metadata/algebra only; no source imports or organism execution."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import eka1_prospective_opportunity as q

def row(tick=100,actor=2):
 return dict(tick=tick,actor=actor,born=True,ordinary_mutating_ancestry=True,feedback=1,forage=dict(tick=tick-1,packet=64,site=0,port=0,success=1),pre_state_sha256='a'*64)

class Prospective(unittest.TestCase):
 def test_first_opportunity_not_first_mutant(self):
  a=row(100,2);a['forage']['packet']=1;b=row(120,10)
  r=q.select_first([a,b]);self.assertEqual(r['selected']['actor'],10);self.assertFalse(r['execution_authorized'])
 def test_no_replacement_after_selection(self):
  a=row();b=row(110,20);r=q.select_first([a,b]);self.assertEqual(r['selected']['actor'],2)
 def test_no_eligible_preserves_actual_world_outcomes(self):
  r=q.select_first([]);self.assertIsNone(r['selected']);self.assertEqual(r['opportunity_contrast_weight'],0);self.assertFalse(r['actual_world_outcomes_zeroed'])
 def test_empty_latest_attempt_overwrites_prior_meal(self):
  a=row();a['feedback']=0;a['forage'].update(packet=None,success=0);self.assertIsNone(q.select_first([a])['selected'])
 def test_pre_read_phase_limit_and_no_fitness_filters(self):
  a=row(2048);self.assertIsNone(q.select_first([a])['selected'])
  a=row();a['fitness']=99
  with self.assertRaises(ValueError):q.select_first([a])
 def test_unknown_or_initial_provenance_refused_or_unavailable(self):
  a=row();a['forage']=None;a['feedback']=0;self.assertIsNone(q.select_first([a])['selected'])
  a['feedback']=1
  with self.assertRaises(ValueError):q.select_first([a])
 def test_ancestry_is_eligibility_not_authentication(self):
  a=row();a['ordinary_mutating_ancestry']=False;self.assertIsNone(q.select_first([a])['selected'])
  self.assertFalse(q.select_first([row()])['original_history_authenticated'])
 def test_all_feedback_port_cases_identify_actual_target(self):
  for target in [0,1]:
   for port in [0,1]:self.assertEqual(q.observer_target(port,int(port==target)),target)
 def test_symbolic_site_phase_identity(self):
  e=row()['forage']
  self.assertFalse(q.conditional_relation(e,dict(tick=150,packet=64,site=0))['common_world_authenticated'])
  for packet in [64,65,1000]:self.assertEqual(q.conditional_relation(e,dict(tick=150,packet=packet,site=0))['target_identity'],'EQUAL_IF_COMMON_WORLD')
 def test_cross_site_stock_phase_and_empty_are_retained_unknown(self):
  e=row()['forage']
  for p in [dict(tick=150,packet=64,site=1),dict(tick=150,packet=1,site=0),dict(tick=2048,packet=64,site=0),dict(tick=150,packet=None,site=0)]:
   r=q.conditional_relation(e,p);self.assertEqual(r['target_identity'],'UNKNOWN');self.assertFalse(r['discard_outcome'])
 def test_order_alias_and_boolean_type(self):
  a=row();saved=copy.deepcopy(a);q.select_first([a]);self.assertEqual(a,saved)
  with self.assertRaises(ValueError):q.select_first([row(100),row(99)])
  a['feedback']=True
  with self.assertRaises(ValueError):q.select_first([a])
 def test_contradictory_feedback_and_posttreatment_fields_refused(self):
  a=row();a['forage']['success']=0
  with self.assertRaises(ValueError):q.select_first([a])
  a=row();a['probe_site']=0
  with self.assertRaises(ValueError):q.select_first([a])
if __name__=='__main__':unittest.main()
