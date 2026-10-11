"""External conservative channel provenance; no World or interventions."""
import base64,json,zlib
from .digital_release07_audit import audit as validate
CONTRACT='DIGITAL-CHANNEL-PROVENANCE-21-v1'

def trace_events(events):
    registers=[set(),set()];memory=[set() for _ in range(8)];control=set()
    feedback=set();cause='initial_supplied';last_act=None;origins={};trace=[]
    for e in events:
        assert e['actor']==0 and type(e['tick']) is int
        tick=e['tick'];op,a,b=e['decoded'];assert op in (1,2,3,4,5,6,7,8,18)
        sampled=None;sample_cause=None;sample_act=None;action=None
        if op==1:
            sampled=sorted(feedback);sample_cause=cause;sample_act=last_act
            registers[a%2]=feedback|control
        elif op==2:registers[a%2]=memory[b%8]|control
        elif op==3:memory[a%8]=registers[b%2]|control
        elif op==4:registers[a%2]=set(control)
        elif op==5:registers[a%2]=registers[a%2]|registers[b%2]|control
        elif op==6:
            action=sorted(registers[a%2]|control);last_act=tick
            if 'attempt' in e:
                x=e['attempt'];origins[str(tick)]=dict(actor=0,tick=tick,packet=x['packet'],outcome=x['success'])
                feedback={tick};cause='actual_own_attempt'
            else:feedback=set();cause='empty_act_reset'
        elif op==8:control=control|registers[a%2]
        trace.append(dict(tick=tick,opcode=op,feedback_read_origins=sampled,feedback_read_cause=sample_cause,
            feedback_read_last_act=sample_act,action_possible_origins=action,
            registers=[sorted(x) for x in registers],memory=[sorted(x) for x in memory],pc_possible_origins=sorted(control)))
    return dict(origins=origins,trace=trace)

def measure(row):
    m=validate(row);assert m['births']==0
    t=trace_events(row['final']['events']);reads=[e for e in t['trace'] if e['opcode']==1]
    acts=[e for e in t['trace'] if e['opcode']==6]
    sampled={x for e in reads for x in e['feedback_read_origins']}
    return dict(contract=CONTRACT,verified=True,history_hash=row['hash'],seed=row['seed'],route=row['route'],
        replayed_ticks=m['ticks'],feedback_reads=len(reads),distinct_sampled_attempts=len(sampled),
        empty_reset_reads=sum(e['feedback_read_cause']=='empty_act_reset' for e in reads),
        initial_supplied_reads=sum(e['feedback_read_cause']=='initial_supplied' for e in reads),
        possible_history_actions=sum(bool(e['action_possible_origins']) for e in acts),
        pc_history_steps=sum(bool(e['pc_possible_origins']) for e in t['trace']),
        memory_history_steps=sum(any(e['memory']) for e in t['trace']),
        register_history_steps=sum(any(e['registers']) for e in t['trace']),
        immutable_code=True,inbox_unused=True,conservative_not_causal=True,**t,
        new_world_histories=0,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:
        row=json.load(f);row=row[0] if type(row) is list else row['history']
    print(base64.b64encode(zlib.compress(json.dumps(measure(row),sort_keys=True,separators=(',',':')).encode())).decode())
