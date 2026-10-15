"""Closed per-seed history interpretation. No producer, referee or target imports."""
import hashlib
import json

FIXED=('fixed0','fixed1','cue_identity','cue_inverse','fixed_alternation','latest_reactive')
CONTROLS=('intact','model_erased','history_misbound','update_frozen')
ROSTER=tuple((r,'intact') for r in FIXED)+tuple((f'learner{q}',c) for q in (2,4,8) for c in CONTROLS)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def origins(row):
    q=row['programme'][0][1]
    provenance=[None]*q;prediction=None;last_attempt=None;warm={};post={}
    revisions=[];uses=[];opportunities=[]
    for index,event in enumerate(row['state']['events']):
        read=event.get('history_read')
        if read is not None:
            address=read['source_address']
            prediction=None if address is None else provenance[address]
        attempt=event.get('attempt')
        if attempt is not None:
            packet=attempt['packet'];cue=attempt['cue'];target=attempt['target']
            phase=int(packet>=48)
            previous=warm.get(cue)
            last_attempt=dict(attempt,event=index,phase=phase,
                personally_changed=bool(phase and previous is not None and previous!=target))
            if phase:
                post[cue]=target
                opportunities.append(dict(packet=packet,cue=cue,success=attempt['success'],
                    personally_changed=None if previous is None else previous!=target))
            else:warm[cue]=target
            if attempt['success'] and prediction is not None and prediction['phase']==1:
                if (prediction['personally_changed'] and prediction['cue']==cue and
                    prediction['success']==0 and prediction['packet']<packet):
                    uses.append(dict(origin_packet=prediction['packet'],use_packet=packet,
                        cue=cue,origin_event=prediction['event'],use_event=index))
        store=event.get('history_store')
        if store is not None and store['after']!=store['before']:
            assert not store['blocked'] and last_attempt is not None and last_attempt['success']==0
            assert event['decoded'][0] in (3,20)
            provenance[store['address']]=dict(last_attempt)
            revisions.append(dict(last_attempt,cell=store['address'],store_event=index,
                                  old_value=store['before'],new_value=store['after']))
    return dict(revisions=revisions,postchange_correct_uses=uses,
        personally_observed_initial={str(k):v for k,v in warm.items()},
        personally_observed_later={str(k):v for k,v in post.items()},opportunities=opportunities)

def summarize(row,proof):
    assert proof['verified'] is True
    assert (row['seed'],row['role'],row['control'])==(proof['seed'],proof['role'],proof['control'])
    assert proof['history_sha256']==digest(row['state'])
    assert proof['final_state_sha256']==digest({k:v for k,v in row['state'].items() if k!='events'})
    assert proof['births']==0
    events=row['state']['events'];physical=[];prefix=[];cut=None;decisions=0;last=[]
    for event in events:
        if 'control_cut' in event:
            assert cut is None
            cut=event['control_cut']
        if cut is None:prefix.append({k:v for k,v in event.items() if k!='state_hash'})
        physical.append({k:v for k,v in event.items() if k not in ('state_hash','history_read','history_store')})
        if event.get('decoded',[None])[0]==6:
            decisions+=1
            if decisions>=57:last.append(event.get('attempt'))
    assert decisions==proof['decisions']
    fields=('ticks','decisions','completed','deaths','births','successes','penalties','formation',
        'paid_cost','captured_energy','cap_heat','failed_packet_heat','final_energy','heat','offered',
        'admitted','rejected','choice_yield','retained_operating_surplus','causal_window',
        'history_sha256','final_state_sha256')
    return dict(seed=row['seed'],role=row['role'],control=row['control'],
        **{k:proof[k] for k in fields},last_four=last,cut=cut,warm_prefix_sha256=digest(prefix),
        physical_sha256=digest(physical),own=origins(row))

def batch(rows,proofs):
    assert len(rows)==len(proofs)==18
    seeds={r['seed'] for r in rows};assert len(seeds)==1
    assert [(r['role'],r['control']) for r in rows]==list(ROSTER)
    lookup={(p['seed'],p['role'],p['control']):p for p in proofs}
    assert len(lookup)==18
    out=[summarize(r,lookup[r['seed'],r['role'],r['control']]) for r in rows]
    for q in (2,4,8):
        assert len({p['warm_prefix_sha256'] for p in out if p['role']==f'learner{q}'})==1
    return dict(verified=True,seed=next(iter(seeds)),records=out,stage_credit=False,
        scope='History interpretation requires external full physics/native/source/grant binding')
