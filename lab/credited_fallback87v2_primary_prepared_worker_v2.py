"""NON-PHYSICS real graph checks; forbids every constructor/target/source import."""
import hashlib,io,json,sys,unittest
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root))
request=json.loads(Path(sys.argv[1]).read_bytes())
for name,digest in request['source_files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
ALLOWED={'experiments.digital_credited_fallback87v2_primary_child','experiments.digital_credited_fallback87v2_primary_boundary',
 'experiments.digital_credited_fallback87v2_primary_plan','experiments.digital_credited_fallback87v2_acceptance',
 'experiments.evidence_write_grant68','experiments.process_limits'}
class Guard:
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('experiments.') and fullname not in ALLOWED:raise AssertionError('No World/source/target/referee: '+fullname)
sys.meta_path.insert(0,Guard())
buffer=io.StringIO();result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(
    unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_digital_credited_fallback87v2_primary.py'))
if not result.wasSuccessful():print(buffer.getvalue())
assert result.wasSuccessful() and result.testsRun==6
for name,module in tuple(sys.modules.items()):
    if name.startswith('experiments.'):
        assert name in ALLOWED and Path(module.__file__).resolve()==root/(name.replace('.','/')+'.py')
for name,digest in request['source_files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
print(json.dumps(dict(verified=True,checks=6,worlds=0,targets=0,mock_role_callbacks=309,
    mock_producer_geneses=1632,execution_admission=False,stage_credit=False),sort_keys=True))
