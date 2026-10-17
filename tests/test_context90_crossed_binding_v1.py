"""One NEW portable attestation check; retained pure tests are not rerun."""
import ast,hashlib,json,unittest
from pathlib import Path
class Binding(unittest.TestCase):
 def test_crossed_qualified_components_bound(self):
  root=Path(__file__).resolve().parents[1];receipt=json.loads((root/'docs/context90-source-qualification.json').read_bytes());q=receipt['qualifications']['context90-crossed-pure-prepared-v1']
  self.assertEqual((q['native_calls'],q['worlds'],q['new_groups']),(2,0,7));self.assertEqual(len(q['archive_sha256']),64)
  for relative in ('experiments/digital_context90_crossed_programme_v1.py','experiments/digital_context90_crossed_registry_v1.py','experiments/digital_context90_crossed_metrics_v1.py','tests/test_context90_crossed_pure_v1.py'):
   actual=hashlib.sha256(ast.dump(ast.parse((root/relative).read_bytes()),include_attributes=False).encode()).hexdigest();self.assertEqual(actual,receipt['semantic_ast'][relative])
if __name__=='__main__':unittest.main()
