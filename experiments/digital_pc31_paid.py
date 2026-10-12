"""Paid complete-acquisition endpoint; input must already have full VM proof."""
import json

VERSION='DIGITAL-PC-CONTROLS-31-PAID-SCOPE-v1'
REFERENCE_ROLES=tuple(f'affine{i}' for i in range(8))+('alternating','fixed0','fixed1')

def endpoint(row):
    program=row['genesis_program'];events=row['final']['events']
    assert program and len(program)<=32 and all(len(x)==3 and all(type(v) is int and 0<=v<32 for v in x) and x[0] in (1,2,3,4,5,6,7,8,18) for x in program)
    assert 1<=len(events)<=512 and [e['tick'] for e in events]==list(range(1,len(events)+1))
    assert all(e['actor']==0 and e['decoded'][0] in (1,2,3,4,5,6,7,8,18) for e in events)
    formation=3*len(program)+16;won={};attempted=set();personal={};outcomes=set();completion=None;paid_work=None;cap_loss=None
    for e in events:
        a=e.get('attempt')
        if a is not None:
            assert type(a['packet']) is int and 0<=a['packet']<32 and type(a['success']) is int and a['success'] in (0,1)
            if a['packet']>=16:attempted.add(a['packet'])
            if a['success']:
                assert a['packet'] not in won;won[a['packet']]=e['tick']
                if len(won)==32:
                    completion=e['tick'];paid_work=formation+completion
                    cap_loss=12+20*32-completion-e['after']['energy'];assert cap_loss>=0
        if e['decoded'][0]==1:
            sample=e['control']['personal_read'];origin=sample['own_source_tick']
            if origin is not None and origin>=64:
                assert 1<=origin<e['tick'];personal[origin]=sample['original'];outcomes.add(sample['original'])
    deaths=[e['tick'] for e in events if 'death' in e]
    return dict(completed=completion is not None,completion_tick=completion,paid_work_to_completion=paid_work,formation_cost=formation,startup_endowment=12,cap_loss_to_completion=cap_loss,successful_food=len(won),fresh_successes=sum(i>=16 for i in won),fresh_attempted=len(attempted),distinct_available_post_own_origins=len(personal),available_post_outcomes=sorted(outcomes),post_own_samples_delivered=bool(personal) and row['control_mode']!='own_disrupted',horizon_survival=not deaths,death_tick=deaths[0] if deaths else None,terminal_instructions=len(events),learning=False)
