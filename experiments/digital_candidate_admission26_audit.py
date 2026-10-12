"""Full independent VM replay precedes complete role projections and admission."""
import json
from .digital_informative_exposure23_interpret import audit as interpret
from .digital_admission_roles24 import reactive_reachability,ordinary_exploration
from .digital_affine_source18 import compile_program
from .digital_neutral_catalogue25 import candidate

def audit(batch):
    assert batch['contract']=='DIGITAL-CANDIDATE-ADMISSION-26-v1'
    seed=batch['seed'];assert type(seed) is int and seed in (26900,26901,26902,26903)
    expected={f'candidate{i}':candidate(i)['program'] for i in (1,94,187,280,373,466,559,652)} if batch['group']=='candidates' else {f'affine{i}':compile_program(i) for i in range(8)}
    if batch['group']=='references':expected.update(alternating=[[4,1,1],[6,0,0],[5,0,1],[7,0,1]],fixed0=[[4,0,0],[6,0,0],[7,0,0]],fixed1=[[4,0,1],[6,0,0],[7,0,0]])
    assert batch['group'] in ('candidates','references') and batch['learning'] is False and batch['stage_credit'] is False
    assert len(batch['histories'])==len(expected) and [x['role'] for x in batch['histories']]==list(expected)
    metrics=[]
    for item in batch['histories']:
        role,row=item['role'],item['row']
        assert item['ancestry']==(candidate(int(role[9:])) if role.startswith('candidate') else None)
        assert row['seed']==seed and row['mode']=='faithful' and row['genesis_program']==expected[role]
        m=interpret(row);ev=row['final']['events'];assert m['births']==0 and all(e['actor']==0 for e in ev)
        actions=[dict(tick=e['tick'],actor=e['actor'],attempt={k:e['attempt'][k] for k in ('packet','port','success')} if 'attempt' in e else None) for e in ev if e['decoded'][0]==6]
        reads=[]
        for e in ev:
            if e['decoded'][0]!=1:continue
            # Separate backwards resolver, no producer's projection or latch cache.
            preceding=[a for a in actions if a['tick']<e['tick']]
            last=preceding[-1] if preceding else None
            origin='initial' if last is None else 'empty_reset' if last['attempt'] is None else 'own_actual_attempt'
            reads.append(dict(tick=e['tick'],actor=0,origin=origin,source_tick=last['tick'] if origin=='own_actual_attempt' else None,value=last['attempt']['success'] if origin=='own_actual_attempt' else 0))
        deaths=[e['tick'] for e in ev if 'death' in e];alive=any(e['tick']==64 for e in ev) and all(t>64 for t in deaths)
        pre=[a['attempt'] for a in actions if a['tick']<64 and a['attempt'] is not None]
        post=[a['attempt'] for a in actions if a['tick']>=64 and a['attempt'] is not None]
        fresh={a['packet'] for a in post if a['success'] and 16<=a['packet']<32}
        ordinary=dict(pre_outcomes=sorted({a['success'] for a in pre}),pre_ports=sorted({a['port'] for a in pre}),alive_through_change=alive,post_actions=len(post),post_successes=sum(a['success'] for a in post),fresh_packets=len(fresh))
        record=dict(alive_through_change=alive,actions=actions,reads=reads)
        cap=12+20*m['successful_food']-len(ev)-m['live_energy'];assert cap>=0
        assert all('self_write' not in e and 'writes' not in e and 'message' not in e for e in ev)
        m.update(role=role,formation=len(row['genesis_program'])*3+16,constructor_remaining=row['final']['constructor_remaining'],actions=len(actions),actual_attempts=len(pre)+len(post),empty_actions=len(actions)-len(pre)-len(post),fresh_packets=len(fresh),cap_loss=cap,death_ticks=deaths,ordinary_admitted=ordinary_exploration(ordinary),reactive_admitted=reactive_reachability(record),role_record=record,ordinary_record=ordinary,learning=False,stage_credit=False)
        metrics.append(m)
    return dict(verified=True,seed=seed,group=batch['group'],metrics=metrics,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    print(json.dumps(audit(json.load(open(sys.argv[1],encoding='utf-8'))),sort_keys=True,separators=(',',':')))
