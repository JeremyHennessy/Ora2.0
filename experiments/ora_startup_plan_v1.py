"""Export reviewable, disabled current-user logon tasks; never register or reboot."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
NS='http://schemas.microsoft.com/windows/2004/02/mit/task'
ET.register_namespace('',NS)


def task_xml(python,repository,store,sid,continuous=False):
    if not re.fullmatch(r'S-1-5-(?:\d+-)*\d+',sid): raise ValueError('Exact current-user SID required')
    for path in (python,repository,store):
        if not Path(path).is_absolute(): raise ValueError('Absolute startup paths required')
    task=ET.Element('{'+NS+'}Task',version='1.2')
    def child(parent,name,value=None,**attributes):
        item=ET.SubElement(parent,'{'+NS+'}'+name,attributes)
        if value is not None: item.text=value
        return item
    info=child(task,'RegistrationInfo'); child(info,'Description','Ora prepared logon startup; activation and evidence gates apply. No OS reboot action.')
    triggers=child(task,'Triggers'); trigger=child(triggers,'LogonTrigger')
    child(trigger,'Enabled','true'); child(trigger,'UserId',sid); child(trigger,'Delay','PT15S')
    principals=child(task,'Principals'); principal=child(principals,'Principal',id='OraUser')
    child(principal,'UserId',sid); child(principal,'LogonType','InteractiveToken'); child(principal,'RunLevel','LeastPrivilege')
    settings=child(task,'Settings')
    for name,value in (('MultipleInstancesPolicy','IgnoreNew'),('DisallowStartIfOnBatteries','true'),
        ('StopIfGoingOnBatteries','true'),('AllowHardTerminate','true'),('StartWhenAvailable','true'),
        ('RunOnlyIfNetworkAvailable','false'),('AllowStartOnDemand','true'),('Enabled','false'),
        ('Hidden','true'),('RunOnlyIfIdle','false'),('WakeToRun','false'),
        ('ExecutionTimeLimit','PT0S' if continuous else 'PT21M'),('Priority','7')): child(settings,name,value)
    actions=child(task,'Actions',Context='OraUser'); execute=child(actions,'Exec')
    arguments=['-B','-m','experiments.ora_session_host_v1',str(store)]
    if continuous: arguments.append('--continuous')
    child(execute,'Command',str(python)); child(execute,'Arguments',subprocess.list2cmdline(arguments))
    child(execute,'WorkingDirectory',str(repository))
    return ET.tostring(task,encoding='utf-8',xml_declaration=True)


def export(destination,store,sid):
    target=Path(destination); target.mkdir(exist_ok=False)
    for continuous,name in ((False,'reboot-test'),(True,'continuous-startup')):
        raw=task_xml(sys.executable,ROOT,Path(store).resolve(),sid,continuous)
        (target/(name+'.xml')).write_bytes(raw)
    # A preparation manifest is deliberately incapable of starting either task.
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT/'experiments').glob('ora_*_v1.py'))}
    hashes['experiments/process_limits.py']=hashlib.sha256((ROOT/'experiments/process_limits.py').read_bytes()).hexdigest()
    value=dict(schema='ORA-STARTUP-PREPARATION-v1',enabled=False,source_head=head,source_hashes=hashes,
        store=str(Path(store).resolve()),sid=sid,seconds=1200,epoch_seconds=120,practice=1,
        files=['experiments/ora_ollama_prepare_v1.py'],
        required_before_activation=['Passing soak receipt','Current source CI and closure checks','Baseline boot/owner/memory capture','User-selected reboot time'],
        installed=False,physical_reboot_performed=False,continuous_startup_enabled=False)
    (target/'preparation.json').write_text(json.dumps(value,indent=2),encoding='utf8')
    return value


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('destination',type=Path)
    parser.add_argument('store',type=Path); parser.add_argument('sid')
    args=parser.parse_args(); result=export(args.destination,args.store,args.sid)
    print(json.dumps({k:result[k] for k in ('enabled','installed','physical_reboot_performed')}))
