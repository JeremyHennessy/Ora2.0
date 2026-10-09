"""CONDENSE-01 raw-start affinity/chemical-work feasibility, not natural dynamics."""
import argparse
from collections import deque
import hashlib
import json
from math import comb

ARMS=('candidate','affinity-ghost','catalysis-ghost','passive')
PAIRS=((0,1),(0,2),(1,2))


def pack(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def affinity(arm):return int(arm!='affinity-ghost')
def bank(s):return 3 if s[5]==0 else 2
def heat(s,arm):return 35-6*s[0]-2*s[1].bit_count()+affinity(arm)*s[2].bit_count()-s[4]-bank(s)
def degree(s,i):return sum(bool(s[2]>>j&1) for j,p in enumerate(PAIRS) if i in p)


def connected(s,i):
    group={i};changed=True
    while changed:
        changed=False
        for j,(a,b) in enumerate(PAIRS):
            if s[2]>>j&1 and (a in group or b in group) and not {a,b}<=group:
                group.update((a,b));changed=True
    return group


def accelerated(s,i,arm):
    others=[j for j in range(3) if j!=i];edge=PAIRS.index(tuple(others))
    return arm!='catalysis-ghost' and bool(s[2]>>edge&1) and (s[3]>>i&1)==(s[3]>>others[0]&1)


def edges(s,arm):
    f,a,b,p,load,phase=s
    for i in range(3):
        if degree(s,i)==0:
            active=bool(a>>i&1)
            direction=-1 if active else 1
            if arm!='passive' and (f<4 and load>0 if active else f>0):
                newphase=2 if phase==1 and i==2 and direction==1 and degree(s,0)>0 else phase
                t=(f-direction,a^(1<<i),b,p,load+direction,newphase)
                if heat(t,arm)>=0:yield (0,i,direction),t
            t=(f,a^(1<<i),b,p,load,phase)
            if heat(t,arm)>=0:yield (1,i,direction),t
        left,right=PAIRS[i]
        bound=bool(b>>i&1)
        if bound or a>>left&1 and a>>right&1 and (p>>left&1)==(p>>right&1):
            t=(f,a,b^(1<<i),p,load,phase)
            if heat(t,arm)>=0:yield (2,i,-1 if bound else 1),t
        bits=sum(1<<j for j in connected(s,i))
        for direction in (-1,1):yield (3,i,direction),(f,a,b,p^bits,load,phase)
    if phase==0 and a&1 and degree(s,0)>0 and load>=1:
        newb=b&~sum(1<<j for j,pair in enumerate(PAIRS) if 0 in pair)
        yield (4,0,1),(f,a&~1,newb,p,load,1)


def probability(s,action,t,arm):
    c,i,d=action
    if c==4:raise ValueError('Paid operator action')
    numerator=(s[0] if d>0 else 4-s[0]) if c==0 else 4
    barrier=(1 if accelerated(s,i,arm) else 4) if c==0 else (3 if c==1 else 2 if c==2 else 1)
    return numerator,barrier+max(0,heat(s,arm)-heat(t,arm))


def endpoint(s,arm):return s[5]==2 and bool(s[1]&1) and degree(s,0)>0 and s[4]>=3 and heat(s,arm)>=8


def provenance(arm,start,path):
    s=start;objects=[];owners=[];traces=[[] for _ in range(3)]
    fuel=[dict(id=i,state='F',events=[]) for i in range(4)];bonds=[];bond_owner={};events=[];states=[list(s)+[heat(s,arm)]]
    def birth(atom,kind,parent=None,food=None):
        identity=len(objects);objects.append(dict(id=identity,atom=atom,state=kind,parent=parent,food=food,alive=True))
        traces[atom].append(identity);return identity
    for i in range(3):owners.append(birth(i,'R'))
    for action in path:
        matches=[t for proposal,t in edges(s,arm) if list(proposal)==action]
        if len(matches)!=1:raise ValueError('Impossible controlled path')
        t=matches[0];c,i,d=action;event=dict(action=action)
        if c in (0,1,4):
            parent=owners[i];objects[parent]['alive']=False;food=None
            if c==0:
                token=next(x for x in fuel if x['state']==('F' if d>0 else 'S'))
                food=token['id'];token['state']='S' if d>0 else 'F';token['events'].append(len(events))
            owners[i]=birth(i,'M' if c!=4 and d>0 else 'R',parent,food)
            event.update(parent=parent,object=owners[i],food=food)
            if c==4:
                lost=[]
                for pair in list(bond_owner):
                    if i in PAIRS[pair]:
                        identity=bond_owner.pop(pair);bonds[identity]['alive']=False;lost.append(identity)
                event['lost_bonds']=sorted(lost)
        elif c==2:
            if d>0:
                identity=len(bonds);bonds.append(dict(id=identity,atoms=list(PAIRS[i]),objects=[owners[j] for j in PAIRS[i]],alive=True,stabilization=affinity(arm)))
                bond_owner[i]=identity
            else:
                identity=bond_owner.pop(i);bonds[identity]['alive']=False
            event['bond']=identity
        else:event['moved_atoms']=sorted(connected(s,i))
        events.append(event);s=t;states.append(list(s)+[heat(s,arm)])
    return dict(start=list(start),path=path,states=states,events=events,objects=objects,
                fuel=fuel,bonds=bonds,atom_history=traces,total_energy=35,material_units=7,
                operator_spent=3-bank(s),endpoint=endpoint(s,arm))


def enumerate_arm(arm):
    starts=[(4,0,0,p,0,0) for p in range(8)]
    pending=deque(starts);parents={s:None for s in starts};count=physical=checks=0;first=None;signatures=set()
    while pending:
        s=pending.popleft()
        if endpoint(s,arm) and first is None:first=s
        for action,t in edges(s,arm):
            count+=1
            if count>3000000:raise ValueError('Edge cap')
            if action[0]<4:
                physical+=1;n,e=probability(s,action,t,arm)
                reverse=(action[0],action[1],-action[2]);matches=[u for a,u in edges(t,arm) if a==reverse and u[:5]==s[:5]]
                if len(matches)!=1:raise ValueError('Missing physical reverse')
                u=matches[0];m,k=probability(t,reverse,u,arm);dh=heat(t,arm)-heat(s,arm)
                signature=(s[0],t[0],n,e,m,k,dh)
                if signature not in signatures:
                    signatures.add(signature)
                    lhs=comb(4,s[0])*n*2**(k+max(0,-dh));rhs=comb(4,t[0])*m*2**(e+max(0,dh))
                    if lhs!=rhs or not 0<n<=96*2**e:raise ValueError('Hidden thermodynamic drive')
                    checks+=1
            if t not in parents:
                parents[t]=(s,action);pending.append(t)
                if len(parents)>150000:raise ValueError('State cap')
    cursor=first;path=[]
    while cursor is not None and parents[cursor] is not None:
        before,action=parents[cursor];path.append(list(action));cursor=before
    path.reverse();states=sorted(parents);endpoints=[s for s in states if endpoint(s,arm)]
    return dict(arm=arm,states=len(states),edges=count,physical_edges=physical,rate_signatures=checks,
                state_sha256=hashlib.sha256(pack(states)).hexdigest(),endpoint_states=len(endpoints),
                minimum_net_fuel=min((4-s[0] for s in endpoints),default=None),
                witness=None if first is None else provenance(arm,cursor,path))


def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args()
    print(json.dumps(dict(schema='condense01',source_revision=a.revision,natural_worlds=0,
                         raw_position_assignments=8,records=[enumerate_arm(arm) for arm in ARMS]),sort_keys=True))


if __name__=='__main__':main()
