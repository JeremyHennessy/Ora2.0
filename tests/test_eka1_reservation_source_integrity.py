"""Offline wrapper budget source/origin regressions; never import a World."""
import ast, hashlib, importlib.util, os, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(os.environ.get('ORA_EKA_REVIEW_ROOT',Path(__file__).resolve().parents[1]))
LEDGER=ROOT/'tools/eka1_cumulative_reservations.py'
spec=importlib.util.spec_from_file_location('tools.eka1_cumulative_reservations',LEDGER)
budget=importlib.util.module_from_spec(spec);spec.loader.exec_module(budget)
class StopBeforeRuntime(RuntimeError):pass
class ReservationSourceChecks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=ROOT);self.file=Path(self.tmp.name)/'ledger'
  self.fd=os.open(self.file,os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_BINARY,0o600)
  self.res=budget.Reservations(self.fd);self.res.role(1,0)
  package=types.ModuleType('tools');package.__path__=[str(ROOT/'tools')];package.eka1_cumulative_reservations=budget
  self.modules=patch.dict(sys.modules,{'tools':package,'tools.eka1_cumulative_reservations':budget});self.modules.start()
 def tearDown(self):self.modules.stop();self.res.close();os.close(self.fd);self.tmp.cleanup()
 def scope(self,derived):
  name='digital_eka1_derived_reconstruction_v1.py' if derived else 'digital_eka1_selection_replay_v1.py'
  tree=ast.parse((ROOT/'experiments'/name).read_bytes())
  names={'reservation_class','reconstruct_and_verify' if derived else 'replay_original_selection'}
  nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
  pinname='SOURCE_PINS' if derived else 'INPUT_PINS'
  pins=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==pinname for t in n.targets)))
  def sentinel():raise StopBeforeRuntime('No World import or execution')
  result={'ROOT':ROOT,'Path':Path,'hashlib':hashlib,pinname:pins,'request_metadata':lambda r:r['configuration'],'prepare':lambda *a:({},{}),'metadata_inputs':sentinel,'runtime_sources':sentinel}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact-source-wrapper-extract>','exec'),result)
  return result
 def invoke(self,scope,derived,index=0,res=None):
  r={'configuration':{'dose':1},'stop_tick':4096,'assigned_stop_tick':4096}
  kw={'reservations':self.res if res is None else res,'genesis_index':index}
  return scope['reconstruct_and_verify'](b'',b'',r,**kw) if derived else scope['replay_original_selection'](b'',r,**kw)
 def test_both_ledger_pins_are_exact(self):
  for d in (False,True):
   s=self.scope(d);self.assertEqual(s['SOURCE_PINS' if d else 'INPUT_PINS']['tools/eka1_cumulative_reservations.py'],hashlib.sha256(LEDGER.read_bytes()).hexdigest());self.assertIs(s['reservation_class'](),budget.Reservations)
 def test_changed_ledger_bytes_refused_before_class_or_runtime(self):
  for d in (False,True):
   s=self.scope(d)
   with patch.object(Path,'read_bytes',return_value=b'changed ledger'):
    with self.assertRaisesRegex(ValueError,'source changed'):self.invoke(s,d)
   self.assertEqual(self.res._genesis[1],{})
 def test_symlink_ledger_refused_without_read(self):
  for d in (False,True):
   s=self.scope(d)
   with patch.object(Path,'is_symlink',return_value=True),patch.object(Path,'read_bytes',side_effect=AssertionError('must reject before read')):
    with self.assertRaisesRegex(ValueError,'source changed'):self.invoke(s,d)
 def test_wrong_module_origin_refused_before_reservation(self):
  for d in (False,True):
   s=self.scope(d)
   with patch.object(budget,'__file__',str(ROOT/'wrong.py')):
    with self.assertRaisesRegex(ValueError,'origin differs'):self.invoke(s,d)
   self.assertEqual(self.res._genesis[1],{})
 def test_wrong_exact_type_and_duplicate_index_refused_before_runtime(self):
  for d in (False,True):
   s=self.scope(d)
   with self.assertRaises(TypeError):self.invoke(s,d,res=object())
  self.res.genesis(1,0)
  for d in (False,True):
   with self.assertRaises(ValueError):self.invoke(self.scope(d),d)
 def test_failed_sync_poison_prevents_both_loaders(self):
  with patch.object(budget.os,'fsync',side_effect=OSError('independent sync failure')):
   with self.assertRaises(OSError):self.invoke(self.scope(False),False)
  raw=self.file.read_bytes()
  with self.assertRaises(RuntimeError):self.invoke(self.scope(True),True,index=1)
  self.assertEqual(raw,self.file.read_bytes())
 def test_full_envelope_burned_before_both_runtime_sentinels(self):
  for d,i in ((False,0),(True,1)):
   with self.assertRaises(StopBeforeRuntime):self.invoke(self.scope(d),d,index=i)
   self.assertEqual(self.res._genesis[1][i],4096)
 def test_invalid_genesis_index_prevents_runtime(self):
  for d in (False,True):
   for index in (True,-1,32,0.0):
    with self.assertRaises(ValueError):self.invoke(self.scope(d),d,index=index)
 def test_no_native_modules_imported(self):self.assertFalse(any(n.startswith('experiments.digital_') for n in sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
