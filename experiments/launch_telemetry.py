"""LAUNCH-01 fixed native capability launch and read-only actual-state observation."""
import argparse
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from types import SimpleNamespace
import uuid
from experiments import isolation_capability as gate
from experiments import heartbeat_template as world
from experiments import heartbeat_template_audit as replay
from experiments import world_telemetry as telemetry
from experiments.process_limits import Job,checked,process_exited

ROOT=Path(__file__).resolve().parents[1]
FILES=tuple(dict.fromkeys((*gate.FILES,*replay.FILES,'experiments/__init__.py','experiments/world_telemetry.py','experiments/launch_telemetry.py','experiments/launch_telemetry_worker.py','experiments/launch_telemetry_audit.py','docs/LAUNCH-01-CONTRACT.md','docs/LAUNCH-01-STORAGE-ERRATUM.md')))


def identity(world_id,revision):
    value=dict(world_id=world_id,source_revision=revision,config_sha256=replay.digest(dict(seed=1,work=2,max_ticks=32)),python=__import__('platform').python_version(),source_sha256=replay.source_hashes())
    value['run_id']=replay.digest(value);return value


def native(runtime,workspace,sid,sid_string,expected):
    kernel,adv,_=gate.libraries();process=gate.Process();attributes=None;job=None;started=time.monotonic()
    row=dict(pid=None,resumed=False,samples=[],read_only=[],expected_identity=expected)
    try:
        startup=gate.StartupEx();startup.startup.cb=c.sizeof(startup);size=c.c_size_t()
        kernel.InitializeProcThreadAttributeList(None,1,0,c.byref(size));attributes=c.create_string_buffer(size.value)
        checked(kernel.InitializeProcThreadAttributeList(attributes,1,0,c.byref(size)));caps=gate.Capabilities(sid,None,0,0)
        checked(kernel.UpdateProcThreadAttribute(attributes,0,0x20009,c.byref(caps),c.sizeof(caps),None,None));startup.attributes=c.cast(attributes,c.c_void_p)
        environment=c.create_unicode_buffer('\0'.join(f'{k}={v}' for k,v in sorted(dict(SystemRoot=os.environ['SystemRoot'],TEMP=str(workspace),TMP=str(workspace),LOCALAPPDATA=str(workspace)).items()))+'\0\0')
        args=[str(runtime/'python.exe'),'-I','-B',str(runtime/'worker.py'),str(workspace)]
        checked(kernel.CreateProcessW(args[0],c.create_unicode_buffer(subprocess.list2cmdline(args)),None,None,False,0x4|0x08000000|0x400|0x80000,environment,str(workspace),c.byref(startup),c.byref(process)))
        row['pid']=process.pid;row['token']=gate.token_info(process.process,kernel,adv)
        if row['token']!=dict(is_appcontainer=True,capabilities=0,package_sid=sid_string):raise RuntimeError('Suspended capability token refusal')
        probe=telemetry.process_sample(process.pid)
        if not probe.get('verified') or not probe.get('alive'):raise RuntimeError('Suspended native birth unavailable')
        binding=dict(pid=process.pid,birth_filetime=probe['birth_filetime'],**{k:expected[k] for k in ('world_id','run_id','source_revision')});row['binding']=binding
        binding_path=workspace.parent/'operator-bindings'/f'{sid_string}.json'
        gate.save(binding_path,binding);row['binding_path']=str(binding_path);row['binding_before_sha256']=gate.sha(binding_path)
        job=Job(SimpleNamespace(memory_bytes=128*1024**2,cpu_seconds=5,processes=1));job.assign(SimpleNamespace(_handle=process.process));row['job_before']=job.usage()
        if kernel.ResumeThread(process.thread)!=1:raise RuntimeError('Suspended resume failed')
        row['resumed']=True;previous=None;handled=set();request=json.loads((workspace/'request.json').read_bytes());ticks=(5,6,7) if request['resume'] else (1,2,5)
        def sample(label,old=None,using=None):
            before=telemetry.hashes(workspace/'world');result=telemetry.sample(workspace/'world',expected['source_revision'],binding if using is None else using,old)
            after=telemetry.hashes(workspace/'world');row['read_only'].append(dict(label=label,before=before,after=after));row['samples'].append(dict(label=label,value=result));return result
        while kernel.WaitForSingleObject(process.process,10)==258:
            if time.monotonic()-started>30:job.terminate();raise RuntimeError('Finite native wall ceiling')
            try:tick=json.loads((workspace/'hold.json').read_bytes())['tick']
            except (OSError,ValueError,KeyError):continue
            if tick in handled:continue
            if tick not in ticks:raise ValueError('Unregistered scheduling hold')
            handled.add(tick);current=sample('first' if tick==ticks[0] else 'advance',previous);previous=current
            sample('same-tick',current)
            sample('wrong-birth',current,dict(binding,birth_filetime=binding['birth_filetime']+1))
            sample('wrong-world',current,dict(binding,world_id='wrong-operator-world'))
            sample('wrong-prefix',dict(current,frame_sha256='0'*64))
            before=telemetry.hashes(workspace/'world');recorded=telemetry.sample(workspace/'world',expected['source_revision']);row['samples'].append(dict(label='recorded',value=recorded));row['read_only'].append(dict(label='recorded',before=before,after=telemetry.hashes(workspace/'world')))
            if tick==ticks[1]:
                wait=time.monotonic()
                while time.monotonic()-wait<5.25:time.sleep(0.05)
                row['expiry_wait_seconds']=time.monotonic()-wait;previous=sample('expired-alive',current)
            gate.save(workspace/'release.pending',dict(tick=tick));(workspace/'release.pending').replace(workspace/'release.json')
        code=w.DWORD();checked(kernel.GetExitCodeProcess(process.process,c.byref(code)));row['exit_code']=code.value
        sample('stopped',previous);row['job_after']=job.usage();row['handled_ticks']=sorted(handled);row['binding_after_sha256']=gate.sha(binding_path)
    except (OSError,RuntimeError,ValueError,KeyError,TypeError) as error:row['error']=str(error)
    finally:
        if process.process and kernel.WaitForSingleObject(process.process,0)==258:gate.terminate_and_wait(kernel,process.process)
        if job:row['job_after']=job.usage();job.close()
        for handle in (process.thread,process.process):
            if handle:checked(kernel.CloseHandle(handle))
        if attributes is not None:kernel.DeleteProcThreadAttributeList(attributes)
        row['stopped']=process_exited(row['pid']) if row['pid'] else True;row['elapsed_seconds']=time.monotonic()-started
    return row


def panel(output,revision):
    kernel,adv,user=gate.libraries();current=kernel.GetCurrentProcess;current.restype=w.HANDLE
    if gate.token_info(current(),kernel,adv)['is_appcontainer']:raise OSError('Ordinary host required; nested confinement refused')
    if len(revision)!=40 or any(x not in '0123456789abcdef' for x in revision):raise ValueError('Exact reviewed source')
    output=Path(output).resolve()
    if output.drive.upper()!='D:' or output.exists() or shutil.disk_usage(output.parent).free<5*1024**3:raise ValueError('Fresh D: output/floor')
    output.mkdir();data=dict(schema='launch01-v1',revision=revision,source_sha256={p:gate.sha(ROOT/p) for p in FILES},rows=[],acl=[],profiles=[]);started=time.monotonic()
    runtime=output/'runtime';gate.copy_runtime(runtime)
    for name in (*replay.FILES,'experiments/__init__.py'):
        path=runtime/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,path)
    shutil.copy2(ROOT/'experiments/launch_telemetry_worker.py',runtime/'worker.py');data['runtime_sha256']={p.relative_to(runtime).as_posix():gate.sha(p) for p in runtime.rglob('*') if p.is_file()}
    account=subprocess.run(['whoami'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()
    binding_folder=output/'operator-bindings';binding_folder.mkdir()
    gate.command_log(data['acl'],['icacls',str(binding_folder),'/inheritance:r','/grant:r',f'{account}:(OI)(CI)F','*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F'])
    try:
        for trial in range(2):
            expected=identity(f'launch01-trial-{trial}',revision)
            for case in ('reference','resource','resume'):
                if time.monotonic()-started>280 or sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>256*1024**2:raise RuntimeError('Finite panel ceiling')
                path=output/f'{trial}-{("resource" if case=="resume" else case)}'
                if case!='resume':path.mkdir()
                profile='OraLab.Launch.'+uuid.uuid4().hex;sid=c.c_void_p();created=False;profile_row=dict(name=profile)
                try:
                    hr=user.CreateAppContainerProfile(profile,profile,'Finite real-launch telemetry fixture',None,0,c.byref(sid))
                    if hr!=0:raise OSError(f'Profile HRESULT {hr & 0xffffffff:08x}')
                    created=True;profile_row['sid']=gate.sid_text(sid,kernel,adv);data['profiles'].append(profile_row)
                    gate.command_log(data['acl'],['icacls',str(runtime),'/grant',f'*{profile_row["sid"]}:(OI)(CI)RX','/T'])
                    gate.command_log(data['acl'],['icacls',str(path),'/grant',f'{account}:(OI)(CI)F',f'*{profile_row["sid"]}:(OI)(CI)M','/T'])
                    gate.command_log(data['acl'],['icacls',str(path),'/setintegritylevel','(OI)(CI)L','/T'])
                    if case=='resume':shutil.copy2(path/'world/frames.jsonl',path/'before-resume.jsonl')
                    for name in ('hold.json','release.json'):
                        if (path/name).exists():(path/name).unlink()
                    gate.save(path/'request.json',dict(world_id=expected['world_id'],revision=revision,resume=case=='resume',resource=case=='resource',binding_path=str(binding_folder/f'{profile_row["sid"]}.json')))
                    row=native(runtime,path,sid,profile_row['sid'],expected);row.update(trial=trial,case=case,workspace=path.name,package_sid=profile_row['sid'])
                    # Preserve per-launch operator evidence before the next launch overwrites scheduling files.
                    evidence=output/f'{trial}-{case}-launch';evidence.mkdir()
                    shutil.copy2(binding_folder/f'{profile_row["sid"]}.json',evidence/'launch-binding.json')
                    for name in ('binding-probe.json','origins.json','resource-result.json','rejection.json','request.json','hold.json','release.json'):
                        if (path/name).exists():shutil.copy2(path/name,evidence/name)
                    data['rows'].append(row);gate.save(output/'evidence.json',data)
                    if 'error' in row or row.get('exit_code')!=(86 if case=='resource' else 0):raise RuntimeError('Native launch failed; preserve')
                finally:
                    if created:profile_row['deleted']=user.DeleteAppContainerProfile(profile)==0
                    if sid:adv.FreeSid(sid)
                    gate.save(output/'evidence.json',data)
    finally:data['elapsed_seconds']=time.monotonic()-started;gate.save(output/'evidence.json',data)
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True);parser.add_argument('--source-revision',required=True);a=parser.parse_args();panel(a.output_dir,a.source_revision)
