"""Independent branch equations and closed-form failure/funding interpreter."""
from fractions import Fraction as F
from itertools import product
import json


def certificate(c,b,m,q,n,contact_count):
    # Two length-two paths in parallel; after one unit loss only one remains.
    intact=1/(1/F(2)+1/F(2));broken=F(2)
    currents=[F(3)/(F(2)+resistance) for resistance in (intact,broken)]
    output=[F(3)*i for i in currents]
    source=[F(6)*i for i in currents]
    waste=[s-w for s,w in zip(source,output)]
    cost=4*c+contact_count*b+q;budget=4*c+6*b+q
    if m:
        # The very first upkeep charge is4 or8, while first harvested work is3.
        reserve=output[0];used=source[0];loss=waste[0];upkeep=patch=F(0)
        whole=post=None;failed='maintenance-pre-1';live,virgin,scrap=4,1,0
    else:
        patch=F(c+2*b)
        assert n*output[0]+output[1]>=patch
        used=(n+2)*source[0]+source[1];loss=(n+2)*waste[0]+waste[1]
        upkeep=F(0);reserve=(n+2)*output[0]+output[1]-patch
        whole=str(reserve-cost);post=str(2*output[0]+output[1]-patch)
        failed=None;live,virgin,scrap=4,0,1
    assert budget+used==(budget-cost)+cost+loss+upkeep+patch+reserve
    return dict(fundable=failed is None,failure=failed,capital=cost,startup_provided=budget,startup_returned=budget-cost,
        source_capacity=6*(n+3),source_used=str(used),source_remaining=str(6*(n+3)-used),resistive_heat=str(loss),
        maintenance=str(upkeep),repair=str(patch),reserve=str(reserve),whole_net=whole,post_net=post,
        live_material=live,virgin_material=virgin,scrap_material=scrap)


def panel():
    results=[]
    for values in product((1,2,4),(0,1,2),(0,1,2),(0,4,8),(2,4,8),range(4)):
        c,b,m,q,n,damage=values
        row=dict(c=c,b=b,m=m,q=q,n=n,damage=damage,
                 segmented=certificate(c,b,m,q,n,6),continuous=certificate(c,b,m,q,n,4))
        if row['segmented']['fundable']:
            assert F(row['segmented']['whole_net'])-F(row['continuous']['whole_net'])==-2*b
            assert row['segmented']['post_net']==row['continuous']['post_net']
        results.append(row)
    return results


if __name__=='__main__':print(json.dumps(panel(),sort_keys=True))
