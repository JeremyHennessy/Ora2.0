"""Full independent Release07 interpretation and route-blind ordinary endpoint."""
import json
from .digital_release07_audit import audit as interpret
PROGRAMS={'alternating':[[4,1,1],[6,0,0],[5,0,1],[7,0,1]],'fixed0':[[4,0,0],[6,0,0],[7,0,0]],'fixed1':[[4,0,1],[6,0,0],[7,0,0]]}

def endpoint(r):
    return (r['pre_outcomes']==[0,1] and r['pre_ports']==[0,1]
            and r['alive_through_change'] and r['post_actions']>=4
            and r['post_successes']>=4)

def audit(record):
    assert set(record)=={'contract','history'} and record['contract']=='DIGITAL-EXPLORATION-13-v1'
    row=record['history'];assert type(row['seed']) is int and row['seed'] in (26190,26191)
    assert row['mode']=='faithful' and row['route'] in PROGRAMS
    assert row['genesis_program']==PROGRAMS[row['route']]
    m=interpret(row);events=row['final']['events']
    assert m['births']==0 and all(e['actor']==0 for e in events)
    pre=[e['attempt'] for e in events if 'attempt' in e and e['tick']<64]
    post=[e['attempt'] for e in events if 'attempt' in e and e['tick']>=64]
    death_ticks=[e['tick'] for e in events if 'death' in e]
    r=dict(pre_outcomes=sorted({a['success'] for a in pre}),pre_ports=sorted({a['port'] for a in pre}),
           alive_through_change=any(e['tick']==64 for e in events) and all(t>64 for t in death_ticks),
           post_actions=len(post),post_successes=sum(a['success'] for a in post))
    # Interpreter above verifies real ACT targets and feedback/state hashes; no
    # wrapper-provided aggregate is trusted as an experience or resource event.
    m.update(personal_opportunities=r,ordinary_admitted=endpoint(r),
             fresh_packets=sum(e['attempt']['success'] and 16<=e['attempt']['packet']<32 for e in events if 'attempt' in e),
             actions=sum(e['decoded'][0]==6 for e in events),actual_attempts=len(pre)+len(post),
             feedback_reads=sum(e['decoded'][0]==1 for e in events),memory_reads=sum(e['decoded'][0]==2 for e in events),
             memory_writes=sum(e['decoded'][0]==3 for e in events),formation_energy=len(sum(PROGRAMS[row['route']],[]))+16,
             supplied_fixed_exploration=True,learning=False,stage_credit=False)
    return m

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:print(json.dumps(audit(json.load(f)),sort_keys=True))
