"""Exact finite relative-coordinate transport kernels; prepared apparatus only."""
from fractions import Fraction as Q
import json

def kernel(mu,k,d,joined,y):
    R=8+4*mu+k+d;states={(0,y,'A'):1}
    for _ in range(16):
        new={}
        for (x,y,s),weight in states.items():
            events=[]
            for h in (-1,1):
                events.append((((x+h)%4,y,s) if s=='A' else (x,y,s),4))
                if joined:events.append((((x-h)%4,0,s) if s=='A' else (0,0,s),mu))
                else:
                    events.append((((x-h)%4,(y-h)%4,s) if s=='A' else (0,(y-h)%4,s),mu))
                    events.append(((x,(y+h)%4,s),mu))
            if joined:events.append(((x,y,s),2*mu))
            events.append(((0,y,'C') if s=='A' and x==y else (x,y,s),k))
            events.append(((0,y,'L') if s=='A' else (x,y,s),d))
            assert sum(v for _,v in events)==R
            for z,v in events:
                if v:new[z]=new.get(z,0)+weight*v
        states=new
    denominator=R**16;assert sum(states.values())==denominator
    terminal=[Q(sum(w for (x,y,s),w in states.items() if y==j),denominator) for j in range(4)]
    capture=Q(sum(w for (x,y,s),w in states.items() if s=='C'),denominator)
    return terminal,capture

def calculate():
    rows=[]
    for mu in (0,1,4,16):
      for k in (1,4,16):
       for d in (0,1,4,16):
        J,p=kernel(mu,k,d,True,0);free=[kernel(mu,k,d,False,y) for y in range(4)]
        assert sum(J)==1 and J[0]==1 and p==free[0][1]
        totals=[]
        for y in range(4):
            dist=[Q(int(j==y)) for j in range(4)];total=Q(0)
            for _ in range(8):
                total+=sum(dist[j]*free[j][1] for j in range(4))
                dist=[sum(dist[j]*free[j][0][z] for j in range(4)) for z in range(4)]
                assert sum(dist)==1
            totals.append(total)
        joined=8*p
        if mu==0:assert joined==totals[0]
        rows.append(dict(mu=mu,k=k,d=d,joined=str(joined),free_colocated=str(totals[0]),free_best=str(max(totals)),shuffle=str(sum(totals)/4),first_packet=str(p),extra_captures=str(joined-max(totals)),extra_work_budget=str(4*(joined-max(totals)))))
    return rows

if __name__=='__main__':print(json.dumps(calculate(),sort_keys=True))
