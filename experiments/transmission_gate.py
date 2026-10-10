"""Ideal finite mechanical accounting bounds, not damage dynamics."""
from fractions import Fraction as Q
from itertools import product

ARMS={'gear':(Q(2),5),'lever':(Q(2),3),'direct':(Q(1),2),'shuffle':(Q(1,2),5)}

def ledger(t,f,m,r,arm):
    if any(x<=0 for x in (t,f,m,r)):raise ValueError('Registered positive parameters')
    ratio,units=ARMS[arm]
    work=Q(2)/ratio if ratio*t>=2 else Q(0)
    assert 0<=work<=t
    return {k:str(v) for k,v in dict(pulse_work=work,offered_potential=12*t,
        gross=12*work,unused_potential=12*(t-work),formation=units*f,
        maintenance=12*units*m,replacement=r,whole=12*work-units*f-12*units*m-r,
        post_gross=6*work,post_maintenance=6*units*m,post=6*work-6*units*m-r).items()}|dict(live=units,scrap=1,raw=9-units)

def panel():
    return [dict(t=str(t),f=str(f),m=str(m),r=str(r),arms={a:ledger(t,f,m,r,a) for a in ARMS})
        for t,f,m,r in product(map(Q,(1,2,4,8)),(Q(1,8),Q(1,2)),(Q(1,64),Q(1,16)),(Q(1,4),Q(1))) ]

def decision(rows):
    counts={a:0 for a in ARMS};advantages=0
    for row in rows:
        for a,v in row['arms'].items():counts[a]+=int(Q(v['whole'])>0 and Q(v['post'])>0)
        gear,lever=row['arms']['gear'],row['arms']['lever']
        assert Q(lever['whole'])-Q(gear['whole'])==2*Q(row['f'])+24*Q(row['m'])
        assert Q(lever['post'])-Q(gear['post'])==12*Q(row['m'])
        advantages+=int(Q(gear['whole'])>Q(lever['whole']) and Q(gear['post'])>Q(lever['post']))
    return dict(cases=len(rows),ledgers=4*len(rows),positive_bound_by_arm=counts,gear_advantages=advantages,
        decision='REJECT fixed-ratio ideal gear train: attainable equal-ratio lever bounds strictly dominate',
        natural_worlds=0,assembly_dynamics=False,autonomous_self_maintenance=False,
        scope='Necessary accounting bounds only; fabrication accessibility and rates remain unmeasured')
