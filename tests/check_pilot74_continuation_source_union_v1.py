"""New raw-byte source/AST check only; never imports world modules or runs suites."""
from pathlib import Path
import ast,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
def check():
    manifest=json.loads((ROOT/'data/pilot74-continuation-source-union-v1.json').read_text(encoding='utf-8'))
    rows={};parsed=0
    for name,expected in manifest['source_files'].items():
        raw=(ROOT/name).read_bytes();actual=hashlib.sha256(raw).hexdigest()
        assert actual==expected,(name,actual,expected)
        assert raw==subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT),name
        if name.endswith('.py'):ast.parse(raw,filename=name);parsed+=1
        rows[name]=actual
    return dict(schema='PILOT74-CONTINUATION-RAW-SOURCE-CI-v1',head_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_hashes=rows,parsed_modules=parsed,external_artifact=manifest['external_native_artifact'],worlds=0,vm_steps=0,old_suites_rerun=False,native_qualification=False)
if __name__=='__main__':print(json.dumps(check(),sort_keys=True,indent=2))
