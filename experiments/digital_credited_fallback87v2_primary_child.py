"""Frozen primary roles. World/target imports occur only after all custody guards."""
import hashlib,json,sys
from pathlib import Path
from experiments import digital_credited_fallback87v2_primary_boundary as boundary
from experiments import evidence_write_grant68 as transport
from experiments.digital_credited_fallback87v2_primary_plan import SEEDS,GROUPS,CASES,ROLES,capacity

M=1024**2
CONFIG=dict(version='CREDITED-FALLBACK87v2-PRIMARY-v1',seeds=list(SEEDS),groups=list(GROUPS),cases=CASES,
    mode='no_variation',max_population=1,expansion_tick=0,horizon=1024,warm=48,decisions=60,
    software_only=False,scientific_contract_sha256='8342c880706e5254c045995e3ca79ba09dbb4d0cca0717008214359aceb7e154',
    contract_sha256='5b112257188ea8067cbb97b5668b0e583c61b27e1343bacd3a008abf24bad300')
enc=boundary.canonical

def spec_shape(value):
    assert type(value) is dict and set(value)=={'path','extent','sha256'}
    assert type(value['path']) is str and Path(value['path']).is_absolute()
    assert type(value['extent']) is int and 0<value['extent']<=64*M
    boundary.hash_string(value['sha256'])

def chain_shape(chain,role):
    assert type(chain) is dict and set(chain)=={'role','request','native','body'} and chain['role']==role
    for field in ('request','native','body'):spec_shape(chain[field])
    assert chain['request']['extent']<=64*1024 and chain['native']['extent']<=M
    assert chain['body']['extent']<=capacity(role)

def group_roles(seed):
    return [r for r in ROLES if r.startswith(('original:'+str(seed)+':','restored:'+str(seed)+':')) and r.endswith((':generate',':audit'))]

def scope(request):
    assert type(request) is dict and set(request)=={'configuration','source_files','source_sha','config_sha','role','kind','input','grant','seal'}
    assert enc(request['configuration'])==enc(CONFIG)
    role=request['role'];assert type(role) is str and role in ROLES
    kind=role.split(':')[-1];assert request['kind']==kind
    inputs=request['input']
    if kind=='generate':assert inputs is None
    elif kind=='audit':spec_shape(inputs)
    elif kind=='metrics':
        seed=int(role.split(':')[1]);expected=group_roles(seed)
        assert type(inputs) is list and len(inputs)==18
        for chain,expected_role in zip(inputs,expected):chain_shape(chain,expected_role)
    else:
        assert kind=='accept' and type(inputs) is dict and set(inputs)=={str(s) for s in SEEDS}
        for seed in SEEDS:chain_shape(inputs[str(seed)],f'original:{seed}:metrics')
    return kind

def read(spec,cap):
    spec_shape(spec);assert spec['extent']<=cap
    from experiments.digital_recording82_reader import read_spec
    return read_spec(spec)

def authenticate(chain,request):
    from experiments.digital_credited_fallback87v2_metric_binding import authenticate as bind
    old=read(chain['request'],64*1024);native=read(chain['native'],M)
    assert scope(old)==old['kind']
    assert old['source_files']==request['source_files'] and old['source_sha']==request['source_sha']
    assert old['config_sha']==request['config_sha']
    assert old['grant']['root']==request['grant']['root']
    path=Path(chain['body']['path']);info=transport.plain(path)
    actual=str(Path(old['grant']['root'])/old['grant']['phase']/old['grant']['name'])
    bind(old,native,chain['body'],chain['role'],CONFIG,actual,(info.st_dev,info.st_ino))
    export=chain['role'].split(':')[0]
    assert boundary.verify_source(Path(old['grant']['root'])/'raw'/export,old['source_files'])==request['source_sha']
    return old

def generate(seed,group):
    from experiments.digital_credited_fallback87v2_world import World
    from experiments.digital_credited_fallback87v2_source import programme,ADMISSION
    from experiments.digital_memory80_recording import terminal_view
    records=[];attempts=0;constructed=0;error=None
    for descriptor in CASES[group]:
        world=None;code=programme(descriptor)
        try:
            attempts+=1;world=World(seed,descriptor,'intact' if group=='references' else group,admission=ADMISSION);constructed+=1
            while world.step():pass
            records.append(dict(descriptor=descriptor,programme=code,state=terminal_view(world.__dict__),ledger=world.control_ledger()))
        except BaseException as exc:
            error=repr(exc);partial=None;partial_error=None;ledger=None
            try:
                if world is not None:partial=terminal_view(world.__dict__);ledger=world.control_ledger()
            except BaseException as recovery:partial_error=repr(recovery)
            records.append(dict(descriptor=descriptor,programme=code,error=error,state=partial,ledger=ledger,partial_error=partial_error));break
    return dict(version=CONFIG['version'],software_only=False,seed=seed,group=group,
        scientific_genesis_attempts=attempts,completed_constructors=constructed,
        paid_target_observations=sum('attempt' in event for r in records if r['state'] is not None for event in r['state']['events']),
        records=records,error=error)

def audit(request,seed,group):
    from experiments.digital_credited_fallback87v2_referee import audit as literal
    from experiments.digital_credited_fallback87v2_source import programme,ADMISSION
    assert 'experiments.digital_memory80' not in sys.modules
    data=read(request['input'],64*M)
    assert data['version']==CONFIG['version'] and data['software_only'] is False and data['error'] is None
    assert (data['seed'],data['group'])==(seed,group)
    assert type(data['scientific_genesis_attempts']) is int and data['scientific_genesis_attempts']==len(CASES[group])
    assert data['completed_constructors']==len(CASES[group])
    assert [r['descriptor'] for r in data['records']]==CASES[group]
    summaries=[]
    for row in data['records']:
        code=programme(row['descriptor']);assert row['programme']==code
        state=row['state'];ledger=row['ledger'];reference=group=='references'
        proof=literal(state,seed=seed,mode='no_variation',max_population=1,expansion_tick=0,
            program=code,horizon=1024,control=None if reference else group,ledger=ledger,reference=reference,admission=ADMISSION)
        actions=[(e,ledger[i]) for i,e in enumerate(state['events']) if e['decoded'][0]==6]
        actual=[e for e,item in actions if 'attempt' in e]
        late=[e['attempt'] for e,item in actions if item['completed_before']>=48 and 'attempt' in e]
        cuts=[dict(tick=item['tick'],earned_energy=state['events'][i-1]['after']['energy'],entry=item['entry'])
            for i,item in enumerate(ledger) if item['entry'] is not None and item['entry']['active']==1]
        summaries.append(dict(descriptor=row['descriptor'],proof=proof,completed=sum(item['completion'] is not None for item in ledger),
            cut=cuts[0] if cuts else None,control_applicable=not reference,never_active=0 if reference else int(not cuts),
            late_served=late,acts=len(actions),served=len(actual),absence=len(actions)-len(actual),
            acquisitions=sum(e['attempt']['success'] for e in actual),captured=sum(e.get('captured',0) for e in actual),
            paid_cpu=len(state['events']),penalties=sum(e.get('penalty',0) for e in state['events']),
            births=state['births'],deaths=state['deaths'],writes=state['writes']))
    return dict(verified=True,version=CONFIG['version'],software_only=False,seed=seed,group=group,
        producer_imported=False,evidence_inputs=request['input'],summaries=summaries,stage_credit=False)

def metrics(request,seed):
    from experiments.digital_credited_fallback87v2_metrics import batch,combine
    from experiments.digital_credited_fallback87v2_metric_binding import bind_inputs
    chains={c['role']:c for c in request['input']}
    for chain in request['input']:authenticate(chain,request)
    batches=[]
    for group in GROUPS:
        orig=chains[f'original:{seed}:{group}:generate']['body'];replay=chains[f'restored:{seed}:{group}:generate']['body']
        assert (orig['extent'],orig['sha256'])==(replay['extent'],replay['sha256'])
        proof_chain=chains[f'original:{seed}:{group}:audit'];old=read(proof_chain['request'],64*1024)
        assert old['input']==orig
        body=read(orig,64*M);proof=read(proof_chain['body'],8*M)
        bind_inputs(orig,body,proof);batches.append(batch(body,proof));del body,proof
    value=combine(batches);assert value['seed']==seed
    value.update(version=CONFIG['version'],input_chains=request['input'])
    return value

def accept(request):
    from experiments.digital_credited_fallback87v2_acceptance import interpret
    endpoints=[]
    for seed in SEEDS:
        chain=request['input'][str(seed)];old=authenticate(chain,request)
        value=read(chain['body'],8*M)
        assert value['seed']==seed and value['version']==CONFIG['version'] and value['execution_admission'] is False
        assert value['input_chains']==old['input']
        assert [r['descriptor'] for r in value['endpoints']]==CASES['intact']
        endpoints.extend(value['endpoints']);del value,old
    value=interpret(endpoints);value['evidence_inputs']=request['input']
    return value

def main():
    request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),64*1024),object_pairs_hook=boundary.pairs)
    kind=scope(request);root=Path.cwd();pins=request['source_files']
    assert Path(__file__).resolve()==root/'experiments/digital_credited_fallback87v2_primary_child.py'
    assert 'experiments/digital_credited_fallback87v2_primary_child.py' in pins
    source=hashlib.sha256(enc(pins)).hexdigest();config=hashlib.sha256(enc(CONFIG)).hexdigest()
    assert source==request['source_sha'] and config==request['config_sha']
    assert boundary.verify_source(root,pins)==source
    assert request['grant']['limit']==capacity(request['role'])
    boundary.validate_grant(dict(grant=request['grant'],grant_seal=request['seal'],configuration_sha256=config,role=request['role']),
        source,'recording' if kind=='generate' else 'proof')
    error=None
    if kind=='accept':value=accept(request)
    else:
        seed=int(request['role'].split(':')[1])
        if kind=='metrics':value=metrics(request,seed)
        else:
            group=request['role'].split(':')[2]
            if kind=='generate':value=generate(seed,group);error=value['error']
            else:value=audit(request,seed,group)
    boundary.module_origins(root,pins);assert boundary.verify_source(root,pins)==source
    if kind in ('metrics','accept'):
        assert not any(name.endswith(('_source','_world','_referee')) or name=='experiments.digital_memory80' for name in sys.modules if name.startswith('experiments.'))
    receipt=transport.record(request['grant'],request['seal'],source,config,request['role'],value)
    print(enc(dict(role=request['role'],source_sha=source,config_sha=config,receipt=receipt)).decode())
    assert error is None,error

if __name__=='__main__':
    try:main()
    except BaseException:
        print(enc(dict(rejected_before_world='experiments.digital_memory80' not in sys.modules)).decode());raise
