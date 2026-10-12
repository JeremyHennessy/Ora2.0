"""Read-only endpoint diagnostics of closed Controls27; never creates a World."""
import json

VERSION='DIGITAL-ENDPOINT-ADMISSION-28-v1'
ROLES=tuple(f'candidate{i}' for i in (1,94,187,280,373,466,559,652))+tuple(f'affine{i}' for i in range(8))+('alternating','fixed0','fixed1')
ARMS=('intact','retained_disabled','own_disrupted')

def summarize(row):
    events=row['final']['events'];assert events and len(events)<=512
    assert [e['tick'] for e in events]==list(range(1,len(events)+1))
    assert all(e['actor']==0 and e['decoded'][0] in (1,2,3,4,5,6,7,18) for e in events)
    attempts=[e for e in events if 'attempt' in e]
    food=[e for e in attempts if e['attempt']['success']]
    assert all(type(e['attempt']['packet']) is int and 0<=e['attempt']['packet']<32 for e in food)
    assert len({e['attempt']['packet'] for e in food})==len(food)
    fresh=[e for e in food if e['attempt']['packet']>=16]
    seen={e['attempt']['packet'] for e in attempts if 16<=e['attempt']['packet']<32}
    deaths=[e['tick'] for e in events if 'death' in e]
    assert row['final']['births']==0 and row['final']['deaths']==len(deaths)<=1
    alive=bool(row['final']['entities']);assert alive==(not deaths)
    assert alive or deaths==[len(events)]
    assert not alive or len(events)==512
    return dict(ticks=len(events),paid_instructions=len(events),actions=sum(e['decoded'][0]==6 for e in events),real_attempts=len(attempts),food=len(food),fresh=len(fresh),fresh_attempted=len(seen),all_fresh_acquired_tick=max((e['tick'] for e in fresh),default=None) if len(fresh)==16 else None,alive_at_change=len(events)>=64 and not(deaths and deaths[0]<=64),alive_at_horizon=alive,death_tick=deaths[0] if deaths else None,post_change_alive_instruction_opportunities=sum(e['tick']>=64 for e in events),retained_rewrites=sum(len(e['control']['rewrites']) for e in events),own_samples=sum(e['decoded'][0]==1 and e['control']['mode']!='own_disrupted' and e['control']['substitution']['own_source_tick'] is not None for e in events))

def compare(candidate,reference):
    for m in (candidate,reference):
        assert all(type(m[k]) is int for k in ('ticks','paid_instructions','food','fresh','fresh_attempted'))
        assert 0<=m['food']<=32 and 0<=m['fresh']<=m['fresh_attempted']<=16 and m['fresh']<=m['food']
        assert 1<=m['ticks']==m['paid_instructions']<=512
        assert type(m['alive_at_horizon']) is bool
        assert (m['death_tick'] is None)==m['alive_at_horizon']
    return dict(fresh_delta=candidate['fresh']-reference['fresh'],food_delta=candidate['food']-reference['food'],survival_delta=int(candidate['alive_at_horizon'])-int(reference['alive_at_horizon']),fixed_fresh_ceiling=reference['fresh']==16,fixed_food_ceiling=reference['food']==32,fixed_horizon_ceiling=reference['alive_at_horizon'],full_fresh_exposure_both=candidate['fresh_attempted']==reference['fresh_attempted']==16,shared_fresh_completion_endpoint=candidate['all_fresh_acquired_tick'] is not None and reference['all_fresh_acquired_tick'] is not None,lower_instruction_count_is_censored=candidate['paid_instructions']<reference['paid_instructions'] and not candidate['alive_at_horizon'],learning_inference=False)

def batch(data):
    assert data['contract']=='DIGITAL-HISTORY-CONTROLS-27-v1'
    assert type(data['seed']) is int and data['seed'] in (27090,27091) and data['control'] in ARMS
    expected=ROLES[:8] if data['group']=='candidates' else ROLES[8:]
    assert data['group'] in ('candidates','references') and tuple(x['role'] for x in data['histories'])==expected
    rows=[]
    for x in data['histories']:
        row=x['row'];assert row['seed']==data['seed'] and row['control_mode']==data['control']
        rows.append(dict(role=x['role'],seed=data['seed'],control=data['control'],**summarize(row)))
    return dict(version=VERSION,rows=rows,new_worlds=0,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    print(json.dumps(batch(json.load(open(sys.argv[1],encoding='utf-8'))),sort_keys=True,separators=(',',':')))
