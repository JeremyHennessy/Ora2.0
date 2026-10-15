"""Exact-export NON-PHYSICS source/custody checks; no World imports permitted."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import digital_credited_fallback87v2_primary_boundary as boundary
def main():
 root=Path.cwd();request=json.loads(Path(sys.argv[1]).read_bytes());pins=request['source_files']
 assert Path(__file__).resolve()==root/'lab/strategy88_pure_worker_v1.py'
 assert boundary.verify_source(root,pins)==request['source_sha']
 path=root/'tests/test_digital_strategy88.py';spec=importlib.util.spec_from_file_location('strategy88_focused',path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
 assert result.wasSuccessful() and result.testsRun==6
 assert 'experiments.digital_memory80' not in sys.modules and 'experiments.digital_strategy88_world' not in sys.modules
 boundary.module_origins(root,pins);assert boundary.verify_source(root,pins)==request['source_sha']
 print(json.dumps(dict(verified=True,checks=6,worlds=0,targets=0,NONPHYSICS=True)))
if __name__=='__main__':main()
