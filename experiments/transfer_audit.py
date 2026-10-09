"""Independent set-of-bonds TRANSFER-01 interpreter; no producer import."""
import argparse,hashlib,itertools,json
from pathlib import Path
PAIRS=list(itertools.combinations(range(6),2)); ORIGINAL={PAIRS.index(p) for p in ((0,1),(2,3),(4,5))}
BASE=sorted(ORIGINAL);ARMS=('candidate','no-transfer','shuffled','background')
def pack(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def transitions(state,types,arm):
    bonds,energy,waste,used=state;occupied=set(itertools.chain.from_iterable(PAIRS[i] for i in bonds))
    available=[PAIRS.index(pair) for pair in itertools.combinations(sorted(set(range(6))-occupied),2)]
    out=[]
    if energy>2:
        for target in available:out.append((['form',target],(bonds|{target},energy-3,waste+2,used)))
    if energy>0:
        for donor in sorted(bonds):
            out.append((['break',donor],(bonds-{donor},energy-1,waste+2,used)))
            if arm=='no-transfer':continue
            for target in available:
                if arm=='background':sites=[None]
                else:
                    a,b=PAIRS[target];signature=int(types[a]!=types[b]);sites=[]
                    for enzyme in sorted(bonds-{donor}):
                        c,d=PAIRS[enzyme];matched=int(types[c]!=types[d])==signature
                        if matched if arm=='candidate' else not matched:sites.append(enzyme)
                for enzyme in sites:out.append((['transfer',donor,target,enzyme],(bonds-{donor}|{target},energy-1,waste+1,True)))
    return out
def enumerate_states(types,damage,budget,arm):
    start=(frozenset(ORIGINAL-{BASE[damage]}),budget,8,False);seen={start};pending=[start];edges=0
    while pending:
        s=pending.pop()
        if s[1]+s[2]+len(s[0])!=10+budget:raise ValueError('Energy ledger')
        for action,nxt in transitions(s,types,arm):
            edges+=1
            if nxt not in seen:seen.add(nxt);pending.append(nxt)
    states=sorted((sum(2**i for i in s[0]),s[1],s[2],s[3]) for s in seen)
    return len(seen),edges,hashlib.sha256(pack(states)).hexdigest(),seen
def witness(record,label,value):
    types,damage,budget,arm=record['types'],record['damage'],record['budget'],record['arm']
    objects=[];owners={};traces=[[] for _ in range(6)];actions=[];photons=10+budget;heat=0
    def create(index,route,parent=None,catalyst=None):
        atoms=list(PAIRS[index]);identity=len(objects)
        objects.append({'id':identity,'atoms':atoms,'alive':True,'route':route,
                        'atom_parents':[list(traces[a]) for a in atoms],'energy_parent':parent,'catalyst':catalyst})
        owners[index]=identity
        for a in atoms:traces[a].append(identity)
        return identity
    def lose(index):
        identity=owners[index];del owners[index];objects[identity]['alive']=False;return identity
    for pair in BASE:
        identity=create(pair,'paid-genesis');photons-=3;heat+=2;actions.append(['genesis',pair,identity])
    identity=lose(BASE[damage]);photons-=1;heat+=2;actions.append(['damage',BASE[damage],identity])
    state=(frozenset(owners),photons,heat,False)
    for action in value['path']:
        possible=transitions(state,types,arm);matches=[nxt for proposal,nxt in possible if proposal==action]
        if len(matches)!=1:raise ValueError('Invalid paid witness action')
        state=matches[0]
        if action[0]=='form':
            index=action[1];identity=create(index,'form');actions.append(['form',index,identity])
        elif action[0]=='break':
            index=action[1];identity=lose(index);actions.append(['break',index,identity])
        else:
            donor,target,catalyst=action[1:];parent=lose(donor);enzyme=owners[catalyst] if catalyst is not None else None
            identity=create(target,'transfer',parent,enzyme);actions.append(['transfer',donor,target,catalyst,parent,identity])
        if len(set(a for i in owners for a in PAIRS[i]))!=2*len(owners):raise ValueError('Atom overlap')
    photons,heat=state[1:3]
    final={'path':value['path'],'events':actions,'objects':objects,'atom_history':traces,'photons':photons,'heat':heat,'final_bonds':sorted(owners),'startup_paid':9,'damage_paid':1}
    if value!=final:raise ValueError('Witness ancestry/work')
    full=state[0]==ORIGINAL;partial=BASE[damage] in state[0]
    accepted={'partial':partial,'whole':full,'transfer-partial':partial and state[3],'transfer-whole':full and state[3]}
    if not accepted[label]:raise ValueError('False functional endpoint')
def audit(path,revision):
    records=[];keys=set();total_states=total_edges=0
    with Path(path).open() as f:
        if json.loads(next(f))!=dict(schema='transfer01',revision=revision,cases=5376,natural_worlds=0):raise ValueError('Source/header')
        for line in f:
            r=json.loads(line);types=r['types'];d=r['damage'];p=r['budget'];arm=r['arm']
            if len(types)!=6 or any(type(x) is not int or x not in (0,1) for x in types) or d not in range(3) or p not in range(7) or arm not in ARMS:raise ValueError('Registered case')
            key=(tuple(types),d,p,arm)
            if key in keys:raise ValueError('Duplicate case')
            keys.add(key);n,e,h,states=enumerate_states(types,d,p,arm)
            if (r['states'],r['edges'],r['state_sha256'])!=(n,e,h):raise ValueError('Complete graph mismatch')
            expected=set()
            for s in states:
                if BASE[d] in s[0]:expected.add('partial')
                if s[0]==ORIGINAL:expected.add('whole')
                if s[3] and BASE[d] in s[0]:expected.add('transfer-partial')
                if s[3] and s[0]==ORIGINAL:expected.add('transfer-whole')
            if set(r['witnesses'])!=expected:raise ValueError('Endpoint omission')
            for label,value in r['witnesses'].items():witness(r,label,value)
            total_states+=n;total_edges+=e
            records.append(dict(types=types,damage=d,budget=p,arm=arm,available=sorted(expected)))
    if len(keys)!=5376:raise ValueError('Incomplete unscreened census')
    minima=[]
    for bits in range(64):
        types=[bits>>i&1 for i in range(6)]
        for d in range(3):
            group=[r for r in records if r['types']==types and r['damage']==d]
            minimum={arm:{label:min((r['budget'] for r in group if r['arm']==arm and label in r['available']),default=None) for label in ('partial','whole','transfer-partial','transfer-whole')} for arm in ARMS}
            minima.append(dict(types=types,damage=d,minimum=minimum))
    wins=sum(x['minimum']['candidate']['whole'] is not None and all(x['minimum'][null]['whole'] is not None and x['minimum']['candidate']['whole']<=x['minimum'][null]['whole']-1 for null in ('no-transfer','background')) for x in minima)
    return dict(verified=True,cases=5376,natural_worlds=0,states=total_states,edges=total_edges,source_revision=revision,minima=minima,advantage_groups=wins,required_groups=96,gate_pass=wins>=96,
                autonomous_self_maintenance=False,classification='RESOURCE GATE PASSED: prospective dynamics required' if wins>=96 else 'NO WHOLE-SYSTEM RESOURCE ADVANTAGE: stop this claim')
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);args=p.parse_args()
    try:print(json.dumps(audit(args.input,args.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,StopIteration,json.JSONDecodeError) as e:print(json.dumps(dict(verified=False,error=str(e))));raise SystemExit(2)
if __name__=='__main__':main()
