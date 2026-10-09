"""TRANSFER-01 possibility census, not a natural-world controller."""
import argparse,copy,hashlib,itertools,json
from collections import deque
PAIRS=tuple(itertools.combinations(range(6),2))
ORIGINAL=tuple(PAIRS.index(p) for p in ((0,1),(2,3),(4,5)))
FULL=sum(1<<i for i in ORIGINAL)
ARMS=('candidate','no-transfer','shuffled','background')
def encode(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def occupied(mask):return {a for i,p in enumerate(PAIRS) if mask>>i&1 for a in p}
def initial(damage,budget):return (FULL^(1<<ORIGINAL[damage]),budget,8,False)
def moves(s,types,arm):
    mask,p,h,used=s;free=[i for i,pair in enumerate(PAIRS) if not occupied(mask).intersection(pair)]
    if p>=3:
        for i in free:yield ['form',i],(mask|(1<<i),p-3,h+2,used)
    if p>=1:
        for i in range(15):
            if mask>>i&1:yield ['break',i],(mask^(1<<i),p-1,h+2,used)
        if arm!='no-transfer':
            for donor in range(15):
                if not mask>>donor&1:continue
                for recipient in free:
                    catalysts=[None] if arm=='background' else [i for i in range(15) if i!=donor and mask>>i&1 and ((types[PAIRS[i][0]]^types[PAIRS[i][1]])==(types[PAIRS[recipient][0]]^types[PAIRS[recipient][1]]))==(arm=='candidate')]
                    for cat in catalysts:yield ['transfer',donor,recipient,cat],(mask^(1<<donor)|(1<<recipient),p-1,h+1,True)
def enumerate_case(types,damage,budget,arm):
    start=initial(damage,budget); parents={start:None}; todo=deque([start]); goals={}; edges=0
    def path(s):
        out=[]
        while parents[s] is not None:
            previous,action=parents[s];out.append(action);s=previous
        return list(reversed(out))
    while todo:
        s=todo.popleft();mask,p,h,used=s
        if p+h+mask.bit_count()!=10+budget:raise ValueError('Energy residual')
        for label,ok in (('partial',bool(mask>>ORIGINAL[damage]&1)),('whole',mask==FULL),('transfer-partial',used and bool(mask>>ORIGINAL[damage]&1)),('transfer-whole',used and mask==FULL)):
            if ok and label not in goals:goals[label]=path(s)
        for action,nxt in moves(s,types,arm):
            edges+=1
            if nxt not in parents:parents[nxt]=(s,action);todo.append(nxt)
    return dict(types=list(types),damage=damage,budget=budget,arm=arm,states=len(parents),edges=edges,state_sha256=hashlib.sha256(encode(sorted(parents))).hexdigest(),
                witnesses={k:history(types,damage,budget,v) for k,v in goals.items()})
def history(types,damage,budget,path):
    photons=10+budget;heat=0;objects=[];alive={};atom_history=[[] for _ in range(6)];events=[]
    def make(pair,route,energy_parent=None,catalyst=None):
        oid=len(objects);atoms=list(PAIRS[pair]);o=dict(id=oid,atoms=atoms,alive=True,route=route,
            atom_parents=[atom_history[a][:] for a in atoms],energy_parent=energy_parent,catalyst=catalyst)
        for a in atoms:atom_history[a].append(oid)
        objects.append(o);alive[pair]=oid;return oid
    def destroy(pair):
        oid=alive.pop(pair);objects[oid]['alive']=False;return oid
    for i in ORIGINAL:
        photons-=3;heat+=2;events.append(['genesis',i,make(i,'paid-genesis')])
    photons-=1;heat+=2;events.append(['damage',ORIGINAL[damage],destroy(ORIGINAL[damage])])
    for action in path:
        if action[0]=='form':
            _,i=action;photons-=3;heat+=2;events.append(['form',i,make(i,'form')])
        elif action[0]=='break':
            _,i=action;photons-=1;heat+=2;events.append(['break',i,destroy(i)])
        else:
            _,donor,recipient,cat=action;parent=destroy(donor);catalyst=alive[cat] if cat is not None else None
            photons-=1;heat+=1;events.append(['transfer',donor,recipient,cat,parent,make(recipient,'transfer',parent,catalyst)])
        if photons<0 or photons+heat+len(alive)!=10+budget:raise ValueError('Witness work borrowing')
    return dict(path=path,events=events,objects=objects,atom_history=atom_history,photons=photons,heat=heat,final_bonds=sorted(alive),startup_paid=9,damage_paid=1)
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--revision',required=True);args=p.parse_args()
    from .evidence_budget import Budget
    b=Budget(args.output,dict(raw=48*1024**2,archive=1024**2,restore=1024**2,failure=2*1024**2),52*1024**2)
    try:
        with b.create('raw','census.jsonl') as f:
            f.write(encode(dict(schema='transfer01',revision=args.revision,cases=5376,natural_worlds=0))+b'\n')
            for bits in range(64):
                types=tuple(bits>>i&1 for i in range(6))
                for damage in range(3):
                    for arm in ARMS:
                        for budget in range(7):f.write(encode(enumerate_case(types,damage,budget,arm))+b'\n')
    finally:
        with b.create('failure','budget.json',1024**2) as f:f.write(encode(copy.deepcopy(b.snapshot())))
if __name__=='__main__':main()
