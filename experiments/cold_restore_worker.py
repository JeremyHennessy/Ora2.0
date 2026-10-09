"""Fixed resume from an independently restored isolated runtime; no genesis."""
import json
import os
from pathlib import Path
import sys
from experiments import heartbeat_template as world
from experiments import heartbeat_template_audit as replay


def provenance():
    root=Path(__file__).resolve().parent
    value=dict(pid=os.getpid(),executable=sys.executable,prefix=sys.prefix,
        isolated=bool(sys.flags.isolated),sys_path=list(sys.path),
        module_files={k:v.__file__ for k,v in sorted(sys.modules.items()) if isinstance(getattr(v,'__file__',None),str)},
        source_sha256=replay.source_hashes())
    paths=[value['executable'],value['prefix'],*value['sys_path'],*value['module_files'].values()]
    if not value['isolated'] or any(not Path(p).resolve().is_relative_to(root) for p in paths):
        raise ValueError('Restored child loaded an external application path')
    return value


def main(workspace):
    workspace=Path(workspace)
    request=json.loads((workspace/'request.json').read_text(encoding='utf-8'))
    if set(request)!={'world_id','revision','resume'} or request['resume'] is not True:
        raise ValueError('Fixed restoration request requires resume')
    report=provenance(); report['phase']='before_resume'
    (workspace/'runtime.json').write_text(json.dumps(report)+'\n',encoding='utf-8')
    (workspace/'worker-started').write_text('fixed-cold-restore',encoding='utf-8')
    world.run(workspace/'world',request['world_id'],request['revision'],work=2,max_ticks=32,seed=1,resume=True)
    report=provenance(); report['phase']='complete'
    (workspace/'runtime.json').write_text(json.dumps(report)+'\n',encoding='utf-8')


if __name__=='__main__':
    try: main(sys.argv[1])
    except (ValueError,OSError,KeyError,TypeError) as error:
        try: (Path(sys.argv[1])/'rejection.json').write_text(json.dumps(dict(reason=str(error)))+'\n',encoding='utf-8')
        except OSError: pass
        raise SystemExit(2)
