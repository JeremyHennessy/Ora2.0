"""NON-PHYSICS finite invariance/counterexample and complete retained-data scope."""
import ast,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ClosedOrigins(unittest.TestCase):
 def test_conditional_reencoding_and_counterexample(self):
  def pred(s,c):return (0,1,c%2,1-c%2)[s]
  for s in range(4):
   for e in (0,1):self.assertEqual((s+e+2)%4,((s+2)%4+e)%4)
   for k in range(12):self.assertEqual(pred((s+2*(k+1))%4,k%2),pred(s,k%2))
  # An odd first cue violates the retained-sequence condition: no universal theorem.
  self.assertNotEqual(pred((0+2)%4,1),pred(0,1))
  report=json.loads((ROOT/'data/strategy88/closed-origins-v1.json').read_bytes());self.assertTrue(report['verified'])
  lookup={(r['seed'],r['role']):r for r in report['summary']['all312']};count=0
  for (seed,role),r in lookup.items():
   if not role.startswith('adaptive:'):continue
   other=lookup[seed,'credit_misbound:'+role[-1]];a=[x for x in r['predictions'] if x['late']];b=[x for x in other['predictions'] if x['late']]
   self.assertEqual(len(a),12);self.assertEqual(len(b),12)
   for k,(x,y) in enumerate(zip(a,b,strict=True)):
    self.assertEqual((x['packet'],x['cue'],x['port']),(y['packet'],y['cue'],y['port']));self.assertEqual(y['strategy'],(x['strategy']+2*(k+1))%4);count+=1
  self.assertEqual(count,576)
 def test_all_roster_raw_derivation_and_negative_preservation(self):
  r=json.loads((ROOT/'data/strategy88/closed-origins-v1.json').read_bytes());s=r['summary']
  self.assertEqual((s['totals']['histories'],s['totals']['source_histories'],s['totals']['uses_independently_reproduced'],s['totals']['selections_independently_reproduced']),(312,192,11076,576))
  self.assertEqual(s['misbinding_late_pair_counts'],{'tie':48});self.assertEqual(len(s['prior2_losses']),4)
  self.assertTrue(all(x['observed_masks'][1]==170 and x['history_reset']==12 and x['reset_delta']<0 for x in s['prior2_losses']))
  old=json.loads((ROOT/'data/strategy88/closed-interpretation-v1.json').read_bytes());self.assertFalse(old['robust_functional_selection']);self.assertFalse(old['robust_strong_reference_value'])
  for name in ('strategy88_closed_origins_v1.py','strategy88_misbinding_encoding_proof_v1.py'):
   tree=ast.parse((ROOT/'lab'/name).read_bytes());imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
   self.assertLessEqual(imports,{'collections','hashlib','json','os','stat','sys','pathlib'})
if __name__=='__main__':unittest.main()
