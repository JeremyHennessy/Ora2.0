"""Invented fixtures only: late causal channels and whole paid admission."""
import copy, unittest
from experiments.digital_latehistory78_world import World, PROGRAMS, h
from experiments.digital_latehistory78_history import history
from experiments.digital_latehistory78_source import SOFTWARE
from experiments.digital_latehistory78_referee import audit
from experiments.digital_latehistory78_controls import Control

class LateHistory(unittest.TestCase):
 def test_all_maps_paid_cut_boundary_and_full_literal_replay(self):
  for seed in SOFTWARE:
   for arm in ('intact','late_erasure','late_misbound'):
    row=history(seed,'supplied_cognitive',arm)
    proof=audit(row,PROGRAMS['supplied_cognitive'],software=True)
    self.assertTrue(proof['completed']);self.assertEqual(proof['deaths'],0)
    onset=next(e for e in row['final']['events'] if e['control']['onset'])
    self.assertEqual(onset['sensor_packet'],20);self.assertEqual(onset['after']['energy'],156)
    self.assertEqual(len([e for e in row['final']['events'] if 'attempt' in e]),32)
    self.assertEqual(proof['formation_cost']+proof['startup_cost'],84)
 def test_independently_generated_warm_physics_equal(self):
  rows=[history(SOFTWARE[2],'supplied_cognitive',a) for a in ('intact','late_erasure','late_misbound')]
  prefixes=[]
  for row in rows:
   events=[]
   for e in row['final']['events']:
    if e['control']['onset']:break
    self.assertEqual(e['control']['rewrites'],[])
    events.append({k:v for k,v in e.items() if k not in ('control','state_hash')})
   prefixes.append(events)
  self.assertEqual(prefixes[0],prefixes[1]);self.assertEqual(prefixes[0],prefixes[2])
 def test_erasure_before_load_and_truthful_channels(self):
  row=history(SOFTWARE[6],'supplied_cognitive','late_erasure')
  events=row['final']['events'];cut=next(i for i,e in enumerate(events) if e['control']['onset'])
  self.assertEqual(events[cut]['after']['memory'][:2],[0,0])
  self.assertEqual(events[cut+1]['decoded'][0],19)
  for e in events[cut:]:
   if 'after' in e and e['decoded'][0] in (0,20):self.assertEqual(e['after']['memory'][:2],[0,0])
   for rewrite in e['control']['rewrites']:self.assertEqual(rewrite['original'][2:],rewrite['value'][2:])
  audit(row,PROGRAMS['supplied_cognitive'],software=True)
 def test_misbinding_swaps_once_and_preserves_nonhistory(self):
  state=dict(r=[0,1],m=[0,15,2,3,4,5,6,7],pc=0,feedback=1)
  c=Control(PROGRAMS['supplied_cognitive'],state,'late_misbound',SOFTWARE[2])
  after=copy.deepcopy(state);after['r'][1]=1;after['pc']=1
  result,ann=c.apply(state,after,1,20)
  self.assertEqual(result['m'][:2],[15,0]);self.assertEqual(ann['onset'],1)
  self.assertEqual({k:v for k,v in result.items() if k!='m'},{k:v for k,v in after.items() if k!='m'})
  again=copy.deepcopy(result);again['pc']=0
  result2,ann2=c.apply(again,again,1,21)
  self.assertEqual(result2,again);self.assertEqual(ann2['onset'],0)
 def test_invariant_misbinding_maps_retained(self):
  state=dict(r=[0,0],m=[15,15,0,0,0,0,0,0],pc=0,feedback=1)
  c=Control(PROGRAMS['supplied_cognitive'],state,'late_misbound',SOFTWARE[0])
  result,ann=c.apply(state,state,0,20)
  self.assertEqual(result,state);self.assertEqual(ann['rewrites'],[]);self.assertEqual(ann['active'],1)
 def test_referee_rejects_lesion_and_energy_forgery(self):
  row=history(SOFTWARE[2],'supplied_cognitive','late_misbound')
  for key in ('active','onset'):
   altered=copy.deepcopy(row);e=next(e for e in altered['final']['events'] if e['control']['onset'])
   e['control'][key]=0;altered['hash']=h(altered['final'])
   with self.assertRaises(AssertionError):audit(altered,PROGRAMS['supplied_cognitive'],software=True)
  altered=copy.deepcopy(row);e=next(e for e in altered['final']['events'] if 'packet_outflow' in e)
  e['packet_outflow']['captured']+=1;altered['hash']=h(altered['final'])
  with self.assertRaises(AssertionError):audit(altered,PROGRAMS['supplied_cognitive'],software=True)
 def test_cap_is_shared_and_every_gain_has_paid_packet(self):
  for route in PROGRAMS:
   row=history(SOFTWARE[0],route,'intact');audit(row,PROGRAMS[route],software=True)
   for e in row['final']['events']:
    if 'after' in e:self.assertLessEqual(e['after']['energy'],160)
    if 'packet_outflow' in e:self.assertEqual(e['packet_outflow']['captured']+e['packet_outflow']['heat'],20)
 def test_source_equal_to_closed_disclosed_programme(self):
  from experiments.digital_oneshot77_source import programmes
  self.assertEqual(PROGRAMS,programmes())
  self.assertTrue(all(len(p)==12 for p in PROGRAMS.values()))

if __name__=='__main__':unittest.main()
