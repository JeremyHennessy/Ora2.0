"""One NEW static interface attestation; no retained tests or World imports."""
import ast,hashlib,json,unittest
from pathlib import Path
class Binding(unittest.TestCase):
 def test_crossed_runtime_interface_sources_bound(self):
  root=Path(__file__).resolve().parents[1];r=json.loads((root/'docs/context90-source-qualification.json').read_bytes());q=r['qualifications']['context90-crossed-interface-prepared-v2']
  self.assertEqual((q['native_calls'],q['worlds'],q['new_groups']),(2,0,7));self.assertEqual(len(q['archive_sha256']),64);self.assertEqual(len(q['failed_v1_archive']),64)
  for relative in ('experiments/digital_context90_crossed_engine_v1.py','experiments/digital_context90_crossed_world_v1.py','experiments/digital_context90_crossed_referee_v1.py','experiments/digital_context90_crossed_child_v1.py','tests/test_context90_crossed_interface_v1.py'):
   self.assertEqual(hashlib.sha256(ast.dump(ast.parse((root/relative).read_bytes()),include_attributes=False).encode()).hexdigest(),r['semantic_ast'][relative])
if __name__=='__main__':unittest.main()
