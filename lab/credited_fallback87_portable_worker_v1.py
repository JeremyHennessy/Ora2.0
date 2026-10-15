"""Run only changed CI fixtures; no World or scientific target permitted."""
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

root=Path.cwd();sys.path.insert(0,str(root))
request=json.loads(Path(sys.argv[1]).read_bytes())
for name,sha in request['source_files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha
for field in ('old_source_test','old_binding_test'):
    spec=request[field];raw=Path(spec['path']).read_bytes()
    assert len(raw)==spec['extent'] and hashlib.sha256(raw).hexdigest()==spec['sha256']
    old=ast.parse(raw)
    new=ast.parse((root/('tests/test_digital_credited_fallback87_source.py' if field=='old_source_test'
                         else 'tests/test_digital_credited_fallback87v2_binding.py')).read_bytes())
    if field=='old_source_test':
        for node in ast.walk(old):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='assertEqual' and len(node.args)==2 and isinstance(node.args[1],ast.Constant) and node.args[1].value=='1826b33893321d1a7a603ccef690e13b92ed16f26d6e6c093f14a45ca367e104':
                node.func.attr='assertIn';node.args[1]=ast.Set(elts=[ast.Constant(value=v) for v in (
                    '1826b33893321d1a7a603ccef690e13b92ed16f26d6e6c093f14a45ca367e104',
                    'dc4b9ebfc6a38a12863df2a569e8f2d0722ed91e09ade14ca8693b08455bea64')])
    else:
        class Replace(ast.NodeTransformer):
            def visit_Expr(self,node):
                call=node.value
                if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and call.func.attr=='assertEqual' and len(call.args)==2 and isinstance(call.args[1],ast.Attribute) and call.args[1].attr=='CONTRACT_SHA256':
                    return ast.parse("""self.assertEqual(source.CONTRACT_SHA256,'8342c880706e5254c045995e3ca79ba09dbb4d0cca0717008214359aceb7e154')
self.assertIn(hashlib.sha256(contract.read_bytes()).hexdigest(),{source.CONTRACT_SHA256,'f97b541a6b28edc11834e4b079368222298cee6afa4d99882ff652a0d54abbef'})""").body
                return node
        old=Replace().visit(old)
    assert ast.dump(old)==ast.dump(new), 'Unexpected test change beyond exact CI fixture guard'
assert request['source_files']['experiments/digital_memory80.py'] in {
    '1826b33893321d1a7a603ccef690e13b92ed16f26d6e6c093f14a45ca367e104',
    'dc4b9ebfc6a38a12863df2a569e8f2d0722ed91e09ade14ca8693b08455bea64'}
assert request['source_files']['docs/DIGITAL-CREDITED-FALLBACK87-PROSPECTIVE-CONTRACT-V2.md'] in {
    '8342c880706e5254c045995e3ca79ba09dbb4d0cca0717008214359aceb7e154',
    'f97b541a6b28edc11834e4b079368222298cee6afa4d99882ff652a0d54abbef'}
ALLOWED={'experiments.digital_memory80','experiments.digital_credited_fallback86_source',
 'experiments.digital_credited_fallback86_controls','experiments.digital_credited_fallback86_control_referee',
 'experiments.digital_credited_fallback87_source','experiments.digital_credited_fallback87_world',
 'experiments.digital_credited_fallback87_referee','experiments.digital_revision84_source',
 'experiments.digital_latehistory78_source','experiments.digital_credited_fallback87v2_source',
 'experiments.digital_credited_fallback87v2_acceptance'}
class Guard:
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('experiments.') and fullname not in ALLOWED:raise AssertionError(fullname)
sys.meta_path.insert(0,Guard())
from experiments import digital_memory80 as engine
from experiments import digital_credited_fallback87_world as world
def forbidden(*args,**kwargs):raise AssertionError('World/step/fresh label forbidden')
engine.World.__init__=forbidden;engine.World.step=forbidden
world.World.__init__=forbidden;world.World.step=forbidden;world._genesis=forbidden
from experiments import digital_credited_fallback87_source as source
from experiments import digital_credited_fallback87v2_source as source2
source.target_mask=forbidden;source2.target_mask=forbidden
sys.path.insert(0,str(root/'tests'))
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in (
 'test_digital_credited_fallback87_source.Source87Tests.test_source_and_import_boundary',
 'test_digital_credited_fallback87v2_binding.BindingV2Tests.test_separate_contract_ast_and_complete_numeric_endpoints'))
buffer=io.StringIO();result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(suite)
if not result.wasSuccessful():print(buffer.getvalue())
assert result.wasSuccessful() and result.testsRun==2
observed={n for n in sys.modules if n.startswith('experiments.')};assert observed<=ALLOWED
for name in observed:assert Path(sys.modules[name].__file__).resolve()==(root/(name.replace('.','/')+'.py')).resolve()
for name,sha in request['source_files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha
print(json.dumps(dict(verified=True,changed_methods=2,reused_other_source_groups=5,
    exact_known_byte_variants_only=True,live_source_normalization=False,
    worlds=0,targets=0,paid_physics=False,stage_credit=False),sort_keys=True))
