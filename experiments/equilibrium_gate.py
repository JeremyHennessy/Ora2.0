"""Exact population/flow census of unchanged LOCAL physical dynamics."""
import argparse,hashlib,json,math
from collections import deque
from fractions import Fraction
from .local_world import transition,heat,pack,ARMS

STEPS=[(k,0,d) for k in ('capture','decay','work') for d in (-1,1)]+[('activate',j,d) for j in range(2) for d in (-1,1)]+[('bond',0,d) for d in (-1,1)]+[('hop',j,1) for j in range(2)]
def exact(q):return [q.numerator,q.denominator]
def multiplicity(s,a):
    k,j,d=a
    if k=='capture':return s[0] if d==1 else s[1]
    if k in ('work','decay'):return s[1] if d==1 else 10-s[0]-s[1]
    return 1
def weight(s):return math.comb(10,s[0])*math.comb(10-s[0],s[1])*2**heat(s)

def census(arm):
    root=(10,0,0,0,0,0);seen={root};queue=deque([root]);edges=0;flux={k:Fraction(0) for k in ('work_forward','work_reverse','activation_debit','activation_refund','total_net')}
    hist={name:{} for name in ('bound','active','work','heat')};z=0;protected=protectedbound=0
    while queue:
        s=queue.popleft();g=weight(s);z+=g;h=heat(s)
        for name,value in zip(hist,(s[3],s[2].bit_count(),s[5],h)):hist[name][value]=hist[name].get(value,0)+g
        if h>=8:protected+=g;protectedbound+=g*s[3]
        for a in STEPS:
            r=transition(s,a,arm)
            if r is None:continue
            t,rate=r;k,j,d=a;back=(k,j,1 if k=='hop' else -d);u,qr=transition(t,back,arm);assert u==s
            flow=Fraction(g*multiplicity(s,a),68)*rate
            reverse=Fraction(weight(t)*multiplicity(t,back),68)*qr
            assert flow==reverse
            flux['total_net']+=flow*(t[5]-s[5])
            if k=='work':flux['work_forward' if d==1 else 'work_reverse']+=flow*2
            if k=='activate':flux['activation_debit' if d==1 else 'activation_refund']+=flow*3
            edges+=1
            if t not in seen:seen.add(t);queue.append(t)
            if len(seen)>250000 or edges>4000000:raise ValueError('Census cap')
    assert {(10,0,0,0,p,0) for p in range(4)}<=seen and flux['total_net']==0
    expectations={name:exact(Fraction(sum(k*v for k,v in values.items()),z)) for name,values in hist.items()}
    return dict(arm=arm,states=len(seen),edges=edges,state_sha256=hashlib.sha256(pack(sorted(seen))).hexdigest(),normalizer=z,histograms={name:{str(k):exact(Fraction(v,z)) for k,v in sorted(values.items())} for name,values in hist.items()},expectations=expectations,bound_probability=expectations['bound'],protected_heat_probability=exact(Fraction(protected,z)),conditional_bound_probability=exact(Fraction(protectedbound,protected)),flows={k:exact(v/z) for k,v in flux.items()},connected=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args()
    print(json.dumps(dict(schema='equilibrium01',source_revision=a.revision,law_revision='cb2b08c94475bfb96333817f448cd4a4037c7e42',natural_worlds=0,records=[census(x) for x in ARMS]),sort_keys=True))
if __name__=='__main__':main()
