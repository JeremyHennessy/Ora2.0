"""One NEW whole-runtime source attestation; no World or retained-group execution."""
import ast,hashlib,json,unittest
from pathlib import Path
class Binding(unittest.TestCase):
 def test_whole_crossed_runtime_source_bound(self):
  root=Path(__file__).resolve().parents[1];r=json.loads((root/'docs/context90-source-qualification.json').read_bytes())
  for tag in ('context90-crossed-pure-prepared-v1','context90-crossed-interface-prepared-v2','context90-crossed-custody-prepared-v1'):
   q=r['qualifications'][tag];self.assertEqual((q['native_calls'],q['worlds'],q['new_groups']),(2,0,7));self.assertEqual(len(q['archive_sha256']),64)
  names=['experiments/digital_context90_crossed_'+name+'_v1.py' for name in ('programme','registry','metrics','engine','world','referee','child','plan')]+['lab/run_context90_crossed_v1.py','tests/test_context90_crossed_custody_v1.py']
  for relative in names:self.assertEqual(hashlib.sha256(ast.dump(ast.parse((root/relative).read_bytes()),include_attributes=False).encode()).hexdigest(),r['semantic_ast'][relative])
  self.assertEqual(hashlib.sha256((root/'docs/CONTEXT90-CROSSED-CONTRACT-v1.md').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'b2d7402f2fa00e34dffd5eca4f747fff6f0e830ed7bc983706fa0613acb9ad7c')
if __name__=='__main__':unittest.main()
