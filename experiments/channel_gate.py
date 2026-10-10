"""Reversible unit chemistry admission; no spatial world or organism installed."""
import argparse
import hashlib
import json
from fractions import Fraction

ARMS=('candidate','independent','shuffled')
ENERGY=(6,4,0)
ACTIONS=[(name,d) for name in ('capture','decay','work') for d in (-1,1)]

def move(s,a,arm,contact):
    h,w,q=s;name,d=a
    first,last,heat,work={'capture':(0,1,2,0),'decay':(1,2,4,0),'work':(1,2,2,2)}[name]
    if q!=(first if d==1 else last):return None
    t=(h+d*heat,w+d*work,last if d==1 else first)
    if min(t[:2])<0:return None
    numerator=4 if name!='work' else {'candidate':(2,32),'independent':(17,17),'shuffled':(32,2)}[arm][contact]
    rate=Fraction(numerator,64*(2**max(0,-d*heat)))
    return t,rate

def local(arm,contact):
    states=edges=0;digest=hashlib.sha256()
    for q in range(3):
        for h in range(33):
            for w in range(33):
                s=(h,w,q);states+=1
                for a in ACTIONS:
                    r=move(s,a,arm,contact)
                    if r is None:continue
                    t,rate=r;back=move(t,(a[0],-a[1]),arm,contact)
                    assert back is not None and back[0]==s
                    assert h+w+ENERGY[q]==t[0]+t[1]+ENERGY[t[2]]
                    assert 2**h*rate==2**t[0]*back[1]
                    edges+=1;digest.update(json.dumps([list(s),list(a),list(t),[rate.numerator,rate.denominator]],separators=(',',':')).encode()+b'\n')
    return dict(arm=arm,contact=contact,states=states,edges=edges,edge_sha256=digest.hexdigest())

def witness(n,arm,contact):
    h,w=8,0;tokens=[0]*n;origins=[None]*n;states=[[h,w,tokens.copy()]];events=[];fresh=thermal=0
    for token in range(n):
        for a in (('capture',1),('work',1),('decay',-1),('work',1)):
            t,rate=move((h,w,tokens[token]),a,arm,contact)
            event=dict(token=token,action=list(a),rate=[rate.numerator,rate.denominator])
            if a==('capture',1):origins[token]='fresh-fuel'
            if a==('decay',-1):origins[token]='thermal-reactivation'
            if a==('work',1):
                event['output_origin']=origins[token]
                if origins[token]=='fresh-fuel':fresh+=2
                else:thermal+=2
                origins[token]=None
            h,w,q=t;tokens[token]=q
            assert h+w+sum(ENERGY[q] for q in tokens)==6*n+8
            events.append(event);states.append([h,w,tokens.copy()])
    return dict(tokens=n,arm=arm,contact=contact,states=states,events=events,total_energy=6*n+8,material_units=n,fresh_fuel_work=fresh,thermal_work=thermal,gross_work=w,final_heat=h,claimed_ceiling=2*n,conservation_ceiling=6*n,bound_falsified=w>2*n and h>=8)

def produce(revision):
    return dict(schema='channel01',source_revision=revision,natural_worlds=0,controlled_certificates=48,full_costs_known=False,local_grids=[local(a,b) for a in ARMS for b in (0,1)],certificates=[witness(n,a,b) for n in range(1,9) for a in ARMS for b in (0,1)])

def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args();print(json.dumps(produce(a.revision),sort_keys=True))

if __name__=='__main__':main()
