"""Pure305-role primary custody graph; separate exact-source CI/registration mandatory."""
M=1024**2
SEEDS=tuple(range(1009700,1009708))+tuple(range(1009900,1009908))
GROUPS=('intact','model_erased','model_misbound','fallback_misbound','history_disabled','references')
CASES={g:([[q,r] for q in (2,4,8) for r in ('fallback0','model','fallback1')] if g!='references'
    else ['fixed0','fixed1','cue_identity','cue_inverse','fixed_alternation','latest_reactive']) for g in GROUPS}
ROLES=tuple(role for seed in SEEDS for role in (
    *[r for group in GROUPS for r in (f'original:{seed}:{group}:generate',
        f'original:{seed}:{group}:audit',f'restored:{seed}:{group}:generate')],
    f'original:{seed}:metrics'))+('original:all:accept',)

def capacity(role):
    assert type(role) is str and role in ROLES
    return (64 if role.endswith(':generate') else 8)*M

def layout(sources,owners,registration_size):
    assert type(registration_size) is int and 0<registration_size<=64*1024
    assert 0<sum(sources.values())*2<=4*M and 0<sum(owners.values())<=16*M
    raw={'registration.json':64*1024,'source.zip':2*M}
    for name,size in sources.items():
        assert type(size) is int and 0<size<=M
        for label in ('original','restored'):raw[label+'/'+name]=size
    for name,size in owners.items():
        assert type(size) is int and 0<size<=M
        raw['owners/'+name]=size
    for role in ROLES:raw['data/'+role.replace(':','-')+'.json']=capacity(role)
    for stem in [r.replace(':','-') for r in ROLES]+['refused'+str(i) for i in range(4)]:
        raw['native/'+stem+'.json']=M;raw['request/'+stem+'.json']=64*1024
    failure={'outcome.json':512*M,'budget.json':512*M}
    limits=dict(raw=sum(raw.values()),failure=sum(failure.values()),
        restore=sum(raw.values())+sum(failure.values()),archive=sum(raw.values())+sum(failure.values())+8*M)
    assert len(ROLES)==305
    assert all(limits[k]<=v*M for k,v in dict(raw=14336,archive=15360,restore=15360,failure=1024).items())
    assert sum(limits.values())<=46080*M
    return raw,failure,limits

def orchestrate(refuse,invoke,verify):
    """Real dependency loop, injectable for explicitly NON-PHYSICS qualification."""
    for field in ('role','configuration','source_sha','seal'):refuse(field)
    metric_specs={};endpoints=[]
    for seed in SEEDS:
        chains=[]
        for group in GROUPS:
            original=None
            for role in (f'original:{seed}:{group}:generate',f'original:{seed}:{group}:audit',f'restored:{seed}:{group}:generate'):
                kind=role.split(':')[-1]
                result=invoke(role,original if kind=='audit' else None);value=result['value'];spec=result['spec']
                assert value['seed']==seed and value['group']==group and value['software_only'] is False
                if kind=='generate':
                    assert value['error'] is None
                    assert type(value['scientific_genesis_attempts']) is int and value['scientific_genesis_attempts']==len(CASES[group])
                    assert [r['descriptor'] for r in value['records']]==CASES[group]
                    if role.startswith('original:'):original=spec
                    else:assert (spec['extent'],spec['sha256'])==(original['extent'],original['sha256'])
                else:
                    assert value['verified'] is True and value['producer_imported'] is False
                    assert value['evidence_inputs']==original
                    assert [r['descriptor'] for r in value['summaries']]==CASES[group]
                    assert all(r['proof']['verified'] is True for r in value['summaries'])
                verify(role,result)
                chains.append(result['chain'])
                del value,result
        role=f'original:{seed}:metrics'
        result=invoke(role,chains);value=result['value']
        assert value['seed']==seed and value['execution_admission'] is False
        assert [r['descriptor'] for r in value['endpoints']]==CASES['intact']
        assert len(value['endpoints'])==9
        metric_specs[str(seed)]=result['chain'];endpoints.extend(value['endpoints'])
        verify(role,result);del value,result,chains
    result=invoke('original:all:accept',metric_specs)
    assert result['value']['numeric_interface_only'] is True and result['value']['execution_admission'] is False
    verify('original:all:accept',result)
    assert len(metric_specs)==16 and len(endpoints)==144
    return dict(metric_specs=metric_specs,endpoints=endpoints,arithmetic=result['value'])


def recording_bound():
    return 9*1024*4096+9*64*1024+M





def admit_ci(receipt,source_head,status):
    assert type(receipt) is dict and receipt.get('passed') is True
    assert receipt.get('conclusion')=='success' and receipt.get('source_head')==source_head
    assert type(status) is str and status==''





def annotated_bound(witness):
    """Conservative impossible field unions, never an executed VM witness."""
    import copy,json
    enc=lambda value:json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    event=copy.deepcopy(witness['ordinary_event_union'])
    event['tick']=1024
    event['input']=[dict(packet=511,cue=7,energy=20,outcome='external_rejected') for _ in range(16)]
    ledger=dict(tick=1024,dispatch_pc=20,completed_before=60,
        entry=dict(previous_pc=20,actual_entry=16,projected_entry=16,completed=60,active=1),
        read=dict(pc=12,index=15,address=7,source_address=None,truthful_cell=15,value=15,active=1),
        completion=dict(completed=60,previous_pc=20,entry=16,energy=224))
    paired=len(enc(dict(event=event,ledger=ledger)))
    assert paired<=4096
    # Closed impossible static union already dominates all bounded physical
    # fields; add descriptor/programme/ledger wrapper margin explicitly.
    static=witness['static_snapshot_bytes']+4096
    assert static<=64*1024
    assert recording_bound()==39387136 and recording_bound()<64*M
    return dict(nonphysics=True,paired_event_bytes=paired,static_bound=static,
                recording_bound=recording_bound(),worlds=0,targets=0)

