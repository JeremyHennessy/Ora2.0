"""Only new compact-layout supplement; prior interface tests are not rerun."""
import ast
import json
import unittest
from pathlib import Path
from experiments import digital_context90_access_v2 as vm
from experiments import digital_context90_access_literal_v2 as literal
from experiments import digital_context90_source_v3 as source

base=Path(__file__).resolve().parent
qualified=base/'qualified-tests.py'
if not qualified.exists():qualified=base/'test_context90_access_v2.py'
functions={n.name:n for n in ast.parse(qualified.read_bytes()).body if isinstance(n,ast.FunctionDef)}
namespace={'vm':vm,'source':source}
# Reuse the exact previously qualified abstract interpreter, not any old test class.
exec(compile(ast.fix_missing_locations(ast.Module(body=[functions[n] for n in ('abstract_trial','slot','put')],type_ignores=[])),str(qualified),'exec'),namespace)
abstract_trial,slot,put=(namespace[n] for n in ('abstract_trial','slot','put'))

class CompactLayout(unittest.TestCase):
 def test_only_new_layout_and_cost_paths(self):
  oldpath=base/'qualified-source.py'
  if not oldpath.exists():oldpath=base.parent/'experiments/digital_context90_source_v2.py'
  prior={};exec(compile(oldpath.read_bytes(),str(oldpath),'exec'),prior)
  mapping={1:27,2:28,3:1,4:2,**{i:i-2 for i in range(5,29)}}
  for q in (2,4,8):
   for entry,oldentry in ((27,1),(1,3)):
    before=prior['programme'](q,oldentry);after=source.programme(q,entry)
    self.assertEqual(len(after),29);self.assertEqual(3*len(after)+q+8,95+q)
    self.assertEqual(after[0],[7,q,entry])
    for old,new in mapping.items():
     triple=before[old][:]
     if triple[0] in (7,8,25):triple[2]=mapping[triple[2]]
     self.assertEqual(after[new],triple)
    for initial in (0,1,2):
     for feedback in (0,1,2):
      idx=8 if entry==1 else 0
      g=abstract_trial(put([0]*8,idx,initial),entry,0,feedback)
      expected=11 if feedback==2 else 21 if feedback==1 and initial==0 else 17 if feedback==1 else 20 if initial==0 else 22
      self.assertEqual(g['cost'],expected);self.assertEqual(g['fees'],1 if feedback==2 else 2 if feedback==1 and initial!=0 else 4)
      self.assertEqual(g['action'],initial&1)
      self.assertEqual(g['entry'],(1 if entry==27 else 27) if feedback==0 and initial else entry)
      if feedback==2:self.assertEqual(g['memory'],put([0]*8,idx,initial))
  for pair in source.BOUNDARIES:self.assertEqual(source.completed_boundary(*pair),pair[1])
  for pair in ((25,27),(26,28),(True,1)):
   with self.assertRaises(ValueError):source.completed_boundary(*pair)

if __name__=='__main__':unittest.main()
