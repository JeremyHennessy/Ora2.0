"""Independent finite-state interpreter; no producer imports or physical prices."""
import itertools

def unique(items):
    d={}
    for k,v in items:
        if k in d:raise ValueError('Duplicate field')
        d[k]=v
    return d

def _states():return tuple(itertools.product((0,1),(0,1),(0,1),range(7)))
def _energy(s):return s[3]+(2 if s[1]==s[2] else 0)

def _tables():
    states=_states();copy={s:(s[0]^s[1],s[1],s[2],s[3]) for s in states}
    stationary={s:s for s in states}
    # Compile explicit equal-energy transpositions instead of the producer's
    # per-call energy-difference branch. Never exceed the finite load ladder.
    for m,a,w in itertools.product((0,1),(0,1),range(5)):
        high=(m,a,a,w);low=(m,a,1-a,w+2)
        stationary[high]=low;stationary[low]=high
    gated={s:stationary[s] if s[0]==s[1] else s for s in states}
    candidate={s:copy[gated[copy[s]]] for s in states}
    tables=dict(memory_cycle=candidate,stationary=stationary,memory_disabled=gated,
                function_disabled={s:s for s in states})
    for table in (*tables.values(),copy):
        assert set(table.values())==set(states)
        assert all(table[table[s]]==s and _energy(table[s])==_energy(s) for s in states)
    assert all(candidate[s]==stationary[s] for s in states if s[0]==0)
    return tables

def _check_record(r):
    if len(r['sequence'])!=3 or any(len(p)!=2 or any(type(b) is not int or b not in (0,1) for b in p) for p in r['sequence']):raise ValueError('Exact packet state/type')
    tables=_tables();arm=r['arm'];state=(0,0,0,0);outputs=[];steps=[]
    count={'memory_cycle':3,'stationary':1,'memory_disabled':1,'function_disabled':0}[arm]
    for n,pair in enumerate(r['sequence']):
        before=state[3];state=tables[arm][(state[0],*pair,before)]
        out=list(state[1:3]);outputs.append(out)
        steps.append(dict(source_id=n,input=pair,output=out,work_before=before,work_after=state[3],memory=state[0],signed_source_work=state[3]-before,gate_operations=count))
    work=state[3];capital=sum(2 for a,b in r['sequence'] if a==b);reverse=[]
    for n in (2,1,0):
        state=tables[arm][(state[0],*outputs[n],state[3])]
        reverse.append(dict(source_id=n,restored=list(state[1:3]),work_after=state[3],memory=state[0]))
    expected=dict(sequence=r['sequence'],arm=arm,initial_source_energy=capital,source_ids=[0,1,2],
        initial_memory=0,final_memory=state[0],retained_load=work,residual_source_energy=capital-work,
        positive_source_work=sum(max(0,s['signed_source_work']) for s in steps),
        returned_source_work=sum(max(0,-s['signed_source_work']) for s in steps),gate_operations=3*count,
        steps=steps,reverse=reverse,costs={n:None for n in ('raw_coupler_fabrication','raw_memory_fabrication','gate_actuation','packet_transport','load_release','upkeep','damage_repair','constructor_renewal')},
        whole_life_net=None,fresh_post_damage_net=None,apparatus_supplied=True,raw_formation=False,renewal_measured=False)
    import json
    if json.dumps(r,sort_keys=True)!=json.dumps(expected,sort_keys=True):raise ValueError('Independent state/cost reconstruction')
    assert state[0]==state[3]==0 and all(s['restored']==r['sequence'][s['source_id']] for s in reverse)

def audit(data):
    pairs=tuple(itertools.product((0,1),repeat=2));arms=('memory_cycle','stationary','memory_disabled','function_disabled')
    tapes=list(itertools.product(pairs,repeat=3));expected=[([[a,b] for a,b in tape],arm) for tape in tapes for arm in arms]
    if set(data)!={'schema','natural_worlds','records'} or data['schema']!='correlated-cycle01-gate-preflight-v1' or type(data['natural_worlds']) is not int or data['natural_worlds']!=0:raise ValueError('Preflight scope')
    if [(r['sequence'],r['arm']) for r in data['records']]!=expected:raise ValueError('Complete unscreened tapes')
    for row in data['records']:_check_record(row)
    matches=[]
    for i in range(0,256,4):
        c,s,md,off=data['records'][i:i+4]
        assert c['retained_load']==s['retained_load'] and c['steps']==[dict(x,gate_operations=3) for x in s['steps']]
        matches.append(dict(sequence=c['sequence'],candidate_gross=c['retained_load'],stationary_gross=s['retained_load'],memory_disabled_gross=md['retained_load'],function_disabled_gross=off['retained_load']))
    return dict(verified=True,logical_states=56,authored_tapes=64,records=256,natural_worlds=0,
        complete_bijection=True,energy_conserved=True,all_return_cycles_restored=True,
        stationary_matches_candidate_on_all_tapes=True,candidate_operations=9,stationary_operations=3,
        net_useful_work_measured=False,whole_life_net=None,fresh_post_damage_net=None,
        profitable_paid_comparator_verified=False,raw_formation_verified=False,admitted=False,
        decision='REJECT_THIS_CONCRETE_CORRELATION_CYCLE_BEFORE_WORLDS',comparisons=matches,
        reason='Simultaneously accessible pair conversion needs no informational memory; supplied-gate construction/actuation/return costs UNKNOWN, not zero.',
        self_maintenance_demonstrated=False,adaptation_demonstrated=False)
