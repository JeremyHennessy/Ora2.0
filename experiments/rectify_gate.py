"""Frozen directional-conversion accounting certificates; no world dynamics."""
from fractions import Fraction as F
from itertools import product


def arm(c,b,m,h,n,d,damage,k):
    bridge=k==0;count=4 if bridge else k;stores=1 if bridge else k
    capital=count*(c+2*b)+4+stores*h
    allowance=max(j*(c+2*b)+4+j*h for j in (1,2,4))
    allowance=max(allowance,4*(c+2*b)+4+h)
    alive=set(range(count));reserve=F(0);source=F(0);heat=F(0)
    upkeep=F(0);patch=F(0);post_work=F(0);post_upkeep=F(0);failure=None
    scrap=0;spare=1;raw=4-count
    def slot(phase,post):
        nonlocal reserve,source,heat,upkeep,post_work,post_upkeep,failure
        if bridge:
            active=set((0,1) if phase==0 else (2,3)).issubset(alive)
            resistance=F(4);drop=2*d
        else:
            positive=set(range((k+1)//2));active=len(alive&(positive if phase==0 else set(range(k))-positive))
            resistance=1+F(k+1,active) if active else F(1);drop=d
        current=(3-drop)/resistance if active else F(0)
        work=3*current;draw=6*current;loss=drop*current+resistance*current**2
        assert draw==work+loss
        reserve+=work;source+=draw;heat+=loss
        if post:post_work+=work
        charge=(len(alive)+stores)*m
        if reserve<charge:failure='upkeep';return False
        reserve-=charge;upkeep+=charge
        if post:post_upkeep+=charge
        return True
    for _ in range(n):
        for phase in (0,1):
            if not slot(phase,False):break
        if failure:break
    if not failure:
        needed=damage in alive
        if needed:alive.remove(damage);scrap=1
        for phase in (0,1):
            if not slot(phase,True):break
        if not failure:
            price=F(c+2*b) if needed else F(0)
            if reserve<price:failure='patch'
            else:
                reserve-=price;patch=price
                if needed:alive.add(damage);spare=0
                for _ in range(2):
                    for phase in (0,1):
                        if not slot(phase,True):break
                    if failure:break
    assert len(alive)+raw+spare+scrap==5
    assert allowance+source==allowance-capital+capital+heat+upkeep+patch+reserve
    assert source<=36*2*(n+3) and reserve<=128
    return dict(fundable=not failure,failure=failure,capital=capital,allowance=allowance,returned=allowance-capital,
        source=str(source),source_remaining=str(36*2*(n+3)-source),heat=str(heat),upkeep=str(upkeep),patch=str(patch),reserve=str(reserve),
        whole=str(reserve-capital) if not failure else None,post=str(post_work-post_upkeep-patch) if not failure else None,
        live=len(alive),raw=raw,spare=spare,scrap=scrap)


def panel():
    return [dict(c=c,b=b,m=str(m),h=h,n=n,d=str(d),damage=damage,
        arms={str(k):arm(c,b,m,h,n,d,damage,k) for k in (0,1,2,4)})
        for c,b,m,h,n,d,damage in product((1,2),(0,1),(F(1,32),F(1,8)),(1,4,8),(2,4),(F(1,4),F(1,2)),range(4))]
