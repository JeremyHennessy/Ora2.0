"""RESTORE-01 manual independent-backup application recovery panel."""
import argparse
import ctypes as c
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid
import zipfile
from experiments import isolation_capability as gate
from experiments import isolation_world as observation
from experiments import heartbeat_template_audit as replay

ROOT=Path(__file__).resolve().parents[1]
BACKUP=Path('C:/ora/isolation04-20261009/isolation04-integrated-20261009-evidence.zip')
BACKUP_SHA='d1956130ee5c359561e948870b5288f352615ed63edb0118b5861758d2bdc564'
WORLD_REVISION='b5d3104087b397d07c62a45592dde4bc13d58e51'
FILES=(*gate.FILES,*replay.FILES,'experiments/__init__.py','experiments/cold_restore.py',
    'experiments/cold_restore_worker.py','experiments/cold_restore_audit.py','docs/RESTORE-01-CONTRACT.md','docs/RESTORE-01-EXECUTION-ERRATUM.md','docs/RESTORE-01-SETUP-ERRATUM.md')
CORRUPTION=b'\n# RESTORE01 registered source-corruption control\n'


def verify_backup():
    if gate.sha(BACKUP)!=BACKUP_SHA: raise ValueError('Independent archive changed')


def restore_members(archive,prefix,destination):
    destination=Path(destination).resolve(); count=0
    for name in archive.namelist():
        if name.startswith(prefix) and not name.endswith('/'):
            target=destination/name[len(prefix):]
            if not target.resolve().is_relative_to(destination): raise ValueError('Archive path escape')
            target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(archive.read(name)); count+=1
    if not count: raise ValueError('Missing registered backup prefix')


def run_panel(output,revision):
    kernel,adv,user=gate.libraries()
    if len(revision)!=40 or any(x not in '0123456789abcdef' for x in revision): raise ValueError('Exact reviewed adapter source')
    output=Path(output).resolve()
    if output.drive.upper()!='D:' or output.exists(): raise ValueError('Fresh D: output')
    if shutil.disk_usage(output.parent).free<5*1024**3: raise OSError('Space floor')
    verify_backup()
    output.mkdir(); started=time.monotonic(); pointers={}
    data=dict(schema='restore01-v1',revision=revision,world_revision=WORLD_REVISION,
        backup=str(BACKUP),backup_sha256=BACKUP_SHA,panel_root=str(output),source_sha256={p:gate.sha(ROOT/p) for p in FILES},rows=[],profiles={},profile_attempts=[],acl=[])
    def save(): gate.save(output/'evidence.json',data)
    runtime=output/'runtime'; bad=output/'corrupt-runtime'
    try:
        with zipfile.ZipFile(BACKUP) as z:
            original=json.loads(z.read('panel/evidence.json'))
            if original['revision']!=WORLD_REVISION: raise ValueError('Original source revision')
            data['original_profiles']={k:v['sid'] for k,v in original['profiles'].items()}
            restore_members(z,'panel/runtime/',runtime)
            if observation.tree(runtime)!=original['runtime_sha256']: raise ValueError('Copied runtime manifest')
            data['archived_runtime_sha256']=observation.tree(runtime)
            for name in replay.FILES:
                if gate.sha(runtime/name)!=gate.sha(ROOT/name): raise ValueError('Immutable archived world law differs')
            for trial in range(2):
                restore_members(z,f'panel/{trial}-cpu/trusted-snapshot/',output/f'input-{trial}')
                restore_members(z,f'panel/{trial}-confined/world/',output/f'reference-{trial}')
        shutil.copy2(ROOT/'experiments/cold_restore_worker.py',runtime/'restore_worker.py')
        data['runtime_sha256']=observation.tree(runtime)
        shutil.copytree(runtime,bad); (bad/'experiments/heartbeat_template.py').write_bytes((bad/'experiments/heartbeat_template.py').read_bytes()+CORRUPTION)
        data['corrupt_runtime_sha256']=observation.tree(bad)
        account=subprocess.run(['whoami'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()
        for trial in range(2):
            name='OraLab.Integrated.'+uuid.uuid4().hex; sid=c.c_void_p()
            result=user.CreateAppContainerProfile(name,name,'Disposable independent-backup restore',None,0,c.byref(sid))
            data['profile_attempts'].append(dict(name=name,hresult=result & 0xffffffff)); save()
            if result!=0: raise OSError(f'Profile HRESULT {result & 0xffffffff:08x}')
            pointers[trial]=sid; data['profiles'][str(trial)]=dict(name=name,sid=gate.sid_text(sid,kernel,adv),deleted=False); save()
            sid_string=data['profiles'][str(trial)]['sid']
            if sid_string in data['original_profiles'].values(): raise ValueError('Old profile identity reused')
            for root in (runtime,bad): gate.command_log(data['acl'],['icacls',str(root),'/grant',f'*{sid_string}:(OI)(CI)RX','/T'])
            workspace=output/f'world-{trial}'; workspace.mkdir()
            gate.command_log(data['acl'],['icacls',str(workspace),'/inheritance:r','/grant:r',f'{account}:(OI)(CI)F','*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F'])
            gate.command_log(data['acl'],['icacls',str(workspace),'/setintegritylevel','(OI)(CI)L'])
            shutil.copytree(output/f'input-{trial}',workspace/'world')
            identity=json.loads((workspace/'world/manifest.json').read_text(encoding='utf-8'))['identity']
            gate.save(workspace/'request.json',dict(world_id=identity['world_id'],revision=WORLD_REVISION,resume=True))
            for case in ('missing-runtime','ungranted','corrupt-source','restore'):
                if time.monotonic()-started>280 or sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>gate.DISK_LIMIT: raise RuntimeError('Finite panel ceiling')
                if case=='corrupt-source': gate.command_log(data['acl'],['icacls',str(workspace),'/grant',f'*{sid_string}:(OI)(CI)M','/T'])
                for name in ('worker-started','runtime.json','rejection.json'): (workspace/name).unlink(missing_ok=True)
                before=observation.tree(workspace/'world'); root=bad if case=='corrupt-source' else runtime
                row=gate.launch(root/('absent.exe' if case=='missing-runtime' else 'python.exe'),root/'restore_worker.py',workspace,output/'unused',0,sid,sid_string,True)
                row.update(trial=trial,case=case,workspace=workspace.name,runtime=root.name,world_before=before,
                    world_after=observation.tree(workspace/'world'),marker=(workspace/'worker-started').exists())
                report=workspace/'runtime.json'; error=workspace/'rejection.json'
                if report.exists(): row['runtime_report']=json.loads(report.read_text(encoding='utf-8'))
                if error.exists(): row['rejection']=json.loads(error.read_text(encoding='utf-8'))
                data['rows'].append(row); save()
            row['recorded_observation']=observation.observe(workspace/'world',WORLD_REVISION); save()
    finally:
        for trial,sid in pointers.items():
            p=data['profiles'][str(trial)]; result=user.DeleteAppContainerProfile(p['name']); p.update(deleted=result==0,cleanup_hresult=result & 0xffffffff); adv.FreeSid(sid)
        data['elapsed_seconds']=time.monotonic()-started; save()
    if gate.sha(BACKUP)!=BACKUP_SHA: raise ValueError('Input archive modified')
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output-dir',required=True); parser.add_argument('--source-revision',required=True)
    args=parser.parse_args(); run_panel(args.output_dir,args.source_revision)
