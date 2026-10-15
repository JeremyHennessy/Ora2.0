"""Finite roster/source/caps; no scientific World construction."""
import copy,hashlib,io,json,unittest
from unittest.mock import patch
from experiments import digital_latehistory78_child as child
from experiments import digital_latehistory78_source as source
def request(kind='generate',export='original'):
 pins={p:'b'*64 for p in child.REQUIRED};cfg=copy.deepcopy(child.CONFIG);seed=1008100
 return dict(configuration=cfg,revision='a'*40,source_files=pins,source_sha256=hashlib.sha256(child.boundary.canonical(pins)).hexdigest(),configuration_sha256=hashlib.sha256(child.boundary.canonical(cfg)).hexdigest(),seed=seed,kind=kind,export=export,role=f'{export}:{seed}:latehistory78:{kind}',input=None if kind=='generate' else {},grant=dict(limit=(1 if kind=='audit' else 16)*1024**2),grant_seal='c'*64)
class Boundary(unittest.TestCase):
 def test_ordinary_paid_roster_and_no_preloaded_knowledge(self):
  self.assertEqual(len(child.ARMS),9);self.assertEqual(len(set(child.ARMS)),9)
  for p in source.programmes().values():self.assertEqual(3*len(p)+16,52)
  self.assertEqual(source.manifest()['acquired_memory'],[0]*8);self.assertFalse(source.manifest()['performance_selection'])
  self.assertEqual(child.membership('intact'),('supplied_cognitive','intact'))
  self.assertEqual(child.membership('latest_reactive'),('latest_reactive','intact'))
 def test_request_caps_source_and_reserves(self):
  for kind,export in [('generate','original'),('generate','restored'),('audit','original')]:
   r=request(kind,export)
   with patch.object(child.boundary,'validate_grant'):self.assertEqual(child.admit(r),r['role'])
  for change in [dict(seed=True),dict(seed=1008200),dict(seed=1008400),dict(role='winner'),dict(configuration=dict(child.CONFIG,startup=0))]:
   r=request();r.update(change)
   with patch.object(child.boundary,'validate_grant',side_effect=RuntimeError('grant reached')):
    with self.assertRaises(AssertionError):child.admit(r)
  r=request();r['grant']['limit']+=1
  with patch.object(child.boundary,'validate_grant'):
   with self.assertRaises(AssertionError):child.admit(r)
 def test_failed_generator_restores_methods_without_any_world(self):
  from experiments import digital_latehistory78_world as kernel,digital_latehistory78_history as producer
  r=request();before=(kernel.World.__init__,kernel.World.step);out=io.StringIO()
  with patch.object(child.sys,'argv',['prepared','D:/OraLab/unused']),patch.object(child.boundary,'bounded_bytes',return_value=child.boundary.canonical(r)),patch.object(child.boundary,'validate_grant'),patch.object(child.boundary,'verify_source',return_value=r['source_sha256']),patch.object(producer,'history',side_effect=RuntimeError('prepared stop')),patch.object(child.sys,'stderr',out):
   with self.assertRaisesRegex(RuntimeError,'prepared stop'):child.main()
  self.assertIs(kernel.World.__init__,before[0]);self.assertIs(kernel.World.step,before[1]);self.assertEqual(json.loads(out.getvalue())['counts'],dict(genesis=0,ordinary_steps=0))
if __name__=='__main__':unittest.main()
