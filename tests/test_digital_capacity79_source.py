"""Invented feedback only; no World imports, source selection or fresh contexts."""
import unittest
from experiments.digital_capacity79_source import DOMAIN,OPS,source,compile_programme,manifest
from experiments.digital_oneshot77_referee import move
from experiments.digital_oneshot77_source import LEARNER,REFERENCES
def decisions(code,labels,orientation):
 s=dict(r=[0,0],m=[0]*8,pc=0,feedback=0);ports=[]
 for tick in range(2048):
  packet=len(ports);cue=(packet+orientation)%2;op,a,b=code[s['pc']];feedback=s['feedback']
  if op==6:
   port=s['r'][a%2]%2;ports.append(port);feedback=int(port==(labels[cue]^int(packet>=16)))
  s=move(code,s,feedback,False,cue)
  if len(ports)==32:return ports
 raise AssertionError('Fixture failed finite decision endpoint')
def cycle(code,family,correct,k):
 start=3 if family==0 else 5;s=dict(r=[0,0],m=[0]*8,pc=start,feedback=0);acts=0
 for tick in range(200):
  op,a,b=code[s['pc']]
  if op==6:acts+=1
  s=move(code,s,int(correct),False,0)
  if s['pc']==start:return tick+1,acts
 raise AssertionError('Fixture cycle did not close')
class CapacitySource(unittest.TestCase):
 def test_complete_unscreened_domain_and_cost_admission(self):
  m=manifest();self.assertEqual(len(m['sources']),12)
  self.assertEqual([tuple(x['descriptor']) for x in m['sources']],list(DOMAIN))
  self.assertEqual([x['descriptor'] for x in m['sources'] if x['source_admissible']],[[0,k] for k in range(1,7)]+[[1,k] for k in range(1,4)])
  for item in m['sources']:
   self.assertEqual(item['formation_cost'],3*len(item['programme'])+16)
   self.assertEqual(item['conditional_copy_and_div_cost'],4*len(item['programme'])+51)
   self.assertFalse(item['performance_selection']);self.assertFalse(item['reproduction_admitted'])
   self.assertEqual(item['acquired_state']['m'],[0]*8)
 def test_same_controller_semantics_for_all_invented_maps(self):
  for family,k in DOMAIN:
   if not source(family,k)['source_admissible']:continue
   reference=REFERENCES['latest_reactive'] if family==0 else LEARNER
   for labels in ((0,0),(0,1),(1,0),(1,1)):
    for orientation in (0,1):
     self.assertEqual(decisions(compile_programme(family,k),labels,orientation),decisions(reference,labels,orientation))
 def test_actual_instruction_cycles_match_declared_prices(self):
  for family,k in DOMAIN:
   item=source(family,k);code=item['programme']
   if not item['source_admissible']:continue
   self.assertEqual(cycle(code,family,True,k),(item['success_cycle_instructions'],k))
   self.assertEqual(cycle(code,family,False,k),(item['wrong_cycle_instructions'],1))
 def test_deterministic_typed_code_and_descriptor_refusal(self):
  self.assertEqual(manifest(),manifest())
  for family,k in DOMAIN:
   code=compile_programme(family,k)
   self.assertTrue(all(len(t)==3 and t[0] in OPS and all(type(v) is int and 0<=v<32 for v in t) for t in code))
   code[0][0]=31;self.assertEqual(compile_programme(family,k)[0][0],7)
  for family,k in ((True,1),(0,True),(2,1),(0,7)):
   with self.assertRaises(ValueError):compile_programme(family,k)
if __name__=='__main__':unittest.main()
