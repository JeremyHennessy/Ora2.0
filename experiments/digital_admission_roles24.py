"""Prospective role predicates. Prepared truth is not measured admission or learning."""
from .digital_affine_admission20_audit import endpoint as ordinary_exploration

def reactive_reachability(record):
    """Single-founder scope; verify complete ACT/read origins before counting reads."""
    try:
        assert type(record) is dict and set(record)=={'alive_through_change','actions','reads'} and record['alive_through_change'] is True
        actions,reads=record['actions'],record['reads']
        assert type(actions) is list and type(reads) is list
        assert actions and reads and len(actions)<=512 and len(reads)<=512
        prior=0;post=[];fresh=set()
        for action in actions:
            assert set(action)=={'tick','actor','attempt'}
            assert type(action['tick']) is int and prior<action['tick']<=512
            assert type(action['actor']) is int and action['actor']==0
            prior=action['tick'];a=action['attempt']
            if a is not None:
                assert type(a) is dict and set(a)=={'packet','port','success'}
                assert all(type(a[k]) is int for k in a)
                assert 0<=a['packet']<64 and a['port'] in (0,1) and a['success'] in (0,1)
                if action['tick']>=64:
                    post.append(a)
                    if a['success'] and 16<=a['packet']<32:
                        assert a['packet'] not in fresh
                        fresh.add(a['packet'])
        index=0;last=None;prior=0;distinct=set();outcomes=set()
        action_ticks={a['tick'] for a in actions}
        for read in reads:
            assert set(read)=={'tick','actor','origin','source_tick','value'}
            assert type(read['tick']) is int and prior<read['tick']<=512 and read['tick'] not in action_ticks
            assert type(read['actor']) is int and read['actor']==0
            assert type(read['value']) is int and read['value'] in (0,1)
            prior=read['tick']
            while index<len(actions) and actions[index]['tick']<read['tick']:
                last=actions[index];index+=1
            if last is None:
                assert read['origin']=='initial' and read['source_tick'] is None and read['value']==0
            elif last['attempt'] is None:
                assert read['origin']=='empty_reset' and read['source_tick'] is None and read['value']==0
            else:
                assert read['origin']=='own_actual_attempt' and type(read['source_tick']) is int and read['source_tick']==last['tick']
                assert read['value']==last['attempt']['success']
                if last['tick']>=64:distinct.add(last['tick']);outcomes.add(read['value'])
        return len(post)>=4 and sum(a['success'] for a in post)>=4 and len(fresh)==16 and len(distinct)>=16 and outcomes=={0,1}
    except (AssertionError,KeyError,TypeError):return False

def prepared_records():
    """Authored evaluator fixtures, no VM steps/resources/organism histories."""
    import copy
    actions=[dict(tick=65,actor=0,attempt=dict(packet=16,port=0,success=0))]+[dict(tick=67+2*i,actor=0,attempt=dict(packet=16+i,port=1,success=1)) for i in range(16)]
    reads=[dict(tick=a['tick']+1,actor=0,origin='own_actual_attempt',source_tick=a['tick'],value=a['attempt']['success']) for a in actions]
    base=dict(alive_through_change=True,actions=actions,reads=reads)
    records=[dict(name='reactive_positive_without_cold_failure',record=base,expected=True)]
    def negative(name):
        x=copy.deepcopy(base);records.append(dict(name=name,record=x,expected=False));return x
    x=negative('empty_reset_is_not_personal_failure');x['actions'].insert(1,dict(tick=66,actor=0,attempt=None));x['reads'][0]['tick']=66;x['reads'][0]['source_tick']=65
    # A separate empty ACT at66 invalidates a claimed old failure read at67;
    # shift the original subsequent events to preserve strictly distinct times.
    for a in x['actions'][2:]:a['tick']+=2
    for r in x['reads'][1:]:r['tick']+=2;r['source_tick']+=2
    x['reads'][0]['tick']=67
    x=negative('repeated_latch_not_sixteen_distinct_post_attempts');x['reads']=[dict(tick=t,actor=0,origin='own_actual_attempt',source_tick=97,value=1) for t in range(98,115)]
    x=negative('other_actor_history');x['actions'][0]['actor']=1
    x=negative('boolean_attempt_identity');x['reads'][0]['source_tick']=True
    x=negative('mismatched_feedback_value');x['reads'][0]['value']=1
    x=negative('no_personal_failure_read');x['reads']=x['reads'][1:]
    x=negative('fifteen_fresh_packets');x['actions']=x['actions'][:-1];x['reads']=x['reads'][:-1]
    x=negative('missing_survival');x['alive_through_change']=False
    x=negative('future_attempt_as_past_history');x['reads'][0]['source_tick']=67
    return records

if __name__=='__main__':
    import json
    records=prepared_records()
    print(json.dumps(dict(contract='DIGITAL-ADMISSION-ROLES-24-v1',software_only=True,new_world_histories=0,seeds_executed=[],records=[dict(**r,actual=reactive_reachability(r['record'])) for r in records]),sort_keys=True,separators=(',',':')))
