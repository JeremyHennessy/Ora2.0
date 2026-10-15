"""One cache integration regression; reuse prior five exact archived test ASTs."""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile
root=Path.cwd();sys.path.insert(0,str(root))
request=json.loads(Path(sys.argv[1]).read_bytes())

def check():
    for name,value in request['source_files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==value
check()
reuse=request['reuse_v1']
for spec in reuse.values():
    raw=Path(spec['path']).read_bytes()
    assert len(raw)==spec['extent'] and hashlib.sha256(raw).hexdigest()==spec['sha256']
old=json.loads(Path(reuse['report']['path']).read_bytes())
assert old['passed'] and old['checks']==5 and old['error'] is None
assert old['evidence_archive_sha256']==reuse['archive']['sha256']
member='raw/original/tests/test_digital_credited_fallback86_active.py'
with zipfile.ZipFile(reuse['archive']['path']) as z:
    assert z.getinfo(member).file_size<=1024**2
    previous=z.read(member)
assert hashlib.sha256(previous).hexdigest()==old['pins'][request['original_test_path']]
current=(root/'tests/test_digital_credited_fallback86_active.py').read_bytes()
def functions(raw):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(raw))
            if isinstance(n,ast.FunctionDef)}
before=functions(previous);after=functions(current)
assert len([name for name in before if name.startswith('test_')])==5
assert all(after[name]==value for name,value in before.items())
class NoWorlds:
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('experiments.') and (fullname in (
            'experiments.digital_memory80','experiments.digital_credited_fallback86_controls')
            or fullname.endswith(('_world','_referee'))):
            raise AssertionError('World/referee forbidden in cache qualification')
sys.meta_path.insert(0,NoWorlds())
spec=importlib.util.spec_from_file_location('active_tests',root/'tests/test_digital_credited_fallback86_active.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
buffer=io.StringIO()
result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromName('ActiveCustody.test_cached_custody_reader_and_body_lifetime',module))
if not result.wasSuccessful():print(buffer.getvalue())
assert result.wasSuccessful() and result.testsRun==1
check()
print(json.dumps(dict(verified=True,checks=1,reused_checks=5,reused_ast_exact=True,
    reused_archive_sha256=reuse['archive']['sha256'],scientific_worlds=0,scientific_targets=0,
    software_worlds=0,software_targets=0,actual_native_refusals=0,stage_credit=False),sort_keys=True))
