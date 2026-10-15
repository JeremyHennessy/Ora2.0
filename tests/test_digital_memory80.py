"""Invented software fixtures only; no primary seeds or scientific claim."""
import copy,unittest
from unittest.mock import patch
from experiments.digital_memory80 import World,programme,SOFTWARE
from experiments.digital_memory80_endpoint import paid_viable_children
class Memory80(unittest.TestCase):
 def test_paid_header_footprint_and_software_seed_boundary(self):
  for q in (2,4,8):
   w=World(SOFTWARE[0],q);self.assertEqual(len(w.entities[0]['memory']),q)
   self.assertEqual(w.heat,51+q+8);self.assertEqual(w.constructor_remaining,256-(51+q+8)-112);w.check()
  with self.assertRaises(AssertionError):World(1008100)
 def test_worst_cold_start_full_paid_ordinary_child_and_own_gain(self):
  w=World(SOFTWARE[1],8,'no_variation',expansion_tick=0);w.run(1024)
  attempts=[e for e in w.events if e['actor']==0 and 'attempt' in e]
  self.assertEqual([e['attempt']['success'] for e in attempts[:9]],[0]*8+[1])
  self.assertEqual(attempts[8]['energy_before'],5)
  children=paid_viable_children(w.snapshot());self.assertTrue(any(c['own_resource_viable'] for c in children));w.check()
 def test_natural_leases_survive_other_actors_until_own_act(self):
  w=World(SOFTWARE[0],8,'no_variation',expansion_tick=0);w.run(800)
  held={};overlap=False
  for e in w.events:
   if 'sense' in e and e['sense']['packet'] is not None:held[e['actor']]=e['sense']['packet']
   if 'attempt' in e:
    p=e['attempt']['packet']
    self.assertTrue(all(other==e['actor'] or packet!=p for other,packet in held.items()))
    if e['actor'] in held:self.assertEqual(held.pop(e['actor']),p)
    overlap |= bool(held)
  self.assertTrue(overlap)
 def test_real_sampler_abort_releases_reserved_units_and_keeps_charges(self):
  w=World(SOFTWARE[0],8,'variation')
  with patch('experiments.digital_memory80.draw_value',side_effect=lambda key,stage:0 if stage=='gate' else 3):
   for _ in range(200):
    w.step()
    if w.events[-1].get('sampler_finished',{}).get('abort'):break
   else:self.fail('Bounded abort fixture unreachable')
  end=w.events[-1];self.assertEqual(end['sampler_finished']['draws'],9)
  self.assertEqual(w.entities[0]['pending'],None);self.assertEqual(w.entities[0]['nursery'],[])
  self.assertEqual(len(w.free),512-67);self.assertEqual(end['after']['energy'],end['energy_before']-1);w.check()
 def test_header_mutation_and_cost_matched_noninheritance(self):
  for mode,expected in [('variation',8),('no_variation',2),('inheritance_disabled',8)]:
   w=World(SOFTWARE[0],2,mode)
   with patch('experiments.digital_memory80.draw_value',side_effect=lambda key,stage:0 if stage=='gate' else 2):
    while not w.births and w.tick<600:w.step()
   child=w.entities[1];self.assertEqual(child['code'][1][0],expected)
   self.assertEqual(len(child['state_units']),expected+8);self.assertEqual(child['memory'],[0]*expected)
   self.assertEqual(w.effective(child),2 if mode=='inheritance_disabled' else expected)
   self.assertEqual(next(e['sampler_finished']['draws'] for e in w.events if 'sampler_finished' in e),2)
   self.assertTrue(paid_viable_children(w.snapshot())[0]['paid']);w.check()
 def test_truthful_absence_does_not_become_negative_feedback(self):
  code=[[7,8,1],[6,0,0],[1,1,0],[7,0,1]]
  w=World(SOFTWARE[0],8,'no_variation',max_population=1,code=code);w.run(1024)
  absent=[i for i,e in enumerate(w.events) if e.get('feedback')==2]
  self.assertTrue(absent)
  for i in absent:
   self.assertNotIn('attempt',w.events[i]);self.assertEqual(w.events[i]['penalty'],0)
   if i+1<len(w.events):self.assertEqual(w.events[i+1].get('read_feedback'),2)
 def test_deterministic_population_and_header_immutable_in_parent(self):
  a=World(SOFTWARE[2],2);b=World(SOFTWARE[2],2)
  self.assertEqual(a.run(350),b.run(350))
  if 0 in a.entities:self.assertEqual(a.entities[0]['code'][1][0],2)
 def test_paid_endpoint_refuses_forged_inherited_knowledge_or_fee(self):
  w=World(SOFTWARE[0],8,'no_variation');w.run(500);original=w.snapshot()
  for kind in ('knowledge','fee'):
   state=copy.deepcopy(original);birth=next(e for e in state['events'] if 'birth' in e)
   if kind=='knowledge':birth['birth']['child']['memory'][0]=1
   else:birth['after']['energy']+=1
   with self.assertRaises(AssertionError):paid_viable_children(state)
if __name__=='__main__':unittest.main()
