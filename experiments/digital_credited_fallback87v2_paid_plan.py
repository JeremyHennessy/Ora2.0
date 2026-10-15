"""Pure22-role SOFTWARE layout and real dependency loop; no execution admission."""
M=1024**2
GROUPS=('intact','model_erased','model_misbound','fallback_misbound','history_disabled','references')
SEED=2100382
CASES={g:([[q,r] for q in (2,4,8) for r in ('fallback0','model','fallback1')]
    if g!='references' else ['fixed0','fixed1','cue_identity','cue_inverse','fixed_alternation','latest_reactive']) for g in GROUPS}
ROLES=tuple(role for group in GROUPS for role in (
    f'original:{SEED}:{group}:generate',f'original:{SEED}:{group}:audit',f'restored:{SEED}:{group}:generate'))

def capacity(role):
    assert type(role) is str and role in ROLES
    return (64 if role.endswith('generate') else 8)*M

def layout(sources,owners,registration_size):
    assert 0<sum(sources.values())*2<=4*M and 0<sum(owners.values())<=16*M
    assert type(registration_size) is int and 0<registration_size<=64*1024
    raw={'registration.json':64*1024,'source.zip':2*M}
    for name,size in sources.items():
        assert type(size) is int and 0<size<=M
        for export in ('original','restored'):raw[export+'/'+name]=size
    for name,size in owners.items():
        assert type(size) is int and 0<size<=M
        raw['owners/'+name]=size
    for role in ROLES:raw['data/'+role.replace(':','-')+'.json']=capacity(role)
    for stem in [r.replace(':','-') for r in ROLES]+['refused'+str(i) for i in range(4)]:
        raw['native/'+stem+'.json']=M;raw['request/'+stem+'.json']=64*1024
    failure={'outcome.json':64*M,'budget.json':64*M}
    limits=dict(raw=sum(raw.values()),failure=sum(failure.values()),
        restore=sum(raw.values())+sum(failure.values()),archive=sum(raw.values())+sum(failure.values())+4*M)
    assert len(ROLES)==18
    assert all(limits[k]<=v*M for k,v in dict(raw=896,archive=1024,restore=1024,failure=128).items())
    assert sum(limits.values())<=3072*M
    return raw,failure,limits

def orchestrate(refuse,invoke,verify):
    for field in ('role','configuration','source_sha','seal'):refuse(field)
    originals={};summaries={}
    for role in ROLES:
        export,seed,group,kind=role.split(':')
        inputs=originals[group] if kind=='audit' else None
        result=invoke(role,inputs);value=result['value'];spec=result['spec']
        assert value['seed']==SEED and value['group']==group and value['software_only'] is True
        assert type(value['scientific_worlds']) is int and type(value['scientific_targets']) is int
        assert value['scientific_worlds']==value['scientific_targets']==0
        if kind=='generate':
            assert type(value['software_genesis_attempts']) is int
            assert value['error'] is None and value['software_genesis_attempts']==len(CASES[group])
            assert [r['descriptor'] for r in value['records']]==CASES[group]
            if export=='original':originals[group]=spec
            else:assert (spec['extent'],spec['sha256'])==(originals[group]['extent'],originals[group]['sha256'])
        else:
            assert value['verified'] and value['producer_imported'] is False and value['evidence_inputs']==inputs
            assert [r['descriptor'] for r in value['summaries']]==CASES[group]
            assert all(r['proof']['verified'] for r in value['summaries'])
            summaries[group]=value
        verify(role,result)
        del value,result
    assert len(originals)==len(summaries)==6
    return summaries


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

