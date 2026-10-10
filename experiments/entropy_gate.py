"""Finite mixing-source reachability and unconditional startup probability."""
from collections import deque
from fractions import Fraction
import argparse,hashlib,json,math

ARMS=('candidate','independent','inverted')
ACTIONS=tuple((k,d) for k in ('work','passive','form') for d in (-1,1))
START=(10,0,0)
GUARD=1e-6
def pack(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def heat(s):return 20-2*s[1]-s[2]
def pref(s,k,arm):
    if k=='form':return 4
    if arm=='independent':return 10
    working=(s[1]==1) if arm=='candidate' else (s[1]==0)
    return (16 if working else 4) if k=='work' else (4 if working else 16)
def move(s,a):
    n,b,w=s;k,d=a
    if k=='form':
        if b!=(d==-1):return None
        t=(n,1-b,w-3*d);count=10
    else:
        count=n if d==1 else 10-n
        if not count:return None
        t=(n-d,b,w+(d if k=='work' else 0))
    if t[2]<0 or heat(t)<0:return None
    return t,count
def probability(s,a,arm):
    outcome=move(s,a)
    if outcome is None:return Fraction(0)
    t,count=outcome
    return Fraction(count*pref(s,a[0],arm),3840*(1<<max(0,heat(s)-heat(t))))
def graph():
    seen={START};q=deque([START]);edges=weighted=0
    while q:
        s=q.popleft()
        for a in ACTIONS:
            result=move(s,a)
            if not result:continue
            t,count=result;back=move(t,(a[0],-a[1]));assert back and back[0]==s
            for arm in ARMS:
                gs=math.comb(10,s[0])*2**heat(s);gt=math.comb(10,t[0])*2**heat(t)
                assert gs*probability(s,a,arm)==gt*probability(t,(a[0],-a[1]),arm)
            edges+=1;weighted+=count
            if t not in seen:seen.add(t);q.append(t)
        assert len(seen)<=2000 and edges<=20000
    return sorted(seen),dict(states=len(seen),directed_channels=edges,labelled_proposals=weighted,
        state_sha256=hashlib.sha256(pack(sorted(seen))).hexdigest(),maximum_work=max(s[2] for s in seen))
def next_flag(s,t,flag,a):
    if a[0]=='form':return 0
    return int(flag or a==('work',1) and s[1]==1)
def repair_max(n,w):
    start=(n,0,w-2,0);seen={start};q=deque([start]);maximum=-1
    while q:
        n,b,w,flag=q.popleft();s=(n,b,w)
        if b and flag:maximum=max(maximum,w)
        for a in ACTIONS:
            out=move(s,a)
            if out:
                t,_=out;node=(*t,next_flag(s,t,flag,a))
                if node not in seen:seen.add(node);q.append(node)
    return maximum
def startup(states,arm):
    augmented=[(*s,f) for s in states for f in ((0,1) if s[1] else (0,))];index={s:i for i,s in enumerate(augmented)}
    rows=[]
    for node in augmented:
        s=node[:3];flag=node[3];row=[];total=Fraction(0)
        for a in ACTIONS:
            p=probability(s,a,arm)
            if p:
                t=move(s,a)[0];row.append((index[(*t,next_flag(s,t,flag,a))],float(p)));total+=p
        assert total<=1;row.append((index[node],float(1-total)));rows.append(row)
    mass=[0.]*len(augmented);mass[index[(*START,0)]]=1.
    for _ in range(2048):
        target=[0.]*len(mass)
        for i,value in enumerate(mass):
            for j,p in rows[i]:target[j]+=value*p
        mass=target
    assert abs(sum(mass)-1)<1e-10
    phase=[];exposed=feasible=0.
    for node,p in zip(augmented,mass):
        n,b,w,f=node
        if b and f and w>=2:
            maximum=repair_max(n,w);okay=maximum>w
            phase.append(dict(left=n,pre_work=w,probability=p,maximum_rebuilt_work=maximum,feasible=okay))
            exposed+=p
            if okay:feasible+=p
    return dict(arm=arm,distribution=[[list(s),p] for s,p in zip(augmented,mass)],mass=sum(mass),
        exposed_probability=exposed,feasible_exposed_probability=feasible,phases=phase)
def certificate():
    actions=[('work',1)]*3+[('form',1)]+[('work',1)]*2+[('loss',1)]+[('work',1)]*3+[('form',1)]+[('work',1)]*2+[('passive',-1),('work',1)]
    s=START;rows=[];pre=None
    for a in actions:
        before=s
        if a[0]=='loss':assert s==(5,1,2);pre=s;s=(5,0,0)
        else:out=move(s,a);assert out;s=out[0]
        rows.append(dict(action=list(a),before=list(before),after=list(s),heat=heat(s)))
    assert s==(0,1,3) and heat(s)==15
    return dict(rows=rows,score=dict(final_work=3,post_gain=3-pre[2],net_transfers=11,formation=6,loss=2,
        source_heat_drawdown=5,final_bound_potential=2,whole_surplus=3),controlled_only=True)
def record(revision):
    states,g=graph();arms=[startup(states,a) for a in ARMS]
    candidate=arms[0]['feasible_exposed_probability']
    return dict(schema='entropy01-admission',source_revision=revision,natural_worlds=0,graph=g,arms=arms,
        certificate=certificate(),numerical_guard=GUARD,admission_passed=candidate-GUARD>=.75)
def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args();print(json.dumps(record(a.revision),sort_keys=True))
if __name__=='__main__':main()
