import hashlib,json,subprocess,sys
from copy import deepcopy
from pathlib import Path
from random import Random
from types import SimpleNamespace as Row
from unittest.mock import patch
from experiments import al02_one_pair as pair, al02_one_pair_consent as c
from experiments import al02_one_pair_custody as custody, al02_one_pair_job as job
from experiments.al02_depletion_checkpoint import _canonical
from experiments.al02_depletion_projection import fork_depletion
from tests import test_al02_depletion_integration as fixture
root=Path.cwd()
out=Path(sys.argv[1]).resolve()
helpers = root / 'tests/al02_release_rehearsal'
real_gate = c.require_bound_worker
frozen_scope = {name: getattr(c, name) for name in (
    'WORKTREE', 'ATTEMPT', 'WORKER', 'STOP', 'CONSENT', 'CONTEXT', 'SEED',
    'V2_DRAFT', 'V2_BINDING', 'V2_PACKAGE', 'CANDIDATE_WORKER')}
final = json.loads((c.V2_DRAFT / 'installed-binding-v2.json').read_bytes())
final_authority = out / 'candidate-scientific-authorization-v2.json'
final_authority.write_bytes(_canonical(dict(
    schema='AL02-CANDIDATE-ONE-ATTEMPT-v2', worker_sha256=c.CANDIDATE_WORKER,
    binding_sha256=c.V2_BINDING, package_sha256=c.V2_PACKAGE,
    seed=str(c.SEED), attempt=str(c.ATTEMPT), owner=c.OWNER)))

final_authority_pin = hashlib.sha256(final_authority.read_bytes()).hexdigest()
assert out.is_dir() and not (out/'lawful').exists()
assert out != c.ATTEMPT.parent and not c.ATTEMPT.exists()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def records(rows):
    return [dict(zip(fixture._PAIR_COLUMNS[row[0]],deepcopy(row[1:]),strict=True)) for row in rows]
state=deepcopy(fixture._PAIR_STATE)
actors=state.pop('organisms')
for actor in actors:
    for field in ('tape','nursery'):
        actor[field]=[Row(op=op,material_unit=unit) for op,unit in actor[field]]
state.update(organisms={a['organism_id']:Row(**a) for a in actors},
             events=records(fixture._PAIR_PREFIX),births=records(fixture._PAIR_BIRTHS))
rng=Random(42)
for _ in range(31):
    if rng.random()<.08:rng.randrange(5)
config=dict(seed=42,variant='mutating',copy_enabled=True,mutation_rate=.08,
            material_units=256,population_limit=64,genesis_energy=604,genesis_material=256,
            initial_food_a=12,initial_food_b=18)
source=root/'experiments/executed_heredity.py'
checkpoint,pin,_=fork_depletion(Row(**config,**state,rng=rng),source.read_bytes(),
                               hashlib.sha256(_canonical(config)).hexdigest())
context=hashlib.sha256(b'ORA PHASE6 INERT FIXTURE 42').hexdigest()
payload=dict(context_sha256=context,checkpoint=checkpoint.decode('ascii'),checkpoint_sha256=pin,
             branches={r:dict(role=r,prefix_sha256=pin,events=records(rows))
                       for r,rows in [('accessible',fixture._PAIR_ACCESSIBLE),
                                      ('sequestered',fixture._PAIR_SEQUESTERED)]})
(out/'lawful.bin').write_bytes(_canonical(payload))
write=next(e for e in payload['branches']['accessible']['events'] if e['kind']=='COPY_WRITE')
write['material_unit']+=1
(out/'forged.bin').write_bytes(_canonical(payload))
shim=out/'inert-worker.py'

worker = root/'experiments/al02_one_pair_worker.py'
paths = [Path(sys.executable), shim, worker, Path(c.__file__), Path(custody.__file__), Path(pair.__file__),
         Path(job.__file__), Path(job.__file__).with_name('process_limits.py'),
         out/'lawful.bin', out/'forged.bin']
pins = {str(p):sha(p) for p in paths}
head = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
original_attempt = c.ATTEMPT
authority = 'ORA-PHASE6-INERT'
results = {}
for name in ('lawful','forged','interrupt','wrong-pin','stop','no-authority','race','substitute','auth-swap','pending-fail','receipt-swap','late-stop','crash-boundary'):
    stage = out/name
    stage.mkdir()
    attempt = stage/name
    for filename in ('lawful.bin','forged.bin'):
        (stage/filename).write_bytes((out/filename).read_bytes())
    local_pins = {**pins, **{str(stage/f):sha(stage/f) for f in ('lawful.bin','forged.bin')}}
    stop = stage/'FIXTURE-STOP'
    command = [sys.executable,'-I','-S','-B',str(shim),str(attempt/'00-pending.json'),authority]
    relay = job.relay_argv(sys.executable,command)
    old_binding = stage/'legacy.json'
    old_binding.write_bytes(b'{}')
    binding = stage/'installed-binding-v2.json'
    package = stage/'human-release-package-v2.json'
    inventory=stage/'source-pins-v2.json'
    inventory.write_bytes(_canonical(local_pins))
    binding.write_bytes(_canonical(dict(schema='ora.al02.installed-binding.v2',
        candidate_commit=head,production_git_head=head, scientific_authorization=False,
        consent_active_for_candidate=False, proposed_command=command,proposed_relay_argv=relay,
        context_sha256=context,seed=42,limits=c.LIMITS,candidate_worker_sha256=sha(shim),
        attempt=str(attempt),source_inventory_sha256=sha(inventory),installed_file_pins=local_pins)))
    package.write_bytes(_canonical(dict(schema='AL02-INACTIVE-HUMAN-RELEASE-PACKAGE-v2',
        artifact_sha256={'installed-binding-v2.json':sha(binding),'source-pins-v2.json':sha(inventory)},candidate=head,
        production_head=head,scientific_authorization=False,seed='42',attempt=str(attempt))))
    auth=stage/'candidate-scientific-authorization-v2.json'
    auth.write_bytes(_canonical(dict(schema='AL02-CANDIDATE-ONE-ATTEMPT-v2',worker_sha256=sha(shim),
        binding_sha256=sha(binding),package_sha256=sha(package),seed='42',attempt=str(attempt),owner=c.OWNER)))
    if name in ('race','crash-boundary'):
        import time
        config = dict(command=command,pins=local_pins,scope=dict(
            WORKTREE=str(root), ATTEMPT=str(attempt), WORKER=str(shim), STOP=str(stop),
            CONSENT=authority,CONTEXT=context,SEED=42,BINDING=str(old_binding),
            V2_DRAFT=str(stage),CANDIDATE_WORKER=sha(shim),V2_BINDING=sha(binding),
            V2_PACKAGE=sha(package),V2_AUTHORIZATION_SHA256=sha(auth)))
        path=stage/'race.json'
        path.write_bytes(_canonical(config))
        helper=helpers / 'race-claimant.py'
        if name=='crash-boundary':
            (stage/'go').touch()
            crash = helper.with_name('crash-claimant.py')
            def invoke(mode):
                return subprocess.run([sys.executable,'-I','-B','-S',str(crash),str(path),mode],
                                      capture_output=True,text=True,timeout=15)
            before = invoke('before')
            assert before.returncode==41 and not attempt.exists(), before
            after = invoke('after')
            assert after.returncode==42 and attempt.is_dir() and not list(attempt.iterdir()), after
            restart=invoke('restart')
            assert restart.returncode==0 and restart.stdout.strip()=='claim lost', restart
            assert not list(attempt.iterdir())
            results[name]=dict(before=41,after=42,restart='claim lost',state='empty claim retained')
            continue
        with subprocess.Popen([sys.executable,'-I','-B','-S',str(helper),str(path),'a'],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) as a, \
             subprocess.Popen([sys.executable,'-I','-B','-S',str(helper),str(path),'b'],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) as b:
            deadline=time.monotonic()+8
            while not all((stage/f'ready-{n}').exists() for n in ('a','b')):
                if time.monotonic()>deadline:
                    raise TimeoutError('Claimants not ready')
                time.sleep(.01)
            (stage/'go').touch()
            observations=[p.communicate(timeout=15) for p in (a,b)]
        assert sorted(row[0].strip() for row in observations)==['claim lost','claim won'],observations
        assert (attempt/'04-terminal.json').exists()
        results[name]=dict(claimants=[a.pid,b.pid],outputs=observations)
        continue
    if name=='stop': stop.touch()
    called=[]
    def referee(data):
        called.append(hashlib.sha256(data).hexdigest())
        return pair.verify(data)
    referee.__name__ = 'verify'
    with patch.multiple(c,WORKTREE=root,ATTEMPT=attempt,WORKER=shim,STOP=stop,
                        CONSENT=authority,CONTEXT=context,SEED=42,BINDING=old_binding,
                        V2_DRAFT=stage,CANDIDATE_WORKER=sha(shim),
                        V2_BINDING=sha(binding),V2_PACKAGE=sha(package),
                        V2_AUTHORIZATION_SHA256=None if name=='no-authority' else sha(auth)), \
         patch.multiple(pair,SEED=42,CONTEXT_SHA256=context):
        real_run = job.run
        real_open = Path.open
        def altered_run(*args, **kwargs):
            if name == 'auth-swap':
                auth.write_bytes(b'{}')
            return real_run(*args, **kwargs)
        def altered_open(path, *args, **kwargs):
            mode = args[0] if args else kwargs.get('mode')
            if path == attempt/'00-pending.json' and mode == 'xb' and name == 'pending-fail':
                raise OSError('injected pending write failure')
            if path == attempt/'02-release-intent.json' and mode == 'xb':
                if name == 'receipt-swap':
                    (attempt/'00-pending.json').write_bytes(b'{}')
                if name == 'late-stop':
                    stop.touch()
            return real_open(path,*args,**kwargs)
        def run():
            if name in ('auth-swap','pending-fail','receipt-swap','late-stop','crash-boundary'):
                with patch.object(job,'run',altered_run), patch.object(Path,'open',altered_open):
                    return transact()
            return transact()
        def checked_inert_admission(actual_pins, actual_command, actual_relay):
            fixture_identity = real_gate(actual_pins, actual_command, actual_relay)
            if fixture_identity is None or actual_command != tuple(command):
                raise ValueError('Expected exact inert custody scope')
            if attempt.resolve().parent != stage.resolve() or not attempt.is_relative_to(out):
                raise ValueError('Unexpected inert evidence destination')
            if tuple(actual_command[4:]) != (str(shim), str(attempt/'00-pending.json'), authority):
                raise ValueError('Scientific command prohibited')
            with patch.multiple(c, **frozen_scope, BINDING=out/'unused',
                                V2_AUTHORIZATION_SHA256=final_authority_pin):
                identity = real_gate(final['installed_file_pins'], final['proposed_command'],
                                     final['proposed_relay_argv'])
            return dict(identity, source_inventory_sha256=final['source_inventory_sha256'],
                        inert_execution=dict(
                            scientific_dispatch=False, fixture_authorization_sha256=fixture_identity['authorization_sha256'],
                            fixture_binding_sha256=fixture_identity['binding_sha256'],
                            fixture_package_sha256=fixture_identity['package_sha256'],
                            worker_sha256=actual_pins[str(shim)], fixture_seed=42,
                            fixture_context=context, attempt=str(attempt), command=list(actual_command),
                            worktree=str(root), relay=actual_relay))
        def transact():
            if name == 'lawful':
                with patch.object(c, 'require_bound_worker', checked_inert_admission):
                    return perform()
            return perform()
        def perform():
            return custody.transaction(attempt,command=command,cwd=root,pins=local_pins,
                expected_account=c.OWNER,context=context,referee=referee if name=='substitute' else pair.verify,consent=authority)
        if name=='wrong-pin':
            local_pins[str(shim)]='0'*64
        try:
            result=run()
        except (ValueError, OSError) as exc:
            expected={'forged':'COPY_WRITE','interrupt':'Transport rejected',
                      'wrong-pin':'Scientific worker pin differs','stop':'STOP',
                      'no-authority':'Candidate scientific authorization absent',
                      'substitute':'Candidate referee identity differs','auth-swap':'artifact identity differs',
                      'pending-fail':'injected pending write failure','receipt-swap':'Candidate receipt identity differs',
                      'late-stop':'STOP present'}[name]
            assert expected in str(exc),(name,str(exc))
            results[name]=dict(error=str(exc),referee_inputs=called)
        else:
            assert name=='lawful' and result['contrast']==3
            results[name]=dict(result=result,referee_inputs=called)
        if attempt.exists() and name not in ('auth-swap','late-stop'):
            try:
                run()
            except FileExistsError:
                results[name]['second_claim']='FileExistsError'
            else:
                raise AssertionError('Duplicate admitted')
    if name == 'lawful':
        identities = [json.loads((attempt/f).read_bytes())['release_identities'] for f in
                      ('00-pending.json','01-verified.json','02-release-intent.json','04-terminal.json')]
        assert all(x == identities[0] for x in identities)
        assert identities[0]['authorization_sha256'] == final_authority_pin
        assert identities[0]['binding_sha256'] == frozen_scope['V2_BINDING']
        assert identities[0]['package_sha256'] == frozen_scope['V2_PACKAGE']
        assert identities[0]['source_inventory_sha256'] == final['source_inventory_sha256']
        assert identities[0]['inert_execution']['command'] == command
        terminal = json.loads((attempt/'04-terminal.json').read_bytes())
        assert terminal['raw_sha256'] == sha(attempt/'raw.bin')
        assert all(sha(attempt/f) == h for f,h in terminal['receipt_sha256'].items())
        assert identities[0]['referee_sha256'] == sha(Path(pair.__file__))
        results[name]['release_identities'] = identities[0]
    assert attempt.exists()==(name in ('lawful','forged','interrupt','auth-swap','pending-fail','receipt-swap','late-stop'))
assert not original_attempt.exists()
(out/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
