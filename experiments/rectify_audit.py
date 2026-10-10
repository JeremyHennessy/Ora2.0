"""Independent parallel-conductance / whole-cycle accounting interpreter."""
from fractions import Fraction as Q
from itertools import product


def certificate(c,b,m,h,n,d,damage,k):
    units=4 if k==0 else k;buffers=1 if k==0 else k
    initial=units*(c+2*b)+4+buffers*h
    allowance=max([4*(c+2*b)+4+h]+[j*(c+2*b)+4+j*h for j in (1,2,4)])
    damaged=damage<units
    def cycle(broken):
        flows=[]
        for polarity in (0,1):
            if k==0:
                pair=(0,1) if polarity==0 else (2,3)
                available=not (broken and damage in pair)
                # Source + store + two diode resistances, each one.
                current=(Q(6)-3-2*d)/(1+1+1+1) if available else Q(0)
            else:
                branch_indices=[i for i in range(k) if (0 if i<(k+1)//2 else 1)==polarity and not (broken and i==damage)]
                conductance=Q(len(branch_indices),k+1)
                current=(Q(6)-3-d)*conductance/(1+conductance)
            imported=6*current;usable=3*current;loss=imported-usable
            cost=(units-int(broken and damaged)+buffers)*m
            flows.append((imported,usable,loss,cost))
        return flows
    normal=cycle(False);broken=cycle(damaged)
    totals=lambda flows:[sum(row[i] for row in flows) for i in range(4)]
    S,W,H,C=totals(normal);SD,WD,HD,CD=totals(broken)
    assert W>=C
    for repetition in range(n):
        assert repetition*(W-C)+normal[0][1]-normal[0][3]>=0
    bank=n*(W-C)
    assert bank+broken[0][1]-broken[0][3]>=0
    bank+=WD-CD
    price=Q(c+2*b) if damaged else Q(0)
    assert bank>=price
    bank-=price
    assert bank+normal[0][1]-normal[0][3]>=0
    used=(n+2)*S+SD;heat=(n+2)*H+HD;maintenance=(n+2)*C+CD
    reserve=(n+2)*W+WD-maintenance-price
    assert reserve<=128 and used<=72*(n+3)
    assert allowance+used==allowance-initial+initial+heat+maintenance+price+reserve
    return dict(fundable=True,failure=None,capital=initial,allowance=allowance,returned=allowance-initial,
        source=str(used),source_remaining=str(72*(n+3)-used),heat=str(heat),upkeep=str(maintenance),patch=str(price),reserve=str(reserve),
        whole=str(reserve-initial),post=str(2*(W-C)+WD-CD-price),live=units,raw=4-units,spare=1-int(damaged),scrap=int(damaged))


def panel():
    rows=[]
    for c,b,m,h,n,d,damage in product((1,2),(0,1),(Q(1,32),Q(1,8)),(1,4,8),(2,4),(Q(1,4),Q(1,2)),range(4)):
        rows.append(dict(c=c,b=b,m=str(m),h=h,n=n,d=str(d),damage=damage,
            arms={str(k):certificate(c,b,m,h,n,d,damage,k) for k in (0,1,2,4)}))
    return rows
