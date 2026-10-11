"""Finite reversible gate preflight. Supplied gates; no autonomous apparatus."""
import itertools

CAPACITY=6
ARMS=('memory_cycle','stationary','memory_disabled','function_disabled')
UNKNOWN=('raw_coupler_fabrication','raw_memory_fabrication','gate_actuation',
         'packet_transport','load_release','upkeep','damage_repair','constructor_renewal')

def energy(pair):
    return 2 if pair[0]==pair[1] else 0

def exchange(pair,work):
    """An involution on equal total-energy source/load states, not a reward."""
    other=(pair[0],1-pair[1]);delta=energy(pair)-energy(other)
    if 0<=work+delta<=CAPACITY:return other,work+delta
    return pair,work

def cycle(pair,work,memory,arm):
    if arm not in ARMS:raise ValueError('Unregistered arm')
    if any(type(q) is not int or q not in (0,1) for q in (*pair,memory)):
        raise ValueError('Bit identity/type')
    if type(work) is not int or work not in range(CAPACITY+1):raise ValueError('Finite load')
    before=memory
    if arm=='memory_cycle':
        memory^=pair[0]
        if memory==pair[0]:pair,work=exchange(pair,work)
        memory^=pair[0]
        operations=3
    elif arm=='stationary':pair,work=exchange(pair,work);operations=1
    elif arm=='memory_disabled':
        if memory==pair[0]:pair,work=exchange(pair,work)
        operations=1
    else:operations=0
    assert memory==before
    return pair,work,memory,operations

def record(sequence,arm):
    memory=0;work=0;steps=[];outputs=[]
    source_capital=sum(energy(pair) for pair in sequence)
    for identity,pair in enumerate(sequence):
        initial_work=work
        out,work,memory,count=cycle(pair,work,memory,arm)
        outputs.append(out)
        steps.append(dict(source_id=identity,input=list(pair),output=list(out),
                          work_before=initial_work,work_after=work,memory=memory,
                          signed_source_work=work-initial_work,gate_operations=count))
    # Actually run every inverse encounter; all residual sources are retained.
    returned=work;reverse=[]
    for identity in reversed(range(len(outputs))):
        out,returned,memory,count=cycle(outputs[identity],returned,memory,arm)
        reverse.append(dict(source_id=identity,restored=list(out),work_after=returned,memory=memory))
        assert out==sequence[identity]
    assert returned==0 and memory==0
    assert sum(energy(pair) for pair in outputs)+work==source_capital
    return dict(sequence=[list(p) for p in sequence],arm=arm,initial_source_energy=source_capital,
                source_ids=list(range(3)),initial_memory=0,final_memory=memory,retained_load=work,
                residual_source_energy=sum(energy(pair) for pair in outputs),
                positive_source_work=sum(max(0,s['signed_source_work']) for s in steps),
                returned_source_work=sum(max(0,-s['signed_source_work']) for s in steps),
                gate_operations=sum(s['gate_operations'] for s in steps),steps=steps,reverse=reverse,
                costs={name:None for name in UNKNOWN},whole_life_net=None,fresh_post_damage_net=None,
                apparatus_supplied=True,raw_formation=False,renewal_measured=False)

def panel():
    pairs=tuple(itertools.product((0,1),repeat=2))
    return dict(schema='correlated-cycle01-gate-preflight-v1',natural_worlds=0,
                records=[record(tape,arm) for tape in itertools.product(pairs,repeat=3) for arm in ARMS])
