"""Unchanged-kernel boundary fixtures, no scientific contexts."""
import unittest
from experiments.digital_memory80 import World,SOFTWARE
class Boundaries(unittest.TestCase):
 def test_context_expansion_is_uniform_and_keeps_existing_labels(self):
  code=[[7,8,1],[4,0,0],[6,0,0],[7,0,1]]
  w=World(SOFTWARE[2],8,'no_variation',max_population=1,code=code);w.run(1664)
  before=next(e['input'] for e in w.events if e['tick']==1472)
  after=next(e['input'] for e in w.events if e['tick']==1536)
  self.assertEqual(set(p['cue'] for p in before),{0,1})
  self.assertEqual([sum(p['cue']==c for p in after) for c in range(8)],[2]*8)
  for e in w.events:
   if 'attempt' in e:self.assertEqual(e['attempt']['target'],(90>>e['attempt']['cue'])&1)
  w.check()
 def test_installed_age_removal_reclaims_material_and_dissipates_energy(self):
  w=World(SOFTWARE[0],8,'no_variation',max_population=1,code=[[7,8,1],[6,0,0],[1,1,0],[7,0,1]])
  w.run(2050);self.assertEqual(w.tick,2048);self.assertEqual(w.entities,{})
  self.assertEqual(w.events[-1]['death']['cause'],'installed_age_law')
  self.assertGreater(w.events[-1]['death']['dissipated'],0)
  self.assertEqual(w.free,list(range(512)));w.check()
 def test_energy_death_returns_unconsumed_leased_packet(self):
  w=World(SOFTWARE[0],8,'no_variation',max_population=1,code=[[7,8,1],[0,0,0],[7,0,1]])
  w.run(150);self.assertEqual(w.tick,112);self.assertEqual(w.entities,{})
  self.assertEqual(w.events[-1]['death']['cause'],'energy');self.assertEqual(w.leases,{})
  self.assertIn(0,w.food);self.assertEqual(w.free,list(range(512)));w.check()
if __name__=='__main__':unittest.main()
