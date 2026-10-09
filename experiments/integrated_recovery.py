"""Bounded ISOLATION-04 one-world integrated recovery; no service mode."""
import argparse
import ctypes as c
from pathlib import Path
import shutil
import subprocess
import time
import uuid
from experiments import isolation_capability as gate
from experiments import isolation_world as observation
from experiments import isolation_resource as resource

ROOT=Path(__file__).resolve().parents[1]
FILES=(*resource.FILES,'experiments/integrated_recovery.py','experiments/integrated_recovery_worker.py',
       'experiments/integrated_recovery_audit.py','docs/ISOLATION-04-CONTRACT.md')


def run_panel(output,revision):
    kernel,adv,user=gate.libraries()
    if len(revision)!=40 or any(x not in '0123456789abcdef' for x in revision): raise ValueError('Exact source')
    output=Path(output).resolve()
    if output.drive.upper()!='D:' or output.exists(): raise ValueError('Fresh D: output')
    if shutil.disk_usage(output.parent).free<5*1024**3: raise OSError('Space floor')
    output.mkdir(); started=time.monotonic(); pointers={}
    data=dict(schema='isolation04-v1',revision=revision,source_sha256={p:gate.sha(ROOT/p) for p in FILES},rows=[],profiles={},acl=[])
    def save(): gate.save(output/'evidence.json',data)
    def profile(label):
        sid=c.c_void_p(); name='OraLab.Integrated.'+uuid.uuid4().hex
        result=user.CreateAppContainerProfile(name,name,'Disposable integrated recovery',None,0,c.byref(sid))
        if result!=0: raise OSError(f'Profile HRESULT {result & 0xffffffff:08x}')
        pointers[label]=sid; data['profiles'][label]=dict(name=name,sid=gate.sid_text(sid,kernel,adv),deleted=False)
        save(); gate.command_log(data['acl'],['icacls',str(runtime),'/grant',f'*{data["profiles"][label]["sid"]}:(OI)(CI)RX','/T'])
    def delete(label):
        p=data['profiles'][label]; result=user.DeleteAppContainerProfile(p['name'])
        p.update(deleted=result==0,cleanup_hresult=result & 0xffffffff,deleted_at_launch=len(data['rows'])); save()
        if result!=0: raise OSError('Profile cleanup failed')
    try:
        runtime=output/'runtime'; gate.copy_runtime(runtime)
        for name in (*observation.replay.FILES,'experiments/__init__.py','experiments/isolation_resource_worker.py'):
            target=runtime/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/name,target)
        shutil.copy2(ROOT/'experiments/integrated_recovery_worker.py',runtime/'integrated_worker.py')
        data['runtime_sha256']=observation.tree(runtime)
        account=subprocess.run(['whoami'],capture_output=True,text=True,check=True,timeout=10).stdout.strip()
        def workspace(path,label=None):
            path.mkdir()
            gate.command_log(data['acl'],['icacls',str(path),'/inheritance:r','/grant:r',f'{account}:(OI)(CI)F','*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F'])
            gate.command_log(data['acl'],['icacls',str(path),'/setintegritylevel','(OI)(CI)L'])
            if label is not None: grant(path,label)
        def grant(path,label):
            gate.command_log(data['acl'],['icacls',str(path),'/grant',f'*{data["profiles"][label]["sid"]}:(OI)(CI)M','/T'])
        def execute(trial,case,path,label,resume=False,fixture='reference',confined=True):
            if time.monotonic()-started>280 or shutil.disk_usage(output).free<5*1024**3 or sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>gate.DISK_LIMIT: raise RuntimeError('Finite panel limits')
            request=dict(world_id=f'isolation04-trial-{trial}',revision=revision,resume=resume,case=fixture)
            gate.save(path/'request.json',request)
            row=gate.launch(runtime/'python.exe',runtime/'integrated_worker.py',path,output/'unused',0,pointers[label],data['profiles'][label]['sid'],confined)
            row.update(trial=trial,case=case,workspace=path.name,profile=label,request=request,world_started=(path/'world-started').exists())
            data['rows'].append(row); save(); return row
        restores=[]
        for trial in range(2):
            old=f'{trial}-original'; profile(old)
            for case in ('ordinary','confined'):
                path=output/f'{trial}-{case}'; workspace(path,old)
                execute(trial,case,path,old,confined=case!='ordinary')
            for kind,io in (('cpu','journal'),('memory','pending'),('wall','replace')):
                path=output/f'{trial}-{kind}'; workspace(path,old)
                execute(trial,kind+'-resource',path,old,fixture=kind)
                shutil.copytree(path/'world',path/'before-resource-resume')
                execute(trial,kind+'-io',path,old,True,'io-'+io)
                shutil.copytree(path/'world',path/'before-io-resume')
                before=observation.tree(path/'world')
                row=execute(trial,kind+'-direct',path,old,True)
                row.update(world_before=before,world_after=observation.tree(path/'world')); save()
                new=f'{trial}-{kind}-new'; profile(new)
                restored=output/f'{trial}-{kind}-restored'; workspace(restored)
                src=path/('trusted-snapshot' if io=='journal' else 'before-io-resume')
                shutil.copytree(src,restored/'world')
                before=observation.tree(restored/'world')
                row=execute(trial,kind+'-ungranted',restored,new,True)
                row.update(world_before=before,world_after=observation.tree(restored/'world')); save()
                grant(restored,new)
                row=execute(trial,kind+'-wrong-sid',restored,old,True)
                row.update(world_before=before,world_after=observation.tree(restored/'world')); save()
                shutil.copytree(restored/'world',restored/'before-new-resume')
                restores.append((trial,kind,restored,new))
            delete(old)
            for t,kind,path,new in [r for r in restores if r[0]==trial]:
                row=execute(t,kind+'-restored',path,new,True)
                row['observation']=observation.observe(path/'world',revision); save(); delete(new)
    finally:
        for label,sid in pointers.items():
            if not data['profiles'][label]['deleted']:
                try: delete(label)
                except OSError as error: data['profiles'][label]['cleanup_error']=str(error)
            adv.FreeSid(sid)
        data['elapsed_seconds']=time.monotonic()-started; save()
    return data


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir',required=True); p.add_argument('--source-revision',required=True)
    a=p.parse_args(); run_panel(a.output_dir,a.source_revision)
