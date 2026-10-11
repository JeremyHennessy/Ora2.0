"""Independent complete Release07 interpretation and typed route-blind endpoint."""
import json
from .digital_release07_audit import audit as interpret
PROGRAMS={
 'affine3':[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[3,1,0],[2,0,1],[18,0,0],[18,0,0],[4,1,1],[5,0,1],[3,1,0],[6,0,0],[7,0,5]],
 'alternating':[[4,1,1],[6,0,0],[5,0,1],[7,0,1]],
 'fixed0':[[4,0,0],[6,0,0],[7,0,0]],'fixed1':[[4,0,1],[6,0,0],[7,0,0]]}

def endpoint(r):
    try:
        assert type(r['pre_outcomes']) is list and type(r['pre_ports']) is list
        assert all(type(v) is int for v in r['pre_outcomes']+r['pre_ports'])
        assert type(r['alive_through_change']) is bool
        assert all(type(r[k]) is int and r[k]>=0 for k in ('post_actions','post_successes','fresh_packets'))
        return (r['pre_outcomes']==[0,1] and r['pre_ports']==[0,1] and r['alive_through_change']
                and r['post_actions']>=4 and r['post_successes']>=4 and r['fresh_packets']==16)
    except (AssertionError,KeyError,TypeError): return False

def audit(record):
    assert set(record)=={'contract','history'} and record['contract']=='DIGITAL-AFFINE-ADMISSION-19-v1'
    row=record['history']; assert type(row['seed']) is int and row['seed'] in (26590,26591)
    assert row['mode']=='faithful' and row['route'] in PROGRAMS and row['genesis_program']==PROGRAMS[row['route']]
    m=interpret(row); events=row['final']['events']; assert m['births']==0 and all(e['actor']==0 for e in events)
    pre=[e['attempt'] for e in events if 'attempt' in e and e['tick']<64]
    post=[e['attempt'] for e in events if 'attempt' in e and e['tick']>=64]
    deaths=[e['tick'] for e in events if 'death' in e]
    fresh=[e['tick'] for e in events if 'attempt' in e and 16<=e['attempt']['packet']<32 and e['attempt']['success']]
    personal=dict(pre_outcomes=sorted({a['success'] for a in pre}),pre_ports=sorted({a['port'] for a in pre}),
       alive_through_change=any(e['tick']==64 for e in events) and all(t>64 for t in deaths),
       post_actions=len(post),post_successes=sum(a['success'] for a in post),fresh_packets=len(fresh))
    actions=[e for e in events if e['decoded'][0]==6]
    empty=[e for e in actions if 'attempt' not in e]; assert all(e['feedback']==0 for e in empty)
    m.update(personal_opportunities=personal,ordinary_admitted=endpoint(personal),fresh_packets=len(fresh),
       actions=len(actions),actual_attempts=len(pre)+len(post),empty_actions=len(empty),
       feedback_reads=sum(e['decoded'][0]==1 for e in events),
       memory_reads=sum(e['decoded'][0]==2 for e in events),memory_writes=sum(e['decoded'][0]==3 for e in events),
       formation_energy=3*len(PROGRAMS[row['route']])+16,first_fresh_tick=fresh[0] if fresh else None,
       last_fresh_tick=fresh[-1] if fresh else None,final_live_energy=sum(e['energy'] for e in row['final']['entities'].values()),
       final_heat=row['final']['heat'],constructor_remaining=row['final']['constructor_remaining'],
       learning=False,stage_credit=False,supplied_fixed_exploration=True)
    if row['route']=='affine3':
        orientation=row['seed']%2; bytick={e['tick']:e for e in events}
        # Prospectively frozen phase predictions are checked against actual
        # independently interpreted histories, not substituted for them.
        assert bytick[5]['after']['energy']==27
        assert bytick[60]['after']['energy']==(52,32)[orientation]
        assert [(e['tick'],e['attempt']['port']) for e in actions if e['tick']<=5]==[(2,0),(5,1)]
        assert [e['tick'] for e in actions if e['tick']>5]==list(range(12,513,8))
        assert m['successful_food']==32 and m['fresh_packets']==16 and m['deaths']==0
        assert m['first_fresh_tick']==(244,268)[orientation] and m['last_fresh_tick']==(484,508)[orientation]
        assert m['final_live_energy']==(36,60)[orientation] and m['final_heat']==(687,663)[orientation]
        assert m['constructor_remaining']==57 and row['final']['tick']==512
        assert m['feedback_reads']==0 and all(e['decoded'][0] not in (9,10,12,14,15,16) for e in events)
        assert m['final_live_energy']+m['final_heat']+57+20*len(row['final']['food'])==1420
        m['derivation_verified']=True
    return m

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f: print(json.dumps(audit(json.load(f)),sort_keys=True))
