"""Independent transition interpreter. Does not import the fixture producer."""
import hashlib
import itertools
import json


def inspect_run(run):
    roles=('C','H','F','S','L')
    n=2 if run['name']=='independent' else 1
    assert run['engines']==n
    candidate=run['name']=='candidate'
    has_f=run['name'] in ('candidate','fabricator_disabled')
    expected=set(roles if has_f else ('C','H','S','L'))
    live={}; serial=0; devices={}; used=set(); raw=set(range(20)); loads=set()
    feeds=set(); expired=set(); damaged=[set(),set()]; formed=[{}, {}, {}]
    bills=[dict(formation=0,upkeep=0,release=0,work=0) for _ in range(3)]
    previous=-1; tester=False; damage_work=0; fabrications=0
    def ready(engine,needed,phase):
        for role in needed:
            d=devices[(engine,role)]
            assert d['working'] and d['paid']==phase
    for ev in run['events']:
        op=ev['op']; phase=ev['phase']; inputs=ev['inputs']
        assert phase in (-1,0,1,2) and phase>=previous
        if phase>previous:
            assert phase==previous+1
            if previous>=0:
                assert all((previous,e) in expired for e in range(n))
                assert set(formed[previous])=={(e,r) for e in range(n) for r in expected}
                assert damaged[previous]==set(formed[previous])
            previous=phase
        assert len(inputs)==len(set(inputs)) and all(i in live for i in inputs)
        consumed=[live[i] for i in inputs]
        outputs=ev['outputs']
        assert all(type(count) is int and count>=0 for _,count in outputs)
        engine=ev.get('engine'); key=(engine,ev.get('role'))
        if op=='tester':
            assert not tester and phase==-1 and not inputs and outputs==[['t',20]]
            tester=True
        elif op=='feed':
            assert tester and phase>=0 and engine in range(n)
            assert (phase,engine) not in feeds and not inputs
            assert outputs==[['p',576//n]]
            assert not any(x[0] in ('p','c') and x[2]==engine for x in live.values())
            feeds.add((phase,engine))
        else:
            assert phase>=0 and (phase,engine) in feeds and engine in range(n)
            assert len(inputs)==sum(c for _,c in outputs)
            # Source and carrier inputs belong to the current phase and engine.
            for kind,p,e,roots in consumed:
                if kind in ('p','c'):assert p==phase and e==engine
            kinds=[x[0] for x in consumed]
            if op in ('photo','fabricate'):
                role=ev['role']; cid=ev['component']; mat=ev['material']
                assert role in expected and key not in devices and cid not in used
                assert type(cid) is int and cid>=0
                assert mat==[4*roles.index(role)+2*engine+i for i in range(2)]
                assert len(set(mat))==2 and set(mat)<=raw
                if op=='photo':
                    assert kinds==['p']*3 and outputs==[['b',1],['h',2]]
                    cost=3
                else:
                    assert candidate and kinds==['c']*2 and outputs==[['b',1],['h',1]]
                    ready(engine,('C','H','F'),phase)
                    assert all(len(x[3])==2 for x in consumed)
                    cost=4; fabrications+=1
                assert key not in formed[phase]
                formed[phase][key]=cid; used.add(cid); raw.difference_update(mat)
                devices[key]=dict(cid=cid,material=mat,potential=serial,working=True,paid=-1)
                bills[phase]['formation']+=cost
            elif op=='upkeep':
                d=devices[key]
                assert d['cid']==ev['component'] and d['working'] and d['paid']!=phase
                assert kinds==['p'] and outputs==[['h',1]]
                d['paid']=phase; bills[phase]['upkeep']+=1
            elif op=='capture':
                ready(engine,('C','H'),phase)
                s=devices.get((engine,'S'))
                capacity=6 if s and s['working'] and s['paid']==phase else 2
                assert sum(x[0]=='c' and x[2]==engine for x in live.values())<capacity
                assert kinds==['p']*2 and outputs==[['c',1],['h',1]]
            elif op=='load':
                ready(engine,('C','H','S','L'),phase)
                assert kinds==['c']*4 and outputs==[['w',2],['h',2]]
                assert all(len(x[3])==2 for x in consumed)
                identities=ev['loads']
                assert len(identities)==2 and len(set(identities))==2
                assert all(type(i) is int and 0<=i<1200 and i not in loads for i in identities)
                loads.update(identities); bills[phase]['work']+=2
            elif op=='expiry':
                assert (phase,engine) not in expired
                assert set(inputs)=={i for i,x in live.items() if x[0] in ('p','c') and x[2]==engine}
                assert outputs==[['h',len(inputs)]]
                expired.add((phase,engine))
            elif op=='damage':
                assert phase<2 and all((phase,e) in expired for e in range(n))
                d=devices[key]
                assert d['cid']==ev['component'] and d['working'] and d['paid']==phase
                assert kinds==['t'] and outputs==[['h',1]]
                d['working']=False; damaged[phase].add(key); damage_work+=1
            elif op=='release':
                d=devices[key]
                assert phase>0 and not d['working'] and d['cid']==ev['component']
                assert ev['material']==d['material'] and inputs[-1]==d['potential']
                assert kinds==['p','p','b'] and outputs==[['h',3]]
                assert not (set(d['material']) & raw)
                raw.update(d['material']); del devices[key]; bills[phase]['release']+=2
            else:raise AssertionError('Unknown transition')
        roots=frozenset().union(*(x[3] for x in consumed))
        for i in inputs:del live[i]
        for kind,count in outputs:
            for _ in range(count):
                ancestry=frozenset((serial,)) if op in ('feed','tester') else roots
                live[serial]=(kind,phase,engine,ancestry); serial+=1
        locked=[i for d in devices.values() for i in d['material']]
        assert len(locked)==len(set(locked)) and not (set(locked)&raw)
        assert raw|set(locked)==set(range(20))
    assert previous==2 and tester and feeds=={(p,e) for p in range(3) for e in range(n)}
    assert expired==feeds and set(formed[2])=={(e,r) for e in range(n) for r in expected}
    assert all(d['working'] and d['paid']==2 for d in devices.values())
    assert len(live)==1748 and not any(x[0] in ('p','c') for x in live.values())
    assert fabrications==(6 if candidate else 0)
    totals={k:sum(b[k] for b in bills) for k in bills[0]}
    payback=totals['work']-sum(totals[k] for k in ('formation','upkeep','release'))
    assert run['epoch_bills']==bills and run['totals']==totals
    assert sum(x[0]=='w' for x in live.values())==totals['work']==len(loads)
    assert run['payback']==payback and run['assistance_work']==damage_work
    assert run['assistance_inclusive_payback']==payback-damage_work
    fresh=[b['work']-b['formation']-b['upkeep']-b['release'] for b in bills]
    return dict(payback=payback,phase_payback=fresh,work=totals['work'],
                tester_work=damage_work,formed_devices=len(used),energy_units=len(live),
                heat=sum(x[0]=='h' for x in live.values()),material_units=20)


def audit(data):
    assert data['schema']=='photofactory01-v1'
    assert data['scheduling']=='CONTROLLED_ASSISTANCE_NOT_AUTONOMY'
    assert data['scheduling_cost']=='UNKNOWN' and data['mechanism_admitted'] is False
    assert data['natural_worlds']==0
    names=('candidate','stationary','independent','fabricator_disabled')
    assert [r['name'] for r in data['runs']]==list(names)
    results={r['name']:inspect_run(r) for r in data['runs']}
    cases=data['shuffle_cases']
    assert len(cases)==120
    assert {tuple(c['layout']) for c in cases}==set(itertools.permutations(range(5)))
    trace=json.dumps(data['runs'][0]['events'],sort_keys=True,separators=(',',':')).encode()
    digest=hashlib.sha256(trace).hexdigest()
    # The complete contact graph is invariant under every bijection. The law
    # never reads positions, so this is an exact quotient, not sampled worlds.
    graph={frozenset((i,j)) for i in range(5) for j in range(i)}
    for c in cases:
        p=c['layout']
        assert {frozenset((p[i],p[j])) for i in range(5) for j in range(i)}==graph
        assert c['trace_sha256']==digest and c['payback']==results['candidate']['payback']
    assert all(r['payback']>0 and all(v>0 for v in r['phase_payback']) for r in results.values())
    assert results['stationary']['payback']>results['candidate']['payback']
    assert all(a>b for a,b in zip(results['stationary']['phase_payback'],results['candidate']['phase_payback']))
    assert results['fabricator_disabled']['payback']>results['candidate']['payback']
    return dict(verified=True,results=results,shuffle_equivalent=120,
                decision='REJECT_BEFORE_NATURAL_WORLDS',autonomous_maintenance=False,
                scheduling_cost='UNKNOWN',reason='Accessible direct formation dominates; ordering has no advantage')
