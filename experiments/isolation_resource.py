"""ISOLATION-03 explicit confined actual-resource/recovery panel."""
import argparse
import ctypes as c
from pathlib import Path
import shutil
import subprocess
import time
import uuid
from experiments import isolation_capability as gate
from experiments import isolation_world as observation
from experiments import heartbeat_template_audit as replay

ROOT=Path(__file__).resolve().parents[1]
CASES=('cpu','cpu-control','memory','memory-control','wall','wall-control')
FILES=(*observation.FILES,'experiments/isolation_resource.py',
       'experiments/isolation_resource_worker.py','experiments/isolation_resource_audit.py',
       'docs/ISOLATION-03-CONTRACT.md','docs/ISOLATION-03-EXECUTION-ERRATUM.md')


def run_panel(output,revision):
    kernel,adv,user=gate.libraries()
    if len(revision)!=40 or any(x not in '0123456789abcdef' for x in revision):
        raise ValueError('Exact reviewed revision')
    output=Path(output).resolve()
    if output.drive.upper()!='D:' or output.exists():
        raise ValueError('Fresh D: output')
    if shutil.disk_usage(output.parent).free<5*1024**3:
        raise OSError('5 GB floor')
    output.mkdir()
    data=dict(schema='isolation03-v1',revision=revision,source_sha256={p:gate.sha(ROOT/p) for p in FILES},
        profile='OraLab.IsolationResource.'+uuid.uuid4().hex,rows=[],acl=[],cleanup=False)
    sid=c.c_void_p(); created=False; started=time.monotonic()
    try:
        result=user.CreateAppContainerProfile(data['profile'],data['profile'],'Bounded resource continuity fixture',None,0,c.byref(sid))
        if result!=0:
            raise OSError(f'Create profile HRESULT {result & 0xffffffff:08x}')
        created=True; data['package_sid']=gate.sid_text(sid,kernel,adv)
        gate.save(output/'evidence.json',data)
        runtime=output/'runtime'; gate.copy_runtime(runtime)
        for name in (*replay.FILES,'experiments/__init__.py'):
            destination=runtime/name; destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,destination)
        shutil.copy2(ROOT/'experiments/isolation_resource_worker.py',runtime/'resource_worker.py')
        data['runtime_sha256']=observation.tree(runtime)
        account=subprocess.run(['whoami'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()
        gate.command_log(data['acl'],['icacls',str(runtime),'/grant',f'*{data["package_sid"]}:(OI)(CI)RX','/T'])
        def workspace(path):
            path.mkdir()
            gate.command_log(data['acl'],['icacls',str(path),'/grant',f'{account}:(OI)(CI)F',f'*{data["package_sid"]}:(OI)(CI)M'])
            gate.command_log(data['acl'],['icacls',str(path),'/setintegritylevel','(OI)(CI)L'])
        def execute(trial,case,path,resume=False):
            if time.monotonic()-started>280 or shutil.disk_usage(output).free<5*1024**3 or sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>gate.DISK_LIMIT:
                raise RuntimeError('Finite panel limits')
            request=dict(world_id=f'isolation03-trial-{trial}',revision=revision,resume=resume,
                case='reference' if resume or case in {'ordinary','confined'} else case)
            gate.save(path/'request.json',request)
            row=gate.launch(runtime/'python.exe',runtime/'resource_worker.py',path,output/'unused',0,sid,data['package_sid'],case!='ordinary')
            row.update(trial=trial,case=case+'-resume' if resume else case,workspace=path.name,request=request,
                world_started=(path/'world-started').exists())
            data['rows'].append(row); gate.save(output/'evidence.json',data)
            row['observation']=observation.observe(path/'world',revision)
            gate.save(output/'evidence.json',data)
            return row
        for trial in range(2):
            for case in ('ordinary','confined',*CASES):
                path=output/f'{trial}-{case}'; workspace(path); row=execute(trial,case,path)
                if case in {'cpu','memory','wall'}:
                    shutil.copytree(path/'world',path/'before-resume')
                    shutil.copy2(path/'world/frames.jsonl',path/'durable-prefix.jsonl')
                    row['prefix_sha256']=gate.sha(path/'durable-prefix.jsonl')
                    gate.save(output/'evidence.json',data)
                    resumed=execute(trial,case,path,True)
                    resumed['prefix_preserved']=(path/'world/frames.jsonl').read_bytes().startswith((path/'durable-prefix.jsonl').read_bytes())
                    gate.save(output/'evidence.json',data)
    finally:
        if created:
            result=user.DeleteAppContainerProfile(data['profile'])
            data.update(cleanup=result==0,cleanup_hresult=result & 0xffffffff)
        if sid: adv.FreeSid(sid)
        data['elapsed_seconds']=time.monotonic()-started
        gate.save(output/'evidence.json',data)
    return data


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',required=True); p.add_argument('--source-revision',required=True)
    a=p.parse_args(); run_panel(a.output_dir,a.source_revision)
