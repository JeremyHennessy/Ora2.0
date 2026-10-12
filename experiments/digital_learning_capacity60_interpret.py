"""Independent raw VM first; opportunity/bills and narrow explicit-channel witnesses."""
from .digital_informative_exposure23_interpret import audit,body,h,clone
from .digital_diagnosis59_origins import trace
from .digital_learning_capacity60 import ARMS,SEEDS,SOURCE_HASH,VERSION,bank


def project(program,events):
    """Prepared partial tables allowed; real callers must first pass full VM audit."""
    words=sum(program,[]);assert len(words)==30
    state=body(0,None,0,[[v,i] for i,v in enumerate(words)],list(range(30,46)),0)
    remaining=set(range(32));views=[];trials=[];reads=[];hashes=[];seen=set();released=[];caps=0;first_food=None;last=None;death=None;endpoint=None;alive64=False
    for tick,e in enumerate(events,1):
        assert e['tick']==tick and e['actor']==0 and e['before']==h(state)
        op,a,b=e['decoded'];assert e['decoded']==words[3*state['pc']:3*state['pc']+3] and op in (1,4,5,6,7,8,18)
        assert not any(k in e for k in ('birth','writes','self_write','message','transfer'))
        available=sorted(p for p in remaining if p<16 or tick>=64);attempt=e.get('attempt')
        assert (attempt is not None)==(op==6 and bool(available))
        energy=state['energy']-1;view=dict(tick=tick,actor=0,decoded=e['decoded'][:],pc_before=state['pc'])
        if op==6:
            view['packet_present']=attempt is not None
            if attempt:
                assert attempt['packet']==available[0] and attempt['position']==0 and attempt['port']==state['registers'][a%2]%2
                key=(attempt['packet'],attempt['port'],tick>=64);informative=key not in seen;seen.add(key)
                last=dict(tick=tick,packet=attempt['packet'],port=attempt['port'],phase=('cold' if tick<64 else 'released' if 16<=attempt['packet']<32 else 'changed_early'),informative=informative,success=bool(attempt['success']))
                trials.append(clone(last))
                if attempt['success']:
                    remaining.remove(attempt['packet']);loss=max(0,energy+20-64);caps+=loss;energy+=20-loss
                    if first_food is None:first_food=tick
                    if 16<=attempt['packet']<32:
                        released.append(dict(tick=tick,packet=attempt['packet']))
                        if len(released)==12:endpoint=dict(tick=tick,bill=46+tick,cap_loss=caps)
            else:last=None
        if op==1:reads.append(dict(tick=tick,register=a%2,feedback=state['feedback'],origin=clone(last)))
        if 'death' in e:
            assert energy==0 and 'after' not in e;death=tick;view['death']=True
        else:
            state=clone(e['after']);assert state['energy']==energy and state['pos']==0 and state['memory']==[0]*8 and state['inbox'] is None
            assert [c[0] for c in state['code']]==words and state['nursery']==[]
            if tick==64:alive64=True
            hashes.append(dict(tick=tick,program=h(words),state=h(state),registers=h(state['registers']),memory=h(state['memory']),pc=h(state['pc']),inbox=h(state['inbox']),feedback=h(state['feedback'])))
        views.append(view)
    origins=trace(views,30);bridges=[]
    for r in reads:
        source=r['origin']
        if source is None or not source['informative']:continue
        for trial in trials:
            if trial['tick']<=r['tick'] or trial['packet']==source['packet']:continue
            # Explicit origin reachability is conservative, never itself causal evidence.
            record=origins['records'][trial['tick']-1]
            used=record['used']
            if [0,source['tick']] in used:
                overwritten=any(v['decoded'][0]==6 and r['tick']<v['tick']<trial['tick'] for v in views)
                if overwritten:bridges.append(dict(read_tick=r['tick'],source_tick=source['tick'],source_packet=source['packet'],later_tick=trial['tick'],later_packet=trial['packet'],success=trial['success'],scope='possible_explicit_own_history_reachability_only'))
    return dict(first_food_tick=first_food,survived64=alive64,endpoint=endpoint,released_acquisitions=released,trials=trials,reads=reads,
                possible_history_bridges=bridges,origin_summary=origins,channel_hashes=hashes,cap_loss=caps,instructions=len(events),death_tick=death,
                cold_ports=sorted({t['port'] for t in trials if t['phase']=='cold'}),released_real_trial_packets=sorted({t['packet'] for t in trials if t['phase']=='released'}),
                learning=False,stage_credit=False)


def interpret(envelope,source):
    assert envelope['version']==VERSION and envelope['source_hash']==SOURCE_HASH and envelope['authored_apparatus'] is True
    arm=envelope['arm'];assert arm in ARMS;program=bank(source)[arm];row=envelope['history']
    assert type(row['seed']) is int and row['seed'] in SEEDS and row['mode']=='faithful' and row['genesis_program']==program
    checked=audit(row);assert checked['verified'] and checked['formation_cost']==46 and checked['births']==checked['paid_copy_words']==checked['mutations']==0
    p=project(program,row['final']['events']);assert p['instructions']==checked['ticks']
    assert (p['death_tick'] is not None)==bool(checked['deaths'])
    if arm=='feedback-disabled':assert p['reads']==[] and p['possible_history_bridges']==[]
    if arm.startswith('fixed'):assert p['reads']==[]
    ordinary=arm=='fixed-exploration' and p['first_food_tick'] is not None and p['first_food_tick']<=12 and p['survived64'] and p['cold_ports']==[0,1] and p['endpoint'] is not None
    return dict(verified=True,seed=row['seed'],arm=arm,raw_hash=h(row),summary=checked,projection=p,ordinary_admitted=ordinary,
                authored_apparatus=True,independent_discovery=False,learning=False,stage_credit=False)


def compare(rows):
    assert len(rows)==112;index={}
    for row in rows:
        assert row['verified'] is True and row['authored_apparatus'] is True and row['stage_credit'] is False
        key=(row['seed'],row['arm']);assert type(key[0]) is int and key[0] in SEEDS and key[1] in ARMS and key not in index;index[key]=row
    assert set(index)=={(seed,arm) for seed in SEEDS for arm in ARMS}
    assert all(index[seed,'fixed-exploration']['ordinary_admitted'] for seed in SEEDS)
    groups={}
    for name,seeds in (('primary',range(60000,60008)),('unseen',range(60200,60208))):
        pairs=[]
        for seed in seeds:
            if seed%2:continue
            selected={arm:[index[s,arm]['projection'] for s in (seed,seed+1)] for arm in ARMS}
            complete={arm:all(p['endpoint'] is not None for p in ps) for arm,ps in selected.items()}
            bills={arm:sum(p['endpoint']['bill'] for p in ps) if complete[arm] else None for arm,ps in selected.items()}
            qualified=all(p['possible_history_bridges'] and any(t['informative'] for t in p['trials'] if t['phase']=='released') for p in selected['intact'])
            controls=('fixed-exploration','cache-cleared','cache-disrupted')
            exposed=qualified and complete['intact'] and all(complete[a] for a in controls)
            advantage=exposed and all(bills['intact']<bills[a] for a in controls)
            best_fixed=[min(values) if values else None for values in ([selected[a][i]['endpoint']['bill'] for a in ('fixed0','fixed1') if selected[a][i]['endpoint'] is not None] for i in (0,1))]
            pairs.append(dict(seeds=[seed,seed+1],complete=complete,bills=bills,possible_history_qualified=qualified,strict_paid_advantage=advantage,
                              decision='APPARATUS_ADVANTAGE_PENDING_CONTROL_CAUSAL_REVIEW' if advantage else 'FAILED_OR_UNDEREXPOSED',secondary_best_fixed_bill=sum(best_fixed) if all(v is not None for v in best_fixed) else None))
        groups[name]=dict(pairs=pairs,all_pairs_strict=sum(p['strict_paid_advantage'] for p in pairs)==4)
    return dict(verified=True,groups=groups,authored_apparatus=True,causal_learning_accepted=False,independent_discovery=False,stage_credit=False)
