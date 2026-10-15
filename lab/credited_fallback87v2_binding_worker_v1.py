"""Source-only native fixture worker: no World/step/fresh target is permitted."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

root=Path.cwd();sys.path.insert(0,str(root))
request=json.loads(Path(sys.argv[1]).read_bytes())
for name,digest in request['source_files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
ALLOWED={'experiments.digital_memory80','experiments.digital_credited_fallback86_source',
 'experiments.digital_credited_fallback86_controls','experiments.digital_credited_fallback86_control_referee',
 'experiments.digital_credited_fallback87_source','experiments.digital_credited_fallback87_world',
 'experiments.digital_credited_fallback87_referee','experiments.digital_revision84_source',
 'experiments.digital_latehistory78_source',
 'experiments.digital_credited_fallback87v2_source','experiments.digital_credited_fallback87v2_world',
 'experiments.digital_credited_fallback87v2_referee','experiments.digital_credited_fallback87v2_acceptance'}
class ImportGuard:
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('experiments.') and fullname not in ALLOWED:
            raise AssertionError('Unqualified module: '+fullname)
sys.meta_path.insert(0,ImportGuard())
from experiments import digital_memory80 as engine
from experiments import digital_credited_fallback87v2_world as world
from experiments import digital_credited_fallback87v2_source as source
from experiments import digital_credited_fallback87v2_referee as literal
assert world._genesis.__code__ is engine.World.__init__.__code__
assert world.bind(engine.World.step).__code__ is engine.World.step.__code__
def forbidden(*args,**kwargs):raise AssertionError('World/step forbidden during source qualification')
engine.World.__init__=forbidden;engine.World.step=forbidden
world.World.__init__=forbidden;world.World.step=forbidden;world._genesis=forbidden
def known_only(function):
    def wrapped(seed,*args,**kwargs):
        assert type(seed) is int and seed in source.SOFTWARE, 'Fresh target forbidden'
        return function(seed,*args,**kwargs)
    return wrapped
source.target_mask=known_only(source.target_mask)
literal.label_mask=known_only(literal.label_mask)

reused=json.loads((root/'data/credited-fallback87/source-prepared-v1.json').read_bytes())
assert reused['passed'] and reused['checks']==6 and reused['worlds']==reused['targets']==0
for path,sha in reused['pins'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
from experiments import digital_credited_fallback87_world as old_world
old_world.World.__init__=forbidden;old_world.World.step=forbidden;old_world._genesis=forbidden
from experiments import digital_credited_fallback87_source as old_source
old_source.target_mask=known_only(old_source.target_mask)

buffer=io.StringIO()
result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(
    unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_digital_credited_fallback87v2_binding.py'))
if not result.wasSuccessful():print(buffer.getvalue())
assert result.wasSuccessful() and result.testsRun==1
assert not [n for n in sys.modules if n.startswith('experiments.') and n not in ALLOWED]
for name in ALLOWED:
    assert Path(sys.modules[name].__file__).resolve()==(root/(name.replace('.','/')+'.py')).resolve()
for name,digest in request['source_files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
print(json.dumps(dict(verified=True,checks=1,reused_source_groups=6,descriptors=9,efficient_references=6,
    original_kernel_code_objects_reused=True,unchanged_literal_helpers=True,
    scientific_worlds=0,targets=0,software_worlds=0,paid_physics_qualified=False,
    source_only=True,stage_credit=False),sort_keys=True))
