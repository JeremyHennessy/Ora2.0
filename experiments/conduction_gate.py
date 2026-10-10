"""CONDUCTION-01 exact prospective work ledger, not a natural-world simulator."""
from fractions import Fraction as Q
from itertools import product
import json


def arm(c,b,m,q,n,contacts):
    capital=4*c+contacts*b+q; allowance=4*c+6*b+q
    reserve=Q(0); source=Q(0); heat=Q(0); maintenance=Q(0); repair=Q(0)
    post_work=Q(0);post_maintenance=Q(0); virgin=1;live=4;scrap=0;failure=None
    def harvest(resistance,units,phase,index):
        nonlocal reserve,source,heat,maintenance,post_work,post_maintenance,failure
        current=Q(6-3,2+resistance)
        work=3*current; draw=6*current; loss=current**2*(2+resistance)
        assert draw==work+loss
        reserve+=work;source+=draw;heat+=loss
        if phase!='pre':post_work+=work
        cost=units*m
        if reserve<cost:
            failure=f'maintenance-{phase}-{index}';return False
        reserve-=cost;maintenance+=cost
        if phase!='pre':post_maintenance+=cost
        return True
    for index in range(1,n+1):
        if not harvest(1,4,'pre',index):break
    if failure is None:
        live-=1;scrap+=1
        if harvest(2,3,'damaged',1):
            price=c+2*b
            if reserve<price:failure='patch-unfundable'
            else:
                reserve-=price;repair=Q(price);virgin-=1;live+=1
                for index in range(1,3):
                    if not harvest(1,4,'post',index):break
    assert live+virgin+scrap==5
    returned=allowance-capital
    assert allowance+source==returned+capital+heat+maintenance+repair+reserve
    return dict(fundable=failure is None,failure=failure,capital=capital,startup_provided=allowance,
        startup_returned=returned,source_capacity=6*(n+3),source_used=str(source),source_remaining=str(6*(n+3)-source),
        resistive_heat=str(heat),maintenance=str(maintenance),repair=str(repair),reserve=str(reserve),
        whole_net=str(reserve-capital) if failure is None else None,
        post_net=str(post_work-post_maintenance-repair) if failure is None else None,
        live_material=live,virgin_material=virgin,scrap_material=scrap)


def panel():
    return [dict(c=c,b=b,m=m,q=q,n=n,damage=damage,
        segmented=arm(c,b,m,q,n,6),continuous=arm(c,b,m,q,n,4))
        for c,b,m,q,n,damage in product((1,2,4),(0,1,2),(0,1,2),(0,4,8),(2,4,8),range(4))]


if __name__=='__main__':print(json.dumps(panel(),sort_keys=True))
