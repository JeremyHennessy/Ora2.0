"""Source/data-only worker: forbid every other experiment module before imports."""
import hashlib,io,json,sys,unittest
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root))
request=json.loads(Path(sys.argv[1]).read_bytes())
def check():
 for name,value in request['source_files'].items():
  assert hashlib.sha256((root/name).read_bytes()).hexdigest()==value
check()
class NoWorlds:
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('experiments.') and (fullname in ('experiments.digital_memory80','experiments.digital_memory80_referee') or fullname.endswith(('_world','_referee'))):
   raise AssertionError('Producer/referee forbidden during pure custody qualification')
sys.meta_path.insert(0,NoWorlds())
buffer=io.StringIO()
result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(
 unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_digital_credited_fallback86_active.py'))
if not result.wasSuccessful():print(buffer.getvalue())
assert result.wasSuccessful() and result.testsRun==5
assert 'experiments.digital_memory80' not in sys.modules and 'experiments.digital_memory80_referee' not in sys.modules
for name,module in list(sys.modules.items()):
 if name.startswith('experiments.') and getattr(module,'__file__',None):
  assert Path(module.__file__).resolve()==(root/(name.replace('.','/')+'.py')).resolve()
check()
print(json.dumps(dict(verified=True,checks=5,scientific_worlds=0,scientific_targets=0,software_worlds=0,software_targets=0,pure_reserved_roles=52,data_only_cells=144,actual_native_refusals=0,stage_credit=False),sort_keys=True))
