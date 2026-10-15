"""Pure52-role software custody layout; not execution admission."""
M=1024**2
ARMS=('model_erased','model_misbound','fallback_misbound','history_disabled')
ROLES=tuple(role for seed in range(2100080,2100084) for arm in ARMS for role in (
    f'original:{seed}:{arm}:generate',f'original:{seed}:{arm}:audit',f'restored:{seed}:{arm}:generate'))

def capacity(role):
    assert type(role) is str and role in ROLES
    return (64 if role.endswith('generate') else 8)*M

def registration_capacity(extent):
    assert type(extent) is int and 0<extent<=32*1024
    return 64*1024

def layout(sources,owners,cached,registration_size):
    assert sum(sources.values())*2<=4*M and sum(owners.values())<=2*M
    assert sum(cached.values())<=12*M
    assert type(registration_size) is int and 0<registration_size<=64*1024
    raw={'registration.json':registration_size,'source.zip':2*M}
    for name,size in sources.items():
        assert type(size) is int and 0<size<=M
        for export in ('original','restored'):raw[export+'/'+name]=size
    for group,items in (('owners',owners),('cached',cached)):
        for name,size in items.items():
            assert type(size) is int and 0<size<=(12*M if group=='cached' else M)
            raw[group+'/'+name]=size
    for role in ROLES:raw['data/'+role.replace(':','-')+'.json']=capacity(role)
    for stem in [role.replace(':','-') for role in ROLES]+['refused'+str(i) for i in range(4)]:
        raw['native/'+stem+'.json']=M;raw['request/'+stem+'.json']=64*1024
    failure={'outcome.json':64*M,'budget.json':64*M}
    limits=dict(raw=sum(raw.values()),failure=sum(failure.values()),
        restore=sum(raw.values())+sum(failure.values()),
        archive=sum(raw.values())+sum(failure.values())+4*M)
    assert len(ROLES)==48
    assert all(limits[key]<=value*M for key,value in dict(raw=2304,archive=2560,restore=2560,failure=128).items())
    assert sum(limits.values())<=7552*M
    return raw,failure,limits

def recording_bound():
    return 9*1024*4096+9*64*1024+M

def admit_ci(receipt,source_head,status):
    assert type(receipt) is dict and receipt.get('passed') is True
    assert receipt.get('conclusion')=='success' and receipt.get('source_head')==source_head
    assert type(status) is str and status==''

def orchestrate(refuse,invoke,verify):
    """Real controller dependency/parity loop, injectable for NON-PHYSICS tests."""
    for field in ('role','configuration','source_sha','seal'):refuse(field)
    originals={};summaries={}
    cases=[[q,r] for q in (2,4,8) for r in ('fallback0','model','fallback1')]
    for role in ROLES:
        export,seed,arm,kind=role.split(':');key=(seed,arm)
        inputs=originals[key] if kind=='audit' else None
        result=invoke(role,inputs);value=result['value'];spec=result['spec']
        assert value['seed']==int(seed) and value['arm']==arm
        assert value['scientific_worlds']==value['scientific_targets']==0
        assert value['software_only'] is True
        if kind=='generate':
            assert value['error'] is None
            assert type(value['software_genesis_attempts']) is int and value['software_genesis_attempts']==9
            assert [row['descriptor'] for row in value['records']]==cases
            if export=='original':originals[key]=spec
            else:
                assert spec['extent']==originals[key]['extent']
                assert spec['sha256']==originals[key]['sha256']
        else:
            assert value['verified'] is True and value['producer_imported'] is False
            assert value['evidence_inputs']==inputs
            assert [row['descriptor'] for row in value['summaries']]==cases
            assert all(row['proof']['verified'] is True for row in value['summaries'])
            summaries[seed+':'+arm]=value
        verify(role,result)
        # Release the previous full producer body before the next native/read
        # call. Only small specs and audit summaries intentionally survive.
        del value,result
    assert len(originals)==len(summaries)==16
    return summaries

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

def validate_cached(entries,reader):
    """Custody/metadata only; full old literal/provenance remains separately pinned."""
    entries=tuple(entries)
    assert len(entries)==4
    for expected,(seed,spec) in zip(range(2100080,2100084),entries):
        assert seed==expected
        value=reader(spec)  # qualified plain-path/identity/extent/hash/canonical read
        assert value['seed']==seed and value['software_only'] is True
        assert value['error'] is None and value['software_genesis_attempts']==9
        assert [row['descriptor'] for row in value['records']]==[
            [q,r] for q in (2,4,8) for r in ('fallback0','model','fallback1')]
        del value  # release full closed body before reading the next one
