"""Retained-data metrics only. No World, source, target, referee or acceptance imports."""
import hashlib
import json

GROUPS=('intact','model_erased','model_misbound','fallback_misbound','history_disabled','references')
DESCRIPTORS=tuple((q,r) for q in (2,4,8) for r in ('fallback0','model','fallback1'))
FIXED=('fixed0','fixed1','cue_identity','cue_inverse','fixed_alternation','latest_reactive')
SEEDS=(2100382,)+tuple(range(1009700,1009708))+tuple(range(1009900,1009908))
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()

def origins(row,group):
    """Extract provenance; this function alone is NOT a literal-physics validator."""
    q=row['programme'][0][1];cells=[None]*q;prediction=None;route=None
    ordinal=0;model_error=None;stored=None;sensed=None;reload_seen=False;not_seen=False
    revisions=[];uses=[];late=[];observed=[{},{}];personal=[{},{}]
    for index,(event,item) in enumerate(zip(row['state']['events'],row['ledger'])):
        pc=item['dispatch_pc'];after=event.get('after');entry=item['entry']
        if entry is not None and entry['active'] and group=='history_disabled':route=None
        if pc==6 and after is not None:sensed=after['registers'][1]
        read=item['read']
        if pc==7:
            assert read is not None
            address=read['source_address'];prediction=None if address is None else cells[address]
        if pc==12:reload_seen=True
        if pc==13 and after is not None:not_seen=True
        if event['decoded'][0]==6:
            attempt=event.get('attempt')
            if attempt is None:
                if pc==8:model_error=None
                continue
            ordinal+=1;phase=int(attempt['packet']>=48);cue=attempt['cue']
            observed[phase][str(cue)]=attempt['target']
            if pc==8:
                assert sensed==cue
                personal[phase][str(cue)]=attempt['target']
                model_error=(dict(attempt,ordinal=ordinal,event=index,tick=event['tick'])
                             if attempt['success']==0 else None)
                reload_seen=not_seen=False;stored=None
            origin=prediction if pc==8 else route if pc in (2,17) else None
            channel='model' if pc==8 else 'semantic'
            bit_match=origin is not None and origin['bit']==attempt['port']
            cue_match=origin is not None and origin['cue']==cue
            gap=None if origin is None else ordinal-origin['ordinal']
            valid=bool(origin is not None and bit_match and (channel!='model' or cue_match)
                       and gap>=2 and attempt['success']==1)
            evidence=dict(packet=attempt['packet'],cue=cue,port=attempt['port'],target=attempt['target'],
                success=attempt['success'],ordinal=ordinal,event=index,tick=event['tick'],
                channel=channel,origin=origin,bit_match=bool(bit_match),cue_match=bool(cue_match),
                served_gap=gap,valid_older_correct=valid,late=item['completed_before']>=48)
            uses.append(evidence)
            if evidence['late']:late.append(evidence)
        if pc==14 and event['decoded'][0]==20 and after is not None:
            assert model_error is not None and reload_seen and not_seen
            assert model_error['ordinal']==ordinal
            address=after['registers'][1]%q;bit=after['registers'][0]&1
            stored=dict(model_error,store_event=index,store_tick=event['tick'],address=address,bit=bit)
            cells[address]=stored;revisions.append(stored)
        if pc==15 and item['completion'] is not None:
            assert stored is not None
            target_entry=item['completion']['entry']
            assert target_entry in (1,16) and stored['bit']==int(target_entry==16)
            route=stored
    return dict(revisions=revisions,uses=uses,late=late,
        observed_maps=observed,personally_sensed_maps=personal,
        observed_mixed=int(len({bit for phase in observed for bit in phase.values()})>1))

def summarize(row,audit_row,group):
    assert row['descriptor']==audit_row['descriptor']
    proof=audit_row['proof'];assert proof['verified'] is True
    state=row['state'];events=state['events'];ledger=row['ledger']
    assert digest({k:v for k,v in state.items() if k!='events'})==proof['final_state_sha256']
    assert len(events)==len(ledger)==proof['ticks']==audit_row['paid_cpu']
    assert state['births']==state['writes']==0
    attempts=[e['attempt'] for e in events if 'attempt' in e]
    successes=sum(a['success'] for a in attempts)
    captured=sum(e.get('captured',0) for e in events)
    penalty=sum(e.get('penalty',0) for e in events)
    formation=3*len(row['programme'])+row['programme'][0][1]+8
    fees=sum(e.get('release_energy',0) for e in events)
    assert fees in (0,16)
    deathheat=sum(e.get('death',{}).get('dissipated',0) for e in events)
    capheat=20*successes-captured;failedheat=20*(len(attempts)-successes)
    living=sum(e['energy'] for e in state['entities'].values())
    assert state['heat']==formation+len(events)+penalty+fees+deathheat+capheat+failedheat
    assert living+deathheat==112+captured-len(events)-penalty
    assert state['heat']+living+state['constructor_remaining']+20*len(state['food'])==1536+20*state['admitted']
    assert state['offered']==state['admitted']+state['rejected']
    completed=sum(item['completion'] is not None for item in ledger)
    assert completed==audit_row['completed'] and 0<=completed<=60
    late=[e['attempt'] for e,item in zip(events,ledger) if item['completed_before']>=48 and 'attempt' in e]
    assert late==audit_row['late_served']
    own=None if group=='references' else origins(row,group)
    return dict(descriptor=row['descriptor'],group=group,completed=completed,deaths=state['deaths'],
        cpu=len(events),served=len(attempts),successes=successes,captured=captured,penalty=penalty,
        formation=formation,fees=fees,cap_heat=capheat,failed_packet_heat=failedheat,heat=state['heat'],
        living=living,constructor_remaining=state['constructor_remaining'],food=len(state['food']),
        offered=state['offered'],admitted=state['admitted'],rejected=state['rejected'],
        N=20*successes-formation-len(events)-penalty,O=captured-len(events)-penalty,
        E=captured-len(events)-penalty-formation-fees,late=late,own=own,
        warm_physical_sha256=digest([e for e,item in zip(events,ledger) if item['completed_before']<48]))

def batch(body,proof):
    seed=body['seed'];group=body['group']
    assert type(seed) is int and seed in SEEDS and group in GROUPS
    assert body['version']==proof['version'] and body['software_only'] is proof['software_only']
    assert type(body['software_only']) is bool
    assert (seed==2100382)==body['software_only']
    assert body['error'] is None and proof['verified'] is True and proof['producer_imported'] is False
    assert (proof['seed'],proof['group'])==(seed,group)
    cases=list(FIXED) if group=='references' else [list(d) for d in DESCRIPTORS]
    assert [r['descriptor'] for r in body['records']]==cases
    assert [r['descriptor'] for r in proof['summaries']]==cases
    count_field='software_genesis_attempts' if body['software_only'] else 'scientific_genesis_attempts'
    assert count_field in body
    assert type(body[count_field]) is int and body[count_field]==len(cases)
    return dict(seed=seed,group=group,rows=[summarize(row,audit_row,group)
        for row,audit_row in zip(body['records'],proof['summaries'])],requires_external_binding=True)

def combine(batches):
    assert type(batches) is list and len(batches)==6
    assert [b['group'] for b in batches]==list(GROUPS)
    seed=batches[0]['seed'];assert all(b['seed']==seed for b in batches)
    rows={b['group']:b['rows'] for b in batches}
    assert all(len(rows[g])==(6 if g=='references' else 9) for g in GROUPS)
    oracle_N=max(r['N'] for r in rows['references']);oracle_E=max(r['E'] for r in rows['references'])
    endpoints=[]
    for i,d in enumerate(DESCRIPTORS):
        current={g:rows[g][i] for g in GROUPS[:-1]}
        assert all(tuple(r['descriptor'])==d for r in current.values())
        assert len({r['warm_physical_sha256'] for r in current.values()})==1
        lookup={g:{(a['packet'],a['cue']):a['success'] for a in r['late']} for g,r in current.items()}
        common=set.intersection(*[set(v) for v in lookup.values()])
        assert len(common)<=12
        intact=current['intact'];own=intact['own']
        older=[u for u in own['late'] if u['valid_older_correct'] and (u['packet'],u['cue']) in common]
        endpoints.append(dict(seed=seed,descriptor=list(d),completed=intact['completed'],
            N=intact['N'],E=intact['E'],fixed_oracle_N=oracle_N,fixed_oracle_E=oracle_E,
            common=len(common),correct_intact=sum(lookup['intact'][k] for k in common),
            correct_joint=sum(lookup['history_disabled'][k] for k in common),
            correct_model=sum(lookup['model_erased'][k] for k in common),
            correct_route=sum(lookup['fallback_misbound'][k] for k in common),
            correct_misbound=sum(lookup['model_misbound'][k] for k in common),
            older_uses=len(older),observed_mixed=own['observed_mixed']))
    return dict(seed=seed,endpoints=endpoints,batches=batches,execution_admission=False,
                requires_external_literal_parity_native_source_grant_binding=True,stage_credit=False)
