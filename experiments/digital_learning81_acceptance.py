"""Separate prospective interpretation. Standard library only; no producer/referee.

Inputs must first pass pinned native physics/custody; full history hashes bind
each proof to its actual independently generated arm. No label queries here.
"""
import hashlib,json

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()

FIXED=('fixed0','fixed1','cue_identity','cue_inverse','fixed_alternation','latest_reactive')
CONTROLS=('intact','model_erased','history_misbound')

def origins(row):
    state=row['state'];q=state['entities'].get('0',{}).get('memory')
    q=len(q) if q is not None else row['programme'][0][1]
    memory=[0]*q;provenance=[None]*q;last_attempt=None;prediction=None;revisions=[];uses=[];decisions=0
    for index,event in enumerate(state['events']):
        read=event.get('history_read')
        if read is not None:
            address=read['source_address'];prediction=None if address is None else provenance[address]
        if 'attempt' in event:
            last_attempt=dict(event['attempt'],event=index)
            if event['attempt']['success'] and prediction is not None:
                if prediction['cue']==event['attempt']['cue'] and prediction['success']==0:
                    uses.append(dict(cue=prediction['cue'],origin_packet=prediction['packet'],
                                     use_packet=event['attempt']['packet'],origin_event=prediction['event'],use_event=index))
        after=event.get('after')
        if after is not None:
            for cell,(before,value) in enumerate(zip(memory,after['memory'])):
                if before!=value:
                    assert event['decoded'][0]==20 and after['feedback']==0 and last_attempt is not None
                    assert last_attempt['success']==0 and last_attempt['cue']%q==cell
                    provenance[cell]=dict(last_attempt)
                    revisions.append(dict(cell=cell,value=value,origin_packet=last_attempt['packet'],store_event=index))
            memory=after['memory'][:]
        if event.get('decoded',[None])[0]==6:decisions+=1
    return dict(revisions=revisions,correct_uses=uses)

def physical_events(row):
    return [{k:v for k,v in e.items() if k not in ('state_hash','history_read')} for e in row['state']['events']]

def interpret(rows,proofs,software=False):
    assert type(software) is bool
    banks=(tuple(range(2100180,2100182)),tuple(range(2100182,2100184))) if software else (
        tuple(range(1008500,1008508)),tuple(range(1008700,1008708)))
    roster=tuple((r,'intact') for r in FIXED)+tuple((f'learner{q}',c) for q in (2,4,8) for c in CONTROLS)
    expected={(seed,role,c) for bank in banks for seed in bank for role,c in roster}
    records={(r['seed'],r['role'],r['control']):r for r in rows}
    physics={(r['seed'],r['role'],r['control']):r for r in proofs}
    assert len(rows)==len(records)==len(proofs)==len(physics)==len(expected)
    assert set(records)==set(physics)==expected
    for key,row in records.items():
        p=physics[key];assert p['verified'] is True and p['history_sha256']==digest(row['state'])
        assert p['final_state_sha256']==digest({k:v for k,v in row['state'].items() if k!='events'})
        assert p['births']==0 and p['stage_credit'] is False
    decisions=[]
    for bank in banks:
        passed_complete=True;passed_accuracy=True;passed_origins=True;equal_invariant=True
        coverage={c:0 for c in CONTROLS[1:]};advantage={c:0 for c in CONTROLS[1:]}
        unequal_advantage=0;equal_maps=0;intact_yield=0;fixed_oracle=0;retained=0;retained_oracle=0;origin_records=[]
        for seed in bank:
            key=(seed,'learner8','intact');row=records[key];p=physics[key]
            passed_complete &= p['completed'] and p['decisions']==64 and p['deaths']==0
            acts=[e for e in row['state']['events'] if e.get('decoded',[None])[0]==6]
            passed_accuracy &= len(acts)==64 and all(e.get('attempt',{}).get('success')==1 for e in acts[32:])
            observations={e['attempt']['cue']:e['attempt']['target'] for e in acts if 'attempt' in e}
            assert len(observations)==8 or not p['completed']
            own=origins(row);origin_records.append(dict(seed=seed,**own))
            if any(observations.values()):passed_origins &= bool(own['revisions'] and own['correct_uses'])
            intact_yield+=p['choice_yield'];retained+=p['retained_operating_surplus']
            fixed_oracle+=max(physics[seed,r,'intact']['choice_yield'] for r in FIXED)
            retained_oracle+=max(physics[seed,r,'intact']['retained_operating_surplus'] for r in FIXED)
            equal=len(set(observations.values()))==1 and len(observations)==8
            if equal:
                equal_maps+=1
                equal_invariant &= physical_events(row)==physical_events(records[seed,'learner8','history_misbound'])
            for control in CONTROLS[1:]:
                left={(x['attempt']['packet'],x['attempt']['cue']):x['attempt']['success'] for x in p['causal_window'] if x['attempt'] is not None}
                other=physics[seed,'learner8',control]
                right={(x['attempt']['packet'],x['attempt']['cue']):x['attempt']['success'] for x in other['causal_window'] if x['attempt'] is not None}
                common=set(left)&set(right);delta=sum(left[k]-right[k] for k in common)
                coverage[control]+=len(common);advantage[control]+=delta
                if control=='history_misbound' and not equal:unequal_advantage+=delta
        gates=dict(complete=bool(passed_complete),late_correct=bool(passed_accuracy),own_revision_use=bool(passed_origins),
                   common_active=all(v>=80 for v in coverage.values()),history_contrast=all(v>=16 for v in advantage.values()),
                   unequal_binding=unequal_advantage>=8,equal_invariant=bool(equal_invariant),paid_choice=intact_yield>=fixed_oracle+16)
        decisions.append(dict(seeds=list(bank),gates=gates,accepted=all(gates.values()),common_active=coverage,
            causal_correct_advantage=advantage,unequal_binding_advantage=unequal_advantage,equal_maps=equal_maps,
            intact_choice_yield=intact_yield,fixed_choice_oracle=fixed_oracle,retained_operating_surplus=retained,
            fixed_retained_oracle=retained_oracle,retained_superiority=retained>retained_oracle,own_origins=origin_records))
    return dict(version='LEARNING81-INTERPRETATION-v1',software_only=software,scientific_worlds=0 if software else len(rows),
        registered_choice_acceptance=not software and all(d['accepted'] for d in decisions),banks=decisions,
        capacity_profiles={f'learner{q}':[physics[s,f'learner{q}',c] for bank in banks for s in bank for c in CONTROLS] for q in (2,4,8)},
        scope='Supplied architecture/acquired label knowledge; nominal paid choice yield distinct from actual retained energy; no evolved architecture/fitness claim',
        stage_credit=False)
