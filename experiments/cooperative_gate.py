"""Registered complete cooperative-potential opportunity calculation; no seeds."""
import argparse,hashlib,json,math
from collections import deque
from fractions import Fraction

START=(0,0,0,4,0)
ARMS=('candidate','independent','inverse')
ACTIONS=tuple((k,d) for k in ('capture','waste','atom0','atom1','bond') for d in (-1,1))
GUARD=1e-6
def coded(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def potential(s,B):return 6+2*(s[0]+s[1])-B*s[2]
def heat(s,B):return 38-potential(s,B)-6*s[3]-s[4]
def move(s,a,B):
    x,y,b,f,w=s;k,d=a;count=4
    if k in ('capture','waste'):
        count=f if d==1 else 4-f
        if not count:return None
        f-=d
        if k=='capture':w+=2*d
    elif k=='bond':
        if x!=1 or y!=1 or b!=(d==-1):return None
        b=1-b
    else:
        i=int(k[-1]);v=(x,y)[i]
        if b or v!=(d==-1):return None
        if i==0:x=1-x
        else:y=1-y
        w-=3*d
    t=(x,y,b,f,w)
    if w<0 or heat(t,B)<0:return None
    return t,count
def pref(s,k,arm):
    if k not in ('capture','waste'):return 4
    if arm=='independent':return 10
    favored=bool(s[2]) if arm=='candidate' else not s[2]
    return (16 if favored else 4) if k=='capture' else (4 if favored else 16)
def rate(s,a,B,arm):
    out=move(s,a,B)
    if not out:return Fraction(0)
    t,n=out
    return Fraction(n*pref(s,a[0],arm),2560*(1<<max(0,heat(s,B)-heat(t,B))))
def graph(B,parity):
    initial=(*START[:4],parity);seen={initial};queue=deque([initial]);edges=proposals=0
    while queue:
        s=queue.popleft()
        assert (s[4]+3*(s[0]+s[1]))%2==parity
        for a in ACTIONS:
            out=move(s,a,B)
            if not out:continue
            t,n=out;assert move(t,(a[0],-a[1]),B)[0]==s
            for arm in ARMS:
                left=math.comb(4,s[3])*2**heat(s,B)*rate(s,a,B,arm)
                right=math.comb(4,t[3])*2**heat(t,B)*rate(t,(a[0],-a[1]),B,arm)
                assert left==right
            edges+=1;proposals+=n
            if t not in seen:seen.add(t);queue.append(t)
        assert len(seen)<2000 and edges<20000
    states=sorted(seen)
    valid=sum(1 for x in (0,1) for y in (0,1) for b in (0,1) if not b or x*y for f in range(5) for w in range(39) if (w+3*(x+y))%2==parity and heat((x,y,b,f,w),B)>=0)
    return states,dict(states=len(states),excluded_energy_admissible_states=valid-len(states),directed_channels=edges,labelled_proposals=proposals,state_sha256=hashlib.sha256(coded(states)).hexdigest(),maximum_work=max(s[4] for s in states))
def flag(s,a,old):
    if a[0] in ('atom0','atom1','bond'):return 0
    return int(old or s[2] and a==('capture',1))
def loss(s,B):
    if not s[2] or s[4]<2:return None
    t=(0,s[1],0,s[3],s[4]-2)
    return t if heat(t,B)>=0 else None
def phases(B,states):
    goals=[s for s in states if s[2] and s[4]>=2 and s[3]<4 and heat(s,B)>=8 and move(s,('capture',-1),B)]
    def maximum(s):
        t=loss(s,B);assert t in states
        candidates=[g[4] for g in goals if g[3]<s[3] and heat(g,B)>=heat(s,B) and g[4]>max(0,6-potential(g,B))]
        return max(candidates,default=-1)
    return maximum
def startup(B,states,repair,arm):
    nodes=[(*s,z) for s in states for z in ((0,1) if s[2] else (0,))];index={s:i for i,s in enumerate(nodes)};rows=[]
    for node in nodes:
        s=node[:5];r=[];total=Fraction(0)
        for a in ACTIONS:
            p=rate(s,a,B,arm)
            if p:
                t=move(s,a,B)[0];r.append((index[(*t,flag(s,a,node[5]))],float(p)));total+=p
        assert total<=1;r.append((index[node],float(1-total)));rows.append(r)
    mass=[0.]*len(nodes);mass[index[(*START,0)]]=1.
    for _ in range(2048):
        nxt=[0.]*len(nodes)
        for i,v in enumerate(mass):
            for j,p in rows[i]:nxt[j]+=v*p
        mass=nxt
    assert abs(sum(mass)-1)<1e-10
    exposed=feasible=retained=depleted=0.;phase=[]
    for n,p in zip(nodes,mass):
        s=n[:5];retained+=p*bool(s[2]);depleted+=p*(s[3]==0)
        if s[2] and n[5] and s[3]>=1 and loss(s,B):
            best=repair(s);okay=best>s[4]
            phase.append(dict(state=list(s),probability=p,post_loss=list(loss(s,B)),maximum_rebuilt_work=best,feasible=okay));exposed+=p;feasible+=p*okay
    return dict(arm=arm,distribution=[[list(s),p] for s,p in zip(nodes,mass)],mass=sum(mass),bound_probability=retained,fuel_depletion_probability=depleted,exposed_probability=exposed,feasible_exposed_probability=feasible,phases=phase)
def record(revision):
    cases=[]
    for B in range(7):
        before,g0=graph(B,0);after,g1=graph(B,1);repair=phases(B,after);arms=[startup(B,before,repair,a) for a in ARMS]
        candidate=arms[0]['feasible_exposed_probability'];shuffle=(candidate+arms[2]['feasible_exposed_probability'])/2
        cases.append(dict(binding=B,initial_structural_capital=6,bound_potential=10-B,capital_drawdown_debit=max(0,B-4),graphs=[g0,g1],arms=arms,full_shuffle_feasible_exposure=shuffle,admission_passed=candidate-GUARD>=.75))
    return dict(schema='cooperative01-admission',source_revision=revision,natural_worlds=0,numerical_guard=GUARD,cases=cases,admitted_bindings=[c['binding'] for c in cases if c['admission_passed']])
def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args();print(json.dumps(record(a.revision),sort_keys=True))
if __name__=='__main__':main()
