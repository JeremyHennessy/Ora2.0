"""Disposable controller process. A Job launch is forbidden in this probe."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

sys.path.insert(0,str(Path.cwd()))
from experiments import al02_campaign_admission as gate, al02_one_pair_custody as custody
from experiments import al02_one_pair_job as job
from tools import run_al02_campaign as controller
from experiments import al02_one_pair as pair
from tools.al02_campaign_evidence import verify_attempt

root=Path.cwd()
stage=Path(sys.argv[1]).resolve()
pilot = sys.argv[2].startswith('pilot-')
mode = sys.argv[2].removeprefix('pilot-')
assert stage.is_relative_to(Path(os.environ['TEMP']).resolve())
assert stage.name.startswith('ora-controller-probe-')
assert not stage.is_relative_to(gate.DESTINATION)
frozen_binding=gate.binding
frozen_admitted=gate.admitted
frozen_read=gate.read_pinned
original_strict_root=gate.DESTINATION
frozen_root=gate.PILOT_DESTINATION if pilot else gate.DESTINATION
frozen_pilot=gate.pilot_binding
original_pilot_root=gate.PILOT_DESTINATION
frozen_checkout=gate.CHECKOUT
frozen_stop=gate.STOP
live = mode in ('live','after-intent','after-terminal','during-worker','positive')
review_path = stage/'reviewed-admissions.json'
reviewed = json.loads(review_path.read_bytes()) if review_path.exists() else {}
row=gate.inventory()[len(list(stage.glob('attempt-*'))) if pilot else len(reviewed)]
fixture_digest = ('2b92aa5c0d187afcf5031bd6d6d6511a45f6667fc8d4f73530e845531b9cd216'
                  if mode=='positive' else pair.CONTEXT_SHA256)
fixture_seed = 42 if mode=='positive' else pair.SEED
b=frozen_pilot() if pilot else frozen_binding()
historical_command=[b['python'],'-I','-S','-B',b['worker'],
                    str(frozen_root/row['attempt']/'00-pending.json'),gate.TOKEN]
shim=stage/'inert.py'
if not live:
    assert shim.read_bytes()==b'raise AssertionError("Controller crash probe must not launch")\n'
gate_source=Path(gate.__file__)
authority=stage/('pilot-authority.json' if pilot else 'campaign-authority.json')
pin=custody.digest(authority)
pins={str(p):custody.digest(p) for p in (Path(b['python']),shim,
      Path(custody.__file__),Path(job.__file__),root/'experiments/process_limits.py',
      root/'experiments/al02_one_pair.py')}
if live:
    for path in (stage/'lawful.bin',root/'experiments/al02_one_pair_worker.py'):
        pins[str(path)]=custody.digest(path)
physical=dict(b,python=b['python'],worker=str(shim),pins=pins,
              production_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
target=stage/row['attempt']
real_mkdir=Path.mkdir
real_open=Path.open
real_run=job.run

def read_authority(path,expected):
    if path==frozen_root/authority.name:
        path=authority
    return frozen_read(path,expected)

def admit(directory,cwd,command,owner,context,limits,actual_pins):
    selected = next(item for item in gate.inventory() if item['attempt']==directory.name)
    assert cwd==root and directory.parent==stage
    assert pilot or directory==target
    assert list(command)==[b['python'],'-I','-S','-B',str(shim),
                           str(directory/'00-pending.json'),gate.TOKEN]
    assert context in ((selected['context_sha256'],fixture_digest) if live else (selected['context_sha256'],))
    assert actual_pins==dict(pins,**{str(gate_source):custody.digest(gate_source)})
    proposed=[b['python'],'-I','-S','-B',b['worker'],
              str(frozen_root/selected['attempt']/'00-pending.json'),gate.TOKEN]
    with patch.multiple(gate,DESTINATION=original_strict_root,CHECKOUT=frozen_checkout,
                        PILOT_DESTINATION=frozen_root if pilot else original_pilot_root,STOP=frozen_stop,
                        binding=frozen_binding,pilot_binding=frozen_pilot):
        identity=frozen_admitted(frozen_root/selected['attempt'],frozen_checkout,
            proposed,owner,selected['context_sha256'],limits,b['pins'])
    if mode=='before-claim':
        os._exit(41)
    if mode=='hold':
        (stage/'holding').touch()
        until=time.monotonic()+8
        while not (stage/'continue').exists():
            if time.monotonic()>until:raise TimeoutError('Test synchronization')
            time.sleep(.01)
    if pilot or (live and context==fixture_digest):
        return dict(identity,inert_execution=True,committed_seed=selected['seed'],
                    seed=fixture_seed,fixture_context_sha256=fixture_digest)
    return dict(identity,inert_execution=True)

def mkdir(path,*args,**kwargs):
    result=real_mkdir(path,*args,**kwargs)
    if path==target and mode in ('after-claim','hold'):
        os._exit(42)
    return result

def open_probe(path,*args,**kwargs):
    if path==target/'00-pending.json' and mode=='pending-fail' and args==('xb',):
        raise OSError('Injected pending write failure')
    return real_open(path,*args,**kwargs)

def run_probe(*args,**kwargs):
    if mode=='after-intent':
        callback=kwargs['before_go']
        def before_go(*args):
            callback(*args)
            os._exit(44)
        return real_run(*args,**dict(kwargs,before_go=before_go))
    if live:
        return real_run(*args,**kwargs)

    if mode=='after-pending':
        os._exit(43)
    raise AssertionError('No-World barrier: transport prohibited in crash probe')

def fixture_context(index, name):
    return dict(index=index,attempt=name,context=pair.CONTEXT,
                context_sha256=pair.CONTEXT_SHA256,seed=pair.SEED)

def fixture_review(root, ordered, admissions):
    rows=[]
    for index, admission in sorted(admissions.items()):
        committed=ordered[index]
        assert admission['identities']['inert_execution'] is True
        assert admission['identities']['committed_seed']==committed['seed']
        rows.append(verify_attempt(root/committed['attempt'],
                    fixture_context(index,committed['attempt']),**admission))
    return dict(rows=rows)

real_transaction=custody.transaction
def fixture_transaction(directory, **kwargs):
    assert directory==target and kwargs['command'][4]==str(shim)
    assert kwargs['context']==row['context_sha256']
    result=real_transaction(directory, **dict(kwargs,context=fixture_digest))
    if mode=='after-terminal':
        os._exit(45)
    return result

if mode=='before-lock':
    os._exit(40)
with patch.multiple(gate,DESTINATION=stage,CHECKOUT=root,STOP=stage/'STOP',
                    AUTHORIZATION_SHA256=pin if not pilot else None,
                    PILOT_AUTHORIZATION_SHA256=pin if pilot else None,
                    PILOT_DESTINATION=stage if pilot else original_pilot_root,
                    pilot_binding=lambda:physical,
                    binding=lambda:physical,admitted=admit,read_pinned=read_authority), \
     patch.object(Path,'mkdir',mkdir), patch.object(Path,'open',open_probe), patch.object(job,'run',run_probe), \
     patch.object(controller.shutil,'disk_usage',
                  (lambda _: type('Disk',(),{'free':0})()) if mode=='capacity' else controller.shutil.disk_usage), \
     patch.object(custody,'transaction',fixture_transaction if live else real_transaction), \
     patch.object(controller,'analyze_committed_panel',
                  fixture_review if live else controller.analyze_committed_panel):
    try:
        start_wall=time.monotonic()
        start_cpu=time.process_time()
        result=controller.run_next(pilot=pilot)
    except (OSError,ValueError) as error:
        print(f'{type(error).__name__}: {error}')
        sys.exit(10)
    else:
        if live:
            assert result['contrast']==(3 if mode=='positive' else 0)
            print(json.dumps(dict(result=result,controller_cpu_seconds=time.process_time()-start_cpu,
                                  controller_total_wall_seconds=time.monotonic()-start_wall)))
        else:
            assert result is None
            print('STOP')
