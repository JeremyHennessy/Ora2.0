"""Pinned SOFTWARE worker; exact source CI and separate parent registration required."""
import hashlib
import json
from pathlib import Path
import sys
from experiments import digital_cognitive76_child as boundary
from experiments import evidence_write_grant68 as transport
from experiments.digital_credited_fallback87v2_source import programme,FIXED

M=1024**2
GROUPS=('intact','model_erased','model_misbound','fallback_misbound','history_disabled','references')
CONFIG=dict(version='CREDITED-FALLBACK87v2-PAID-SOFTWARE-v1',seeds=[2100382],groups=list(GROUPS),
    cases={g:([[q,r] for q in (2,4,8) for r in ('fallback0','model','fallback1')] if g!='references' else list(FIXED)) for g in GROUPS},
    mode='no_variation',max_population=1,expansion_tick=0,horizon=1024,warm=48,decisions=60,
    software_only=True,contract_sha256='7393f1bbd8c06727b72da21068b048412d9fa71b3c6fad9ac62f6b022553409e')
ROLES=tuple(role for group in GROUPS for role in (
    f'original:2100382:{group}:generate',f'original:2100382:{group}:audit',f'restored:2100382:{group}:generate'))
enc=boundary.canonical

def scope(request):
    assert type(request) is dict and set(request)=={
        'configuration','source_files','source_sha','config_sha','role','kind','input','grant','seal'}
    assert enc(request['configuration'])==enc(CONFIG)
    assert type(request['role']) is str and request['role'] in ROLES
    kind=request['role'].split(':')[-1];assert request['kind']==kind
    if kind=='generate':assert request['input'] is None
    else:assert type(request['input']) is dict and set(request['input'])=={'path','extent','sha256'}
    return kind

def main():
    assert len(CONFIG['contract_sha256'])==64, 'Invalid frozen contract binding'
    request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),64*1024),object_pairs_hook=boundary.pairs)
    kind=scope(request);_,seed_text,group,_=request['role'].split(':');seed=int(seed_text)
    root=Path.cwd()
    assert Path(__file__).resolve()==root/'experiments/digital_credited_fallback87v2_paid_child.py'
    pins=request['source_files'];assert 'experiments/digital_credited_fallback87v2_paid_child.py' in pins
    source=hashlib.sha256(enc(pins)).hexdigest();config=hashlib.sha256(enc(CONFIG)).hexdigest()
    assert source==request['source_sha'] and config==request['config_sha']
    assert boundary.verify_source(root,pins)==source
    assert request['grant']['limit']==(64*M if kind=='generate' else 8*M)
    boundary.validate_grant(dict(grant=request['grant'],grant_seal=request['seal'],
        configuration_sha256=config,role=request['role']),source,'recording' if kind=='generate' else 'proof')
    error=None
    if kind=='generate':
        from experiments.digital_credited_fallback87v2_world import World
        from experiments.digital_memory80_recording import terminal_view
        records=[];attempts=0
        for descriptor in CONFIG['cases'][group]:
            world=None;code=programme(descriptor)
            try:
                attempts+=1;world=World(seed,descriptor,'intact' if group=='references' else group)
                while world.step():pass
                records.append(dict(descriptor=descriptor,programme=code,
                    state=terminal_view(world.__dict__),ledger=world.control_ledger()))
            except BaseException as exc:
                error=repr(exc);partial=None;partial_error=None;ledger=None
                try:
                    if world is not None:partial=terminal_view(world.__dict__);ledger=world.control_ledger()
                except BaseException as recovery:partial_error=repr(recovery)
                records.append(dict(descriptor=descriptor,programme=code,error=error,state=partial,
                    ledger=ledger,partial_error=partial_error));break
        value=dict(version=CONFIG['version'],software_only=True,scientific_worlds=0,scientific_targets=0,
            seed=seed,group=group,software_genesis_attempts=attempts,records=records,error=error)
    else:
        from experiments.digital_credited_fallback87v2_referee import audit
        from experiments.digital_recording82_reader import read_spec
        assert 'experiments.digital_memory80' not in sys.modules
        data=read_spec(request['input'])
        assert data['version']==CONFIG['version'] and data['software_only'] is True
        assert type(data['scientific_worlds']) is int and type(data['scientific_targets']) is int
        assert data['scientific_worlds']==data['scientific_targets']==0
        assert type(data['software_genesis_attempts']) is int
        assert data['error'] is None and data['software_genesis_attempts']==len(CONFIG['cases'][group])
        assert data['seed']==seed and data['group']==group
        assert [r['descriptor'] for r in data['records']]==CONFIG['cases'][group]
        summaries=[]
        for row in data['records']:
            code=programme(row['descriptor']);assert row['programme']==code
            reference=group=='references';state=row['state'];ledger=row['ledger']
            proof=audit(state,seed=seed,mode='no_variation',max_population=1,expansion_tick=0,
                program=code,horizon=1024,control=None if reference else group,
                ledger=ledger,reference=reference)
            actions=[(event,ledger[i]) for i,event in enumerate(state['events']) if event['decoded'][0]==6]
            actual=[event for event,item in actions if 'attempt' in event]
            late=[event['attempt'] for event,item in actions if item['completed_before']>=48 and 'attempt' in event]
            cuts=[dict(tick=item['tick'],earned_energy=state['events'][i-1]['after']['energy'],entry=item['entry'])
                for i,item in enumerate(ledger) if item['entry'] is not None and item['entry']['active']==1]
            summaries.append(dict(descriptor=row['descriptor'],proof=proof,
                completed=sum(item['completion'] is not None for item in ledger),
                cut=cuts[0] if cuts else None,control_applicable=not reference,
                never_active=0 if reference else int(not cuts),late_served=late,
                acts=len(actions),served=len(actual),absence=len(actions)-len(actual),
                acquisitions=sum(event['attempt']['success'] for event in actual),
                captured=sum(event.get('captured',0) for event in actual),paid_cpu=len(state['events']),
                penalties=sum(event.get('penalty',0) for event in state['events']),
                births=state['births'],deaths=state['deaths'],writes=state['writes']))
        value=dict(verified=True,version=CONFIG['version'],software_only=True,scientific_worlds=0,
            scientific_targets=0,producer_imported=False,seed=seed,group=group,
            evidence_inputs=request['input'],summaries=summaries,stage_credit=False)
    boundary.module_origins(root,pins);assert boundary.verify_source(root,pins)==source
    receipt=transport.record(request['grant'],request['seal'],source,config,request['role'],value)
    print(enc(dict(role=request['role'],source_sha=source,config_sha=config,receipt=receipt)).decode())
    assert error is None,error

if __name__=='__main__':
    try:main()
    except BaseException:
        print(enc(dict(rejected_before_world='experiments.digital_memory80' not in sys.modules)).decode());raise
