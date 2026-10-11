"""Full independent old-law interpretation then actual personal-experience ledger."""
import json
from .digital_release07_audit import audit as interpret
ANCESTOR=[[4,1,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]
BASELINES={'ancestor':ANCESTOR,'alternating':[[4,1,1],[6,0,0],[5,0,1],[7,0,1]],'fixed0':[[4,0,0],[6,0,0],[7,0,0]],'fixed1':[[4,0,1],[6,0,0],[7,0,0]]}
def experience_endpoint(rows):
    return any(r['outcomes']==[0,1] and r['reads_between_real_actions']>=4 and r['post_change_actions']>=4 and r['post_change_successes']>=1 for r in rows)
def audit(record):
    assert set(record)=={'contract','history'} and record['contract']=='DIGITAL-EXPERIENCE-12-PAID-FIXTURE-v1'
    row=record['history'];assert type(row['seed']) is int and row['seed'] in (26090,26091) and row['mode']=='faithful'
    route=row['route']
    if route.startswith('feedback'):
        assert route in ('feedback6','feedback9','feedback12','feedback15');code=sum(ANCESTOR,[]);code[int(route[8:])]=1;expected=[code[i:i+3] for i in range(0,18,3)]
    else:assert route in BASELINES;expected=BASELINES[route]
    assert row['genesis_program']==expected;m=interpret(row);actors={};last={};pending={}
    for e in row['final']['events']:
        actor=e['actor'];r=actors.setdefault(actor,dict(actor=actor,outcomes=set(),reads_between_real_actions=0,post_change_actions=0,post_change_successes=0))
        if e['decoded'][0]==1 and actor in last:pending[actor]=True
        if 'attempt' in e:
            if pending.pop(actor,False):r['reads_between_real_actions']+=1
            r['outcomes'].add(e['attempt']['success']);last[actor]=e['attempt']
            if e['tick']>=64:r['post_change_actions']+=1;r['post_change_successes']+=int(e['attempt']['success'])
    personal=[]
    for r in actors.values():r['outcomes']=sorted(r['outcomes']);personal.append(r)
    m.update(fresh_packets=sum(e.get('attempt',{}).get('success',0) and 16<=e['attempt']['packet']<32 for e in row['final']['events'] if 'attempt' in e),feedback_reads=sum(e['decoded'][0]==1 for e in row['final']['events']),memory_reads=sum(e['decoded'][0]==2 for e in row['final']['events']),memory_writes=sum(e['decoded'][0]==3 for e in row['final']['events']),personal_experiences=personal,experience_reachable=experience_endpoint(personal),prepared_fixture=True,learning_candidate_admitted=False,learning=False)
    return m
if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:print(json.dumps(audit(json.load(f)),sort_keys=True))
