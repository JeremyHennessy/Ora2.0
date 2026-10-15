"""Invented software worlds only; no registered context or reserve."""
import copy,unittest
from experiments.digital_oneshot77_world import World,PROGRAMS,h
from experiments.digital_oneshot77_history import history
from experiments.digital_oneshot77_referee import audit
class OneShot(unittest.TestCase):
 def test_wrong_choice_consumes_paid_packet_once(self):
  w=World(2000077,route='fixed0');w.step();w.step();e=w.events[-1]
  self.assertEqual(e['attempt']['success'],0);self.assertNotIn(0,w.food)
  self.assertEqual(e['packet_outflow'],dict(packet=0,energy=20,captured=0,heat=20))
  self.assertEqual(w.constructor_remaining,44);self.assertEqual(w.heat,52+2+4+20);w.check()
 def test_absence_is_truthful_shared_feedback(self):
  w=World(2000078,route='fixed0')
  while w.tick<50:w.step()
  self.assertEqual(w.events[-1]['decoded'][0],6);self.assertNotIn('attempt',w.events[-1]);self.assertEqual(w.events[-1]['feedback'],2)
  self.assertNotIn('packet_outflow',w.events[-1]);w.check()
 def test_whole_paid_route_and_literal_proof_in_both_orientations(self):
  for seed in (2000077,2000078):
   row=history(seed,'supplied_cognitive','intact');proof=audit(row,PROGRAMS['supplied_cognitive'],software=True)
   self.assertTrue(proof['completed']);self.assertEqual(proof['deaths'],0);self.assertGreaterEqual(proof['successes'],28)
   self.assertEqual(proof['formation_cost'],52);self.assertEqual(proof['startup_cost'],32)
   self.assertEqual(len([e for e in row['final']['events'] if 'attempt' in e]),32)
 def test_actual_model_controls_are_paid_and_fully_replayed(self):
  for arm in ('model_disabled','history_misbound'):
   row=history(2000077,'supplied_cognitive',arm);proof=audit(row,PROGRAMS['supplied_cognitive'],software=True)
   self.assertTrue(proof['verified']);self.assertEqual(proof['formation_cost']+proof['startup_cost'],84)
   for e in row['final']['events']:
    for cut in e['control']['rewrites']:self.assertEqual(cut['channel'],'m')
 def test_literal_referee_rejects_loss_or_target_forgery(self):
  row=history(2000077,'supplied_cognitive','intact')
  for field in ('packet_outflow','attempt'):
   changed=copy.deepcopy(row);event=next(e for e in changed['final']['events'] if field in e)
   event[field]['heat' if field=='packet_outflow' else 'target']^=1;changed['hash']=h(changed['final'])
   with self.assertRaises(AssertionError):audit(changed,PROGRAMS['supplied_cognitive'],software=True)
if __name__=='__main__':unittest.main()
