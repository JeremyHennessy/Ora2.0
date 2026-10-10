"""Independent Cartesian census, labelled law and gather probability interpreter."""
import argparse,hashlib,json,math
from fractions import Fraction

KINDS=('bond','atom1','atom0','waste','capture')
def encode(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def thermal(s,binding):return 32-2*s[0]-2*s[1]+binding*s[2]-6*s[3]-s[4]
def apply(s,kind,d,B):
    z=list(s);multiplicity=4
    if kind=='bond':
        if z[0]*z[1]!=1 or z[2]!=(d<0):return None
        z[2]=int(d>0)
    elif kind.startswith('atom'):
        target=int(kind[-1])
        if z[2] or z[target]!=(d<0):return None
        z[target]=int(d>0);z[4]-=3*d
    else:
        multiplicity=z[3] if d>0 else 4-z[3]
        if multiplicity==0:return None
        z[3]-=d
        if kind=='capture':z[4]+=d*2
    t=tuple(z)
    if z[4]<0 or thermal(t,B)<0:return None
    return t,multiplicity
def probability(s,k,d,B,arm):
    out=apply(s,k,d,B)
    if out is None:return Fraction(0)
    t,n=out
    barrier=4
    if k in ('capture','waste'):
        if arm=='independent':barrier=10
        else:
            high=(s[2]==1) if arm=='candidate' else (s[2]==0)
            barrier=(16 if high else 4) if k=='capture' else (4 if high else 16)
    return Fraction(n,40)*Fraction(barrier,64)*Fraction(1,2**max(0,thermal(s,B)-thermal(t,B)))
def census(B,p):
    allstates=sorted((a,b,c,f,w) for a in (0,1) for b in (0,1) for c in (0,1) if not c or a*b for f in range(5) for w in range(39) if (w+3*(a+b))%2==p and thermal((a,b,c,f,w),B)>=0)
    seen={(0,0,0,4,p)};stack=list(seen);edges=labelled=0
    while stack:
        s=stack.pop()
        for d in (1,-1):
            for k in KINDS:
                out=apply(s,k,d,B)
                if out is None:continue
                t,n=out;assert apply(t,k,-d,B)[0]==s
                for arm in ('inverse','independent','candidate'):
                    assert probability(s,k,d,B,arm)*math.comb(4,s[3])*2**thermal(s,B)==probability(t,k,-d,B,arm)*math.comb(4,t[3])*2**thermal(t,B)
                edges+=1;labelled+=n
                if t not in seen:seen.add(t);stack.append(t)
    assert seen.issubset(set(allstates))
    excluded=set(allstates)-seen
    for s in excluded:
        for k in KINDS:
            for d in (-1,1):
                out=apply(s,k,d,B)
                assert out is None or out[0] in excluded
    reachable=sorted(seen)
    return reachable,dict(states=len(seen),excluded_energy_admissible_states=len(excluded),directed_channels=edges,labelled_proposals=labelled,state_sha256=hashlib.sha256(encode(reachable)).hexdigest(),maximum_work=max(s[4] for s in seen))
def destruction(s,B):
    if s[2]!=1 or s[4]<2:return None
    target=(0,s[1],0,s[3],s[4]-2)
    assert thermal(target,B)-thermal(s,B)==4-B
    return target if thermal(target,B)>=0 else None
def newflag(s,k,d,z):return 0 if k in ('bond','atom0','atom1') else int(z or k=='capture' and d>0 and s[2])
def phase_max(s,B,component):
    start=destruction(s,B);assert start in component
    best=-1
    for g in component:
        if not g[2] or g[3]>=s[3] or g[4]<=max(0,B-4) or thermal(g,B)<max(8,thermal(s,B)):continue
        # A last forward bound capture establishes the current pair's function;
        # reciprocal connectivity reaches its predecessor without a supplied pair.
        prior=apply(g,'capture',-1,B)
        if prior is not None and prior[0] in component:best=max(best,g[4])
    return best
def calculate(B,physical,component,arm):
    nodes=sorted((*s,z) for s in physical for z in range(1+s[2]));index={s:i for i,s in enumerate(nodes)};incoming=[[] for _ in nodes]
    for i,n in enumerate(nodes):
        s=n[:5];total=Fraction(0)
        for d in (1,-1):
            for k in KINDS:
                p=probability(s,k,d,B,arm)
                if p:
                    t=apply(s,k,d,B)[0];j=index[(*t,newflag(s,k,d,n[5]))];incoming[j].append((i,float(p)));total+=p
        assert 0<=total<=1;incoming[i].append((i,float(1-total)))
    mass=[0.]*len(nodes);mass[index[(0,0,0,4,0,0)]]=1.
    for _ in range(2048):mass=[math.fsum(mass[i]*p for i,p in row) for row in incoming]
    assert abs(math.fsum(mass)-1)<1e-10
    rows=[];exposed=[];feasible=[]
    for n,p in zip(nodes,mass):
        s=n[:5]
        if s[2] and n[5] and s[3]>0 and destruction(s,B) is not None:
            best=phase_max(s,B,component);good=best>s[4];exposed.append(p)
            if good:feasible.append(p)
            rows.append(dict(state=list(s),probability=p,post_loss=list(destruction(s,B)),maximum_rebuilt_work=best,feasible=good))
    return dict(arm=arm,distribution=[[list(n),p] for n,p in zip(nodes,mass)],mass=math.fsum(mass),bound_probability=math.fsum(p for n,p in zip(nodes,mass) if n[2]),fuel_depletion_probability=math.fsum(p for n,p in zip(nodes,mass) if n[3]==0),exposed_probability=math.fsum(exposed),feasible_exposed_probability=math.fsum(feasible),phases=rows)
def compare(a,b):
    if isinstance(a,float) or isinstance(b,float):assert abs(a-b)<1e-10;return
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:compare(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):compare(x,y)
    else:assert a==b
def audit(record,revision):
    assert record['schema']=='cooperative01-admission' and record['source_revision']==revision and record['natural_worlds']==0 and record['numerical_guard']==1e-6
    assert len(record['cases'])==7;decisions=[]
    for B,c in enumerate(record['cases']):
        assert c['binding']==B and c['initial_structural_capital']==6 and c['bound_potential']==10-B and c['capital_drawdown_debit']==max(0,B-4)
        before,g0=census(B,0);after,g1=census(B,1);assert c['graphs']==[g0,g1];component=set(after);calculated=[]
        assert [a['arm'] for a in c['arms']]==['candidate','independent','inverse']
        for r in c['arms']:
            other=calculate(B,before,component,r['arm']);compare(r,other);calculated.append(other)
        probability=calculated[0]['feasible_exposed_probability'];shuffle=(probability+calculated[2]['feasible_exposed_probability'])/2
        compare(c['full_shuffle_feasible_exposure'],shuffle);assert c['admission_passed']==(probability-1e-6>=.75)
        decisions.append(dict(binding=B,graphs=[g0,g1],arms=[{k:v for k,v in r.items() if k not in ('distribution','phases')} for r in calculated],full_shuffle_feasible_exposure=shuffle,admission_passed=c['admission_passed']))
    admitted=[c['binding'] for c in decisions if c['admission_passed']];assert admitted==record['admitted_bindings']
    return dict(verified=True,source_revision=revision,natural_worlds=0,cases=decisions,admitted_bindings=admitted,admission_passed=bool(admitted),classification='ADMITTED_FOR_PANEL_DESIGN' if admitted else 'NOT_ADMITTED_OPPORTUNITY',self_maintenance_demonstrated=False)
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:r=json.load(f)
        print(json.dumps(audit(r,a.revision),sort_keys=True))
    except (AssertionError,KeyError,ValueError,TypeError) as e:print(json.dumps(dict(refused=True,error=str(e))));raise SystemExit(2)
if __name__=='__main__':main()
