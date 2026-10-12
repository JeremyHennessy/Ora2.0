"""Independent full interpretation, unchanged ordinary endpoint, own-event reads."""
import json
from .digital_informative_exposure23_interpret import audit as interpret
from .digital_affine_admission20_audit import endpoint

PROGRAMS={
 'affine3':[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[3,1,0],[2,0,1],[18,0,0],[18,0,0],[4,1,1],[5,0,1],[3,1,0],[6,0,0],[7,0,5]],
 'alternating':[[4,1,1],[6,0,0],[5,0,1],[7,0,1]],
 'witness':[[4,1,1],[2,0,0],[6,0,0],[1,0,0],[8,0,7],[7,0,1],[18,0,0],[2,0,0],[5,0,1],[3,0,0],[7,0,1]],
 'fixed0':[[4,0,0],[6,0,0],[7,0,0]],'fixed1':[[4,0,1],[6,0,0],[7,0,0]]}

def audit(rows):
    assert type(rows) is list and len(rows)==1
    row=rows[0];assert type(row['seed']) is int and row['seed'] in (26890,26891)
    assert row['mode']=='faithful' and row['route'] in PROGRAMS and row['genesis_program']==PROGRAMS[row['route']]
    m=interpret(row);events=row['final']['events'];assert m['births']==0 and all(e['actor']==0 for e in events)
    pre=[e['attempt'] for e in events if 'attempt' in e and e['tick']<64]
    post=[e['attempt'] for e in events if 'attempt' in e and e['tick']>=64]
    fresh=[e['tick'] for e in events if e.get('attempt',{}).get('success')==1 and 16<=e['attempt']['packet']<32]
    deaths=[e['tick'] for e in events if 'death' in e]
    personal=dict(pre_outcomes=sorted({a['success'] for a in pre}),pre_ports=sorted({a['port'] for a in pre}),alive_through_change=any(e['tick']==64 for e in events) and all(t>64 for t in deaths),post_actions=len(post),post_successes=sum(a['success'] for a in post),fresh_packets=len(fresh))
    last=None; origin='initial';value=0;reads=[]
    for e in events:
        if e['decoded'][0]==1:
            reads.append(dict(tick=e['tick'],source=last,origin=origin,value=value))
        if e['decoded'][0]==6:
            value=e['feedback'];last=e['tick'] if 'attempt' in e else None;origin='own_actual_attempt' if last else 'empty_reset'
    unique={r['source'] for r in reads if r['source'] is not None}
    empty=[e for e in events if e['decoded'][0]==6 and 'attempt' not in e]
    # Total success energy = retained live energy + instructions + cap loss - startup.
    cap_loss=12+20*m['successful_food']-len(events)-m['live_energy']
    assert cap_loss>=0
    m.update(personal_opportunities=personal,ordinary_admitted=endpoint(personal),fresh_packets=len(fresh),feedback_reads=len(reads),distinct_own_reads=len(unique),repeated_own_reads=sum(r['source'] is not None for r in reads)-len(unique),initial_reads=sum(r['origin']=='initial' for r in reads),empty_reset_reads=sum(r['origin']=='empty_reset' for r in reads),read_provenance=reads,actions=sum(e['decoded'][0]==6 for e in events),actual_attempts=len(pre)+len(post),empty_actions=len(empty),cap_loss=cap_loss,constructor_remaining=row['final']['constructor_remaining'],first_fresh_tick=fresh[0] if fresh else None,last_fresh_tick=fresh[-1] if fresh else None,death_ticks=deaths,learning=False,stage_credit=False,supplied_references_only=True)
    if row['route']=='affine3':
        t={e['tick']:e for e in events};assert t[5]['after']['energy']==27 and t[60]['after']['energy']==(52,32)[row['seed']%2]
        assert [(e['tick'],e['attempt']['port']) for e in events if e['decoded'][0]==6 and e['tick']<=5]==[(2,0),(4,1)]
        assert [e['tick'] for e in events if e['decoded'][0]==6 and e['tick']>5]==list(range(12,row['final']['tick']+1,8))
        assert m['feedback_reads']==0
    return m

def panel_admitted(metrics):
    expected={(s,r) for s in (26890,26891) for r in PROGRAMS}
    if len(metrics)!=10 or {(m['seed'],m['route']) for m in metrics}!=expected:return False
    return all(m['ordinary_admitted']==(m['route'] in ('affine3','alternating','witness')) and (m['route']!='witness' or m['distinct_own_reads']>=16) for m in metrics)

if __name__=='__main__':
    import sys
    print(json.dumps(audit(json.load(open(sys.argv[1],encoding='utf-8'))),sort_keys=True))
