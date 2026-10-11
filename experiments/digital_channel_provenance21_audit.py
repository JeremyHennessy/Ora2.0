"""Independent dependency graph and backward origin traversal, no extractor import."""
import json
from .digital_release07_audit import audit as interpret

def reconstruct(events):
    nodes=[((),None)];r=[0,0];memory=[0]*8;c=0;f=0;cause='initial_supplied';last=None;origins={};trace=[]
    def node(dependencies=(),origin=None):
        nodes.append((tuple(dependencies),origin));return len(nodes)-1
    def ancestors(index):
        pending=[index];seen=set();found=set()
        while pending:
            i=pending.pop()
            if i in seen:continue
            seen.add(i);deps,origin=nodes[i]
            if origin is not None:found.add(origin)
            pending.extend(deps)
        return sorted(found)
    for e in events:
        assert e['actor']==0;tick=e['tick'];op,a,b=e['decoded'];assert op in (1,2,3,4,5,6,7,8,18)
        sampled=None;why=None;act=None;selected=None
        if op==1:sampled=ancestors(f);why=cause;act=last;r[a%2]=node((f,c))
        elif op==2:r[a%2]=node((memory[b%8],c))
        elif op==3:memory[a%8]=node((r[b%2],c))
        elif op==4:r[a%2]=node((c,))
        elif op==5:r[a%2]=node((r[a%2],r[b%2],c))
        elif op==6:
            selected=sorted(set(ancestors(r[a%2]))|set(ancestors(c)));last=tick
            if 'attempt' in e:
                hit=e['attempt'];origins[str(tick)]={'actor':0,'tick':tick,'packet':hit['packet'],'outcome':hit['success']}
                f=node(origin=tick);cause='actual_own_attempt'
            else:f=0;cause='empty_act_reset'
        elif op==8:c=node((c,r[a%2]))
        trace.append(dict(tick=tick,opcode=op,feedback_read_origins=sampled,feedback_read_cause=why,
            feedback_read_last_act=act,action_possible_origins=selected,registers=[ancestors(x) for x in r],
            memory=[ancestors(x) for x in memory],pc_possible_origins=ancestors(c)))
    return dict(origins=origins,trace=trace)

def audit(row,receipt):
    m=interpret(row);assert m['births']==0
    t=reconstruct(row['final']['events']);reads=[e for e in t['trace'] if e['opcode']==1]
    expected=dict(contract='DIGITAL-CHANNEL-PROVENANCE-21-v1',verified=True,history_hash=row['hash'],
        seed=row['seed'],route=row['route'],replayed_ticks=m['ticks'],feedback_reads=len(reads),
        distinct_sampled_attempts=len({v for e in reads for v in e['feedback_read_origins']}),
        empty_reset_reads=sum(e['feedback_read_cause']=='empty_act_reset' for e in reads),
        initial_supplied_reads=sum(e['feedback_read_cause']=='initial_supplied' for e in reads),
        possible_history_actions=sum(bool(e['action_possible_origins']) for e in t['trace'] if e['opcode']==6),
        pc_history_steps=sum(bool(e['pc_possible_origins']) for e in t['trace']),
        memory_history_steps=sum(any(e['memory']) for e in t['trace']),
        register_history_steps=sum(any(e['registers']) for e in t['trace']),
        immutable_code=True,inbox_unused=True,conservative_not_causal=True,**t,
        new_world_histories=0,learning=False,stage_credit=False)
    assert json.dumps(receipt,sort_keys=True)==json.dumps(expected,sort_keys=True)
    return {k:v for k,v in expected.items() if k not in ('origins','trace')}

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f,open(sys.argv[2],encoding='utf-8') as g:
        row=json.load(f);row=row[0] if type(row) is list else row['history']
        print(json.dumps(audit(row,json.load(g)),sort_keys=True))
