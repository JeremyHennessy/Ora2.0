"""Run only new NON-PHYSICS custody fixtures; forbid all World/literal modules."""
import hashlib,io,json,sys,unittest
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root))
request=json.loads(Path(sys.argv[1]).read_bytes())
for name,digest in request['source_files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
allowed={name[:-3].replace('/','.') for name in request['source_files'] if name.startswith('experiments/') and name.endswith('.py')}
for name in tuple(allowed):
    if name.endswith(('_world','_referee')) or name in ('experiments.digital_memory80',):allowed.remove(name)
class Guard:
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('experiments.') and fullname not in allowed:
            raise AssertionError('World/physics/foreign experiment import forbidden: '+fullname)
sys.meta_path.insert(0,Guard())
buffer=io.StringIO()
result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(
    unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_digital_credited_fallback87v2_paid.py'))
if not result.wasSuccessful():print(buffer.getvalue())
assert result.wasSuccessful() and result.testsRun==6
for name,module in tuple(sys.modules.items()):
    if name.startswith('experiments.'):
        assert name in allowed
        assert Path(module.__file__).resolve()==root/(name.replace('.','/')+'.py')
for name,digest in request['source_files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
print(json.dumps(dict(verified=True,checks=6,worlds=0,targets=0,nonphysics=True,
    role_graph=22,planned_software_geneses=102,paid_physics=False,stage_credit=False),sort_keys=True))
