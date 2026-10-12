"""Independent VM/operator audit and opportunity-aware diagnostic summaries."""
import json
from .digital_history_controls27_interpret import audit as interpret
from .digital_affine_source18 import compile_program
from .digital_neutral_catalogue25 import candidate

def projection(state):
    # Strip only operator annotations. Physical resource/action/state histories
    # remain complete; values, outcomes, deaths and state hashes are not copied.
    import copy
    result=copy.deepcopy(state)
    for e in result['events']:del e['control']
    return result

def audit(batch):
    assert batch['contract']=='DIGITAL-HISTORY-CONTROLS-27-v1' and batch['learning'] is False and batch['stage_credit'] is False
    assert type(batch['seed']) is int and batch['seed'] in (27090,27091) and batch['control'] in ('intact','retained_disabled','own_disrupted')
    expected={f'candidate{i}':candidate(i)['program'] for i in (1,94,187,280,373,466,559,652)} if batch['group']=='candidates' else {f'affine{i}':compile_program(i) for i in range(8)}
    if batch['group']=='references':expected.update(alternating=[[4,1,1],[6,0,0],[5,0,1],[7,0,1]],fixed0=[[4,0,0],[6,0,0],[7,0,0]],fixed1=[[4,0,1],[6,0,0],[7,0,0]])
    assert batch['group'] in ('candidates','references') and [x['role'] for x in batch['histories']]==list(expected)
    metrics=[]
    for item in batch['histories']:
        row=item['row'];role=item['role'];assert row['seed']==batch['seed'] and row['control_mode']==batch['control'] and row['genesis_program']==expected[role]
        assert item['ancestry']==(candidate(int(role[9:])) if role.startswith('candidate') else None)
        m=interpret(row);events=row['final']['events'];assert m['births']==0 and all(e['actor']==0 for e in events)
        actual=[e for e in events if 'attempt' in e];fresh={e['attempt']['packet'] for e in actual if e['attempt']['success'] and 16<=e['attempt']['packet']<32}
        post=[e for e in actual if e['tick']>=64];reads=[e for e in events if e['decoded'][0]==1]
        own_reads={e['control']['substitution']['own_source_tick'] for e in reads if e['control']['substitution']['own_source_tick'] is not None}
        cap=12+20*m['successful_food']-len(events)-m['live_energy'];assert cap>=0
        m.update(role=role,control=batch['control'],actual_attempts=len(actual),actions=sum(e['decoded'][0]==6 for e in events),empty_actions=sum(e['decoded'][0]==6 and 'attempt' not in e for e in events),fresh_packets=len(fresh),post_actual_attempts=len(post),feedback_reads=len(reads),distinct_own_read_origins=len(own_reads),read_substitutions=sum(e['control']['substitution'] is not None and e['control']['mode']=='own_disrupted' for e in events),retained_rewrites=sum(len(e['control']['rewrites']) for e in events),cap_loss=cap,constructor_remaining=row['final']['constructor_remaining'],death_ticks=[e['tick'] for e in events if 'death' in e],physical_projection_sha256=__import__('hashlib').sha256(json.dumps(projection(row['final']),sort_keys=True,separators=(',',':')).encode()).hexdigest(),learning=False,stage_credit=False)
        metrics.append(m)
    return dict(verified=True,seed=batch['seed'],group=batch['group'],control=batch['control'],metrics=metrics,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    print(json.dumps(audit(json.load(open(sys.argv[1],encoding='utf-8'))),sort_keys=True,separators=(',',':')))
