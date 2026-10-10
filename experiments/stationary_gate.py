"""Prospective matched-clock stationary comparator; prepared apparatus only."""
from fractions import Fraction as Q
import json

def packet(mu,k,d,moving):
    rate=8+4*mu+k+d
    states={(0,0):1}
    for _ in range(16):
        new={}
        for (x,status),count in states.items():
            events=[]
            for step in (-1,1):
                events.append((((x+step)%4,status) if status==0 else (0,status),4))
                events.append((((x-step)%4,status) if status==0 and moving else (x,status),mu))
            events.extend([((x,status),2*mu),((0,1) if status==0 and x==0 else (x,status),k),((0,2) if status==0 else (x,status),d)])
            assert sum(w for _,w in events)==rate
            for state,w in events:
                if w:new[state]=new.get(state,0)+count*w
        states=new
    assert sum(states.values())==rate**16
    return Q(sum(w for (x,s),w in states.items() if s==1),rate**16)

def calculate():
    rows=[]
    for mu in (0,1,4,16):
      for k in (1,4,16):
       for d in (0,1,4,16):
        tether=8*packet(mu,k,d,True);fixed=8*packet(mu,k,d,False)
        rows.append(dict(mu=mu,k=k,d=d,tether=str(tether),stationary=str(fixed),stationary_extra_work=str(4*(fixed-tether))))
    return rows

if __name__=='__main__':print(json.dumps(calculate(),sort_keys=True))
