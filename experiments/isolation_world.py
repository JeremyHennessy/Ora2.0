"""ISOLATION-02 explicit finite-world confinement/continuity composition."""
import argparse
import ctypes as c
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

from experiments import isolation_capability as gate
from experiments import heartbeat_template_audit as replay

ROOT = Path(__file__).resolve().parents[1]
POINTS = ('pre_commit','post_journal','post_pending','post_checkpoint')
FILES = (*gate.FILES, *replay.FILES, 'experiments/__init__.py',
         'experiments/isolation_world.py', 'experiments/isolation_world_worker.py',
         'experiments/isolation_world_audit.py', 'docs/ISOLATION-02-CONTRACT.md')


def tree(folder):
    return {p.relative_to(folder).as_posix(): gate.sha(p) for p in Path(folder).rglob('*') if p.is_file()}


def observe(folder, revision):
    before = tree(folder)
    evidence = replay.inspect(folder, revision)
    current = datetime.fromisoformat(evidence['frames'][-1]['last_heartbeat'])
    report = replay.inspect(folder, revision, current=current)['report']
    if tree(folder) != before:
        raise RuntimeError('Read-only observation modified world')
    return dict(recorded=True, report=report, world_tree_sha256=before,
                states_sha256=replay.digest(evidence['states']),
                events_sha256=replay.digest([f['event'] for f in evidence['frames'] if f['event'] is not None]))


def run_panel(output, revision):
    kernel, adv, user = gate.libraries()
    if len(revision) != 40 or any(char not in '0123456789abcdef' for char in revision):
        raise ValueError('Exact reviewed revision')
    output = Path(output).resolve()
    if output.drive.upper() != 'D:' or output.exists():
        raise ValueError('Fresh D: output required')
    if shutil.disk_usage(output.parent).free < 5*1024**3:
        raise OSError('5 GB floor')
    output.mkdir()
    data = dict(schema='isolation02-v1', revision=revision, source_sha256={p:gate.sha(ROOT/p) for p in FILES},
                profile='OraLab.IsolationWorld.'+uuid.uuid4().hex, rows=[], acl=[], cleanup=False)
    sid, created = c.c_void_p(), False
    started = time.monotonic()
    try:
        result = user.CreateAppContainerProfile(data['profile'], data['profile'], 'Bounded world continuity fixture', None, 0, c.byref(sid))
        if result != 0:
            raise OSError(f'Create profile HRESULT {result & 0xffffffff:08x}')
        created = True
        data['package_sid'] = gate.sid_text(sid, kernel, adv)
        gate.save(output/'evidence.json',data)
        runtime = output/'runtime'
        gate.copy_runtime(runtime)
        for name in (*replay.FILES, 'experiments/__init__.py'):
            destination=runtime/name
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,destination)
        # The launcher's inert-worker pathname is replaced only for this new fixture.
        shutil.copy2(ROOT/'experiments/isolation_world_worker.py',runtime/'world_worker.py')
        data['runtime_sha256']=tree(runtime)
        account=subprocess.run(['whoami'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()
        gate.command_log(data['acl'],['icacls',str(runtime),'/grant',f'*{data["package_sid"]}:(OI)(CI)RX','/T'])
        def workspace(path):
            path.mkdir()
            gate.command_log(data['acl'],['icacls',str(path),'/grant',f'{account}:(OI)(CI)F',f'*{data["package_sid"]}:(OI)(CI)M'])
            gate.command_log(data['acl'],['icacls',str(path),'/setintegritylevel','(OI)(CI)L'])
        def execute(trial, case, path, resume=False, point=None, fault=None, wrong=False):
            if time.monotonic()-started>280 or sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>gate.DISK_LIMIT:
                raise RuntimeError('Finite panel time/disk ceiling')
            identity=f'isolation02-trial-{trial}'
            request=dict(world_id=identity+'-wrong' if wrong else identity, revision=revision,resume=resume,point=point)
            gate.save(path/'request.json',request)
            row=gate.launch(runtime/('absent.exe' if fault=='missing' else 'python.exe'),
                runtime/'world_worker.py',path,output/'unused-canary',0,sid,data['package_sid'],
                case!='ordinary',fault if fault in {'job','token'} else None)
            row.update(trial=trial,case=case,workspace=path.name,request=request,
                       world_started=(path/'world-started').exists(),world_exists=(path/'world').exists())
            data['rows'].append(row)
            gate.save(output/'evidence.json',data)
            return row
        for trial in range(2):
            for case in ('ordinary','confined'):
                path=output/f'{trial}-{case}'; workspace(path)
                row=execute(trial,case,path)
                row['observation']=observe(path/'world',revision)
                gate.save(output/'evidence.json',data)
            path=output/f'{trial}-confined'
            before=tree(path/'world')
            row=execute(trial,'identity-rejection',path,resume=True,wrong=True)
            row.update(world_before=before,world_after=tree(path/'world'))
            gate.save(output/'evidence.json',data)
            for point in POINTS:
                path=output/f'{trial}-{point}'; workspace(path)
                row=execute(trial,point+'-interrupt',path,point=point)
                row['observation']=observe(path/'world',revision)
                durable=path/'world/frames.jsonl'
                prefix=path/'durable-prefix.jsonl'; shutil.copy2(durable,prefix)
                row['prefix_sha256']=gate.sha(prefix)
                before=path/'before-resume'; shutil.copytree(path/'world',before)
                gate.save(output/'evidence.json',data)
                row=execute(trial,point+'-resume',path,resume=True)
                row['observation']=observe(path/'world',revision)
                row['prefix_preserved']=durable.read_bytes().startswith(prefix.read_bytes())
                gate.save(output/'evidence.json',data)
            for fault in ('missing','job','token'):
                path=output/f'{trial}-setup-{fault}'; workspace(path)
                execute(trial,'setup-'+fault,path,fault=fault)
    finally:
        if created:
            result=user.DeleteAppContainerProfile(data['profile'])
            data.update(cleanup=result==0,cleanup_hresult=result & 0xffffffff)
        if sid:
            adv.FreeSid(sid)
        data['elapsed_seconds']=time.monotonic()-started
        gate.save(output/'evidence.json',data)
    return data


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--source-revision',required=True)
    args=parser.parse_args()
    run_panel(args.output_dir,args.source_revision)
