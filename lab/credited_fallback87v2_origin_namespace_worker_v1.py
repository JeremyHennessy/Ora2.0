"""One metadata-only supplement; no closed corpus or World is executed."""
import ast,hashlib,io,json,sys,unittest
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tests'))
request=json.loads(Path(sys.argv[1]).read_bytes())
for name,digest in request['source_files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
old=Path('D:/OraLab/runs/credited-fallback87v2-origin-prepared-v2-20261015/raw/original')
report=json.loads(Path(request['old_report']['path']).read_bytes())
assert hashlib.sha256(Path(request['old_report']['path']).read_bytes()).hexdigest()==request['old_report']['sha256']
assert report['passed'] is True and report['qualified_closed_originals']==51
metric='experiments/digital_credited_fallback87v2_metrics.py'
test='tests/test_digital_credited_fallback87v2_metrics.py'
for name in (metric,test,'experiments/digital_credited_fallback87v2_metric_binding.py'):
    expected=next(v for p,v in report['pins'].items() if p.replace('\\','/').endswith(name))
    assert hashlib.sha256((old/name).read_bytes()).hexdigest()==expected
class Replace(ast.NodeTransformer):
    def visit_Assert(self,node):
        if "body['software_genesis_attempts']" in ast.unparse(node.test):
            return ast.parse("""count_field='software_genesis_attempts' if body['software_only'] else 'scientific_genesis_attempts'
assert count_field in body
assert type(body[count_field]) is int and body[count_field]==len(cases)""").body
        return node
assert ast.dump(Replace().visit(ast.parse((old/metric).read_bytes())))==ast.dump(ast.parse((root/metric).read_bytes()))
class RemoveNew(ast.NodeTransformer):
    def visit_ImportFrom(self,node):return None if node.module=='unittest.mock' else node
    def visit_FunctionDef(self,node):
        return None if node.name=='test_explicit_software_and_primary_count_namespaces' else node
assert ast.dump(ast.parse((old/test).read_bytes()))==ast.dump(RemoveNew().visit(ast.parse((root/test).read_bytes())))
assert (old/'experiments/digital_credited_fallback87v2_metric_binding.py').read_bytes()==(root/'experiments/digital_credited_fallback87v2_metric_binding.py').read_bytes()
ALLOWED={'experiments.digital_credited_fallback87v2_metrics','experiments.digital_credited_fallback87v2_metric_binding'}
class Guard:
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('experiments.') and fullname not in ALLOWED:raise AssertionError('No World/source/target/referee: '+fullname)
sys.meta_path.insert(0,Guard())
buffer=io.StringIO();result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromName('test_digital_credited_fallback87v2_metrics.OriginMetrics.test_explicit_software_and_primary_count_namespaces'))
if not result.wasSuccessful():print(buffer.getvalue())
assert result.wasSuccessful() and result.testsRun==1
for name,digest in request['source_files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
print(json.dumps(dict(verified=True,checks=1,reused_closed_originals=51,reused_native_bindings=18,
    reused_prior_groups=6,worlds=0,targets=0,execution_admission=False,metadata_only=True),sort_keys=True))
