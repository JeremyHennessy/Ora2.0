"""Finite STORAGE-02 sixteen-case real-file-operation panel, explicit invocation."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from experiments import world_io_audit as audit

ROOT=Path(__file__).resolve().parents[1]

def run(output,revision):
    if not audit.snapshot.revision_valid(revision):
        raise ValueError('Exact revision required')
    output=Path(output); output.mkdir(exist_ok=False)
    evidence=dict(schema='storage02-panel-v1',revision=revision,sources=audit.sources(),records=[],commands=[])
    def execute(module,args,log,expected=0):
        with (output/log).open('w',encoding='utf-8') as f:
            code=subprocess.run([sys.executable,'-B','-m',module,*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=30).returncode
        evidence['commands'].append(dict(module=module,args=list(map(str,args)),log=log,exit_code=code))
        (output/'panel.json').write_bytes((json.dumps(evidence,sort_keys=True)+'\n').encode())
        if code!=expected:
            raise ValueError(f'{log} exit{code}, expected{expected}')
    def args(path):
        return ['--output-dir',path,'--world-id','storage02-reference','--source-revision',revision,'--work','2','--max-ticks','32','--seed','1']
    execute('experiments.heartbeat_template',args(output/'reference'),'reference.log')
    execute('experiments.heartbeat_template',[*args(output/'paused'),'--pause-after','3'],'paused.log')
    execute('experiments.world_snapshot',['pack','--world-dir',output/'paused','--archive',output/'snapshot.zip','--source-revision',revision],'snapshot.log')
    for case in audit.CASES:
        directory=output/case; directory.mkdir()
        fault_exit,resume_exit=audit.expected(case)
        execute('experiments.world_io_fault',['--case',case,'--trace-dir',directory,*args(directory/'world')],case+'/fault.log',fault_exit)
        shutil.copytree(directory/'world',directory/'before')
        execute('experiments.heartbeat_template',[*args(directory/'world'),'--resume'],case+'/resume.log',resume_exit)
        if resume_exit and audit.hashes(directory/'world')!=audit.hashes(directory/'before'):
            raise ValueError('Rejected input mutated')
        execute('experiments.world_snapshot',['restore','--world-dir',directory/'restored','--archive',output/'snapshot.zip','--source-revision',revision],case+'/restore.log')
        shutil.copytree(directory/'restored',directory/'restored-before')
        execute('experiments.heartbeat_template',[*args(directory/'restored'),'--resume'],case+'/continued.log')
        before=audit.hashes(directory/'restored')
        execute('experiments.heartbeat_template_audit',['--input-dir',directory/'restored','--source-revision',revision],case+'/observer.json')
        if before!=audit.hashes(directory/'restored'):
            raise ValueError('Observer mutated world')
        evidence['records'].append(dict(case=case,fault_exit=fault_exit,resume_exit=resume_exit,
            before_sha256=audit.hashes(directory/'before'),after_sha256=audit.hashes(directory/'world'),
            restored_sha256=audit.hashes(directory/'restored'),observer_read_only=True))
        (output/'panel.json').write_bytes((json.dumps(evidence,sort_keys=True)+'\n').encode())
    return evidence

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir',required=True); p.add_argument('--source-revision',required=True)
    a=p.parse_args()
    try:
        print(json.dumps(dict(cases=len(run(a.output_dir,a.source_revision)['records']))))
    except (ValueError,OSError,KeyError,TypeError,subprocess.TimeoutExpired) as e:
        p.exit(2,f'Rejected I/O panel: {e}\n')
