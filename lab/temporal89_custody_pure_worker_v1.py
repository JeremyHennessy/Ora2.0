"""New finite graph/mock checks only;actual native roles/genesis are not simulated."""
import hashlib,io,json,sys,unittest
from pathlib import Path

def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()

def main():
 q=json.loads(Path(sys.argv[1]).read_bytes());root=Path(q['root']);assert Path(__file__).resolve()==root/'lab/temporal89_custody_pure_worker_v1.py'
 sys.path.insert(0,str(root))
 from experiments import digital_credited_fallback87v2_primary_boundary as boundary
 assert boundary.verify_source(root,q['source_files'])==q['source_sha']
 sys.path.insert(0,str(root/'tests'))
 from test_digital_temporal89_custody import Temporal89Custody
 assert Path(sys.modules['test_digital_temporal89_custody'].__file__).resolve()==root/'tests/test_digital_temporal89_custody.py'
 names=unittest.defaultTestLoader.getTestCaseNames(Temporal89Custody);assert len(names)==6
 stream=io.StringIO()
 result=unittest.TextTestRunner(stream=stream,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Temporal89Custody))
 assert result.wasSuccessful() and result.testsRun==6,stream.getvalue()
 assert not any(n in sys.modules for n in ('experiments.digital_temporal89_world','experiments.digital_temporal89_source','experiments.digital_memory80'))
 boundary.module_origins(root,q['source_files'])
 value=enc(dict(verified=True,checks=6,scope='NON-PHYSICS graph mocks;not actual31native calls',worlds=0,targets=0))
 Path(q['output']).write_bytes(value)
 print(enc(dict(verified=True,extent=len(value),sha256=hashlib.sha256(value).hexdigest(),worlds=0,targets=0)).decode())

if __name__=='__main__':main()
