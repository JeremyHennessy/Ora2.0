"""Separate rational mechanical balance enumeration, no producer imported."""
from fractions import Fraction as F

def panel():
    result=[]
    for torque in [F(1),F(2),F(4),F(8)]:
        for formation in [F(1,8),F(1,2)]:
            for service in [F(1,64),F(1,16)]:
                for rebuilding in [F(1,4),F(1)]:
                    arms={}
                    for name,multiplier,count in [('gear',F(2),5),('lever',F(2),3),('direct',F(1),2),('shuffle',F(1,2),5)]:
                        travel=1/multiplier
                        delivered=2*travel if torque>=2*travel else F(0)
                        body=count*formation;maintenance=count*service*12
                        first=6*delivered-6*count*service-body
                        after=6*delivered-6*count*service-rebuilding
                        terms={'pulse_work':delivered,'offered_potential':torque*12,'gross':delivered*12,
                            'unused_potential':12*torque-12*delivered,'formation':body,'maintenance':maintenance,
                            'replacement':rebuilding,'whole':first+after,'post_gross':6*delivered,
                            'post_maintenance':count*service*6,'post':after}
                        assert terms['offered_potential']==terms['gross']+terms['unused_potential']
                        assert terms['whole']==terms['gross']-body-maintenance-rebuilding
                        arms[name]={k:str(v) for k,v in terms.items()}|dict(live=count,scrap=1,raw=9-count)
                        assert sum(arms[name][k] for k in ('live','scrap','raw'))==10
                    result.append(dict(t=str(torque),f=str(formation),m=str(service),r=str(rebuilding),arms=arms))
    return result

def audit(rows):
    assert rows==panel()
    differences=[]
    for row in rows:
        gear,lever=row['arms']['gear'],row['arms']['lever']
        whole=F(lever['whole'])-F(gear['whole']);post=F(lever['post'])-F(gear['post'])
        assert whole>0 and post>0
        differences.append((whole,post))
    return dict(verified=True,cases=len(rows),ledgers=128,lever_strictly_dominates=len(differences),
        minimum_whole_difference=str(min(x[0] for x in differences)),minimum_post_difference=str(min(x[1] for x in differences)),
        scope='Declared ideal law and positive uniform costs; not a universal gearing impossibility')
