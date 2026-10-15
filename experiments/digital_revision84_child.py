"""Finite scoped native roles. A configuration/admission string alone grants nothing."""
import hashlib,json,sys
from pathlib import Path
from experiments import digital_cognitive76_child as boundary
from experiments import evidence_write_grant68 as transport
from experiments.digital_revision84_source import SOFTWARE,PRIMARY,UNSEEN,ADMISSION,roster,programme

CONFIG=dict(version='REVISION84-SCIENTIFIC-v1',phase='science',seeds=list(PRIMARY+UNSEEN),
    roster=[list(x) for x in roster()],horizon=1024,software_only=False,
    contract_sha256='520a648a7beb5828ffc6c4295e1bf47b8af3021dc91357a637e15da436954283')
PREPARED=dict(CONFIG,version='REVISION84-WHOLE-PREPARED-v1',phase='prepared',seeds=list(SOFTWARE),software_only=True)
enc=boundary.canonical

def scope(request):
    assert set(request)=={'configuration','source_files','source_sha','config_sha','role','kind','input','grant','seal'}
    supplied=request['configuration']
    assert type(supplied) is dict and type(supplied.get('software_only')) is bool
    configuration=PREPARED if supplied.get('phase')=='prepared' else CONFIG
    assert supplied==configuration
    if request['kind']=='interpret':
        assert request['role']=='original:interpret'
        return configuration,None,'interpret'
    export,seed_string,kind=request['role'].split(':');seed=int(seed_string)
    assert str(seed)==seed_string and seed in configuration['seeds'] and kind==request['kind']
    assert (export,kind) in (('original','generate'),('original','audit'),('restored','generate'),('original','metrics'))
    return configuration,seed,kind

def main():
    request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),1024**2),object_pairs_hook=boundary.pairs)
    configuration,seed,kind=scope(request)
    pins=request['source_files'];root=Path.cwd()
    assert 'experiments/digital_revision84_child.py' in pins
    source=hashlib.sha256(enc(pins)).hexdigest();config=hashlib.sha256(enc(configuration)).hexdigest()
    assert source==request['source_sha'] and config==request['config_sha']
    assert boundary.verify_source(root,pins)==source
    assert request['grant']['limit']==(64 if kind=='generate' else 8)*1024**2
    boundary.validate_grant(dict(grant=request['grant'],grant_seal=request['seal'],
        configuration_sha256=config,role=request['role']),source,'recording' if kind=='generate' else 'proof')
    error=None;software=configuration['software_only']
    if kind=='generate':
        from experiments import digital_revision84_world as producer
        from experiments.digital_memory80_recording import terminal_view,FIELDS
        target=producer.target_mask;queries=[]
        admission=None if software else ADMISSION
        def guarded_target(value,packet,admission=None):
            assert value in configuration['seeds']
            assert admission==(None if software else ADMISSION)
            queries.append((value,packet));return target(value,packet,admission)
        producer.target_mask=guarded_target
        old_genesis=producer._genesis;attempts=[]
        def guard_genesis(self,value,*args,**kwargs):
            assert value in configuration['seeds']
            attempts.append(value);return old_genesis(self,value,*args,**kwargs)
        producer._genesis=guard_genesis
        def view(world):
            raw=world.__dict__
            expected=FIELDS|{'control_mode','control_active','decisions','source_role','finish_pc'}
            assert set(raw)==expected
            return dict(terminal_view({k:raw[k] for k in FIELDS}),
                        **{k:raw[k] for k in expected-FIELDS})
        rows=[]
        for role,control in configuration['roster']:
            world=None
            try:
                world=producer.World(seed,role,control,admission=admission)
                while not world.done():assert world.step()
                rows.append(dict(seed=seed,role=role,control=control,
                                 programme=programme(role),state=view(world)))
            except BaseException as exc:
                error=repr(exc)
                if world is not None:
                    try:partial=view(world)
                    except BaseException:partial=None
                    rows.append(dict(seed=seed,role=role,control=control,error=error,state=partial))
                break
        value=dict(version=configuration['version'],software_only=software,
            software_genesis_attempts=len(attempts) if software else 0,
            software_target_queries=len(queries) if software else 0,
            scientific_worlds=0 if software else len(attempts),
            scientific_targets=0 if software else len(queries),records=rows,error=error)
    elif kind=='audit':
        from experiments.digital_recording82_reader import read_spec
        from experiments.digital_revision84_referee import audit,digest
        assert 'experiments.digital_revision84_world' not in sys.modules
        assert 'experiments.digital_memory80' not in sys.modules
        data=read_spec(request['input'])
        assert data['version']==configuration['version'] and data['software_only']==software
        assert data['scientific_worlds']==(0 if software else 18)
        assert data['software_genesis_attempts']==(18 if software else 0)
        rows=data['records'];assert data['error'] is None
        assert [(r['role'],r['control']) for r in rows]==[tuple(x) for x in configuration['roster']]
        calls=sum('attempt' in e for r in rows for e in r['state']['events'])
        assert data['scientific_targets']==(0 if software else calls)
        assert data['software_target_queries']==(calls if software else 0)
        proofs=[]
        for row in rows:
            assert row['seed']==seed and row['programme']==programme(row['role'])
            proofs.append(audit(row['state'],seed=seed,role=row['role'],control=row['control'],program=row['programme']))
        def prefix(state):
            events=[]
            for e in state['events']:
                if 'control_cut' in e:break
                events.append({k:v for k,v in e.items() if k!='state_hash'})
            return digest(events)
        for q in (2,4,8):
            group=[r for r in rows if r['role']==f'learner{q}']
            assert len(group)==4 and len({prefix(r['state']) for r in group})==1
        focal=[r for r in rows if r['role']=='learner8'];windows=[];cuts=[]
        for row in focal:
            p=next(p for p in proofs if p['role']==row['role'] and p['control']==row['control'])
            cut=[e['control_cut'] for e in row['state']['events'] if 'control_cut' in e]
            cuts.append(cut)
            if software:
                assert p['completed'] and p['decisions']==60 and not p['deaths']
                assert len(cut)==1 and cut[0]['energy']==221 and cut[0]['decisions']==48 and cut[0]['pc']==1
            windows.append({(x['attempt']['packet'],x['attempt']['cue']) for x in p['causal_window'] if x['attempt'] is not None})
        common=set.intersection(*windows)
        if software:assert len(common)==12
        value=dict(verified=True,seed=seed,software_only=software,scientific_worlds=0,scientific_targets=0,
            proofs=proofs,q8_common_active=len(common),cuts=cuts,independent_warm_prefix=True,
            producer_imported=False,evidence_inputs=request['input'],stage_credit=False)
    elif kind=='metrics':
        from experiments.digital_recording82_reader import read_spec
        from experiments.digital_revision84_metrics import batch
        assert set(request['input'])=={'recording','proof'}
        data=read_spec(request['input']['recording']);proof=read_spec(request['input']['proof'])
        assert data['version']==configuration['version'] and data['software_only']==software
        assert data['scientific_worlds']==(0 if software else 18)
        assert data['error'] is None and proof['verified'] and proof['seed']==seed and proof['software_only']==software
        assert proof['evidence_inputs']==request['input']['recording']
        value=batch(data['records'],proof['proofs'])
        assert value['seed']==seed
        value.update(software_only=software,evidence_inputs=request['input'],scientific_worlds=0,scientific_targets=0)
        assert not any(n in sys.modules for n in ('experiments.digital_revision84_world','experiments.digital_revision84_referee','experiments.digital_memory80'))
    else:
        from experiments.digital_recording82_reader import read_spec
        from experiments.digital_revision84_acceptance import interpret
        assert type(request['input']) is list and len(request['input'])==len(configuration['seeds'])
        batches=[]
        for expected,spec in zip(configuration['seeds'],request['input']):
            value=read_spec(spec)
            assert value['verified'] and value['seed']==expected and value['software_only']==software
            batches.append(value)
        value=interpret(batches,software=software)
        value.update(verified=True,evidence_inputs=request['input'],scientific_worlds=0,scientific_targets=0)
        assert not any(n in sys.modules for n in ('experiments.digital_revision84_world','experiments.digital_revision84_referee','experiments.digital_revision84_metrics','experiments.digital_memory80'))
    boundary.module_origins(root,pins);assert boundary.verify_source(root,pins)==source
    receipt=transport.record(request['grant'],request['seal'],source,config,request['role'],value)
    print(enc(dict(role=request['role'],source_sha=source,config_sha=config,receipt=receipt)).decode())
    assert error is None,error

if __name__=='__main__':
    try:main()
    except BaseException:
        print(enc(dict(rejected_before_world='experiments.digital_revision84_world' not in sys.modules)).decode())
        raise
