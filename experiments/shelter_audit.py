"""Independent cell-count and window accounting, never imports producer."""
from fractions import Fraction as F


def panel():
    distinct=sum(int((x,y)!=(0,y)) + int((x,y)!=(4,y)) +
                 int((x,y)!=(x,0)) + int((x,y)!=(x,4))
                 for x in range(5) for y in range(5))
    shuffle=F(distinct,100)*F(16,24)
    assert shuffle==F(8,15)
    result=[]
    for wc in (F(2),F(4)):
        for ac in (F(1,4),F(1)):
            for wm in (F(1,32),F(1,8)):
                for am in (F(1,64),F(1,16)):
                    arms={}
                    for name,protectors,hit in [('shared',16,F(1)),('independent',0,F(0)),
                            ('compact',0,F(0)),('individual',72,F(1)),('shuffle',16,shuffle)]:
                        assembly=wc*9+ac*protectors
                        service=24*(wm*9+am*protectors)
                        armor_destroyed=36*hit
                        worker_destroyed=37-armor_destroyed
                        recovery=armor_destroyed*ac+worker_destroyed*wc+F(37,4)
                        first=432-assembly-service
                        second=432-service-recovery
                        third=second
                        whole=first+second+third
                        values=dict(input=2592,gross=1296,conversion_heat=1296,
                            construction=assembly,maintenance=3*service,repair=2*recovery,
                            total_heat=2592-whole,whole=whole,post_gross=864,
                            post_maintenance=2*service,post=second+third,
                            first_repair_bank=first-recovery,
                            lost_workers=2*worker_destroyed,lost_armor=2*armor_destroyed)
                        assert whole==1296-assembly-3*service-2*recovery
                        assert values['total_heat']==1296+assembly+3*service+2*recovery
                        arms[name]={k:str(v) for k,v in values.items()}|dict(
                            live=9+protectors,scrap=74,raw=192-9-protectors-74,
                            ensemble_moments=(name=='shuffle'))
                        assert sum(arms[name][k] for k in ('live','scrap','raw'))==192
                    result.append(dict(w=str(wc),a=str(ac),p=str(wm),q=str(am),arms=arms))
    return result


def audit(rows):
    if rows!=panel():
        raise ValueError('Independent geometry/accounting mismatch')
    deltas=[]
    for row in rows:
        shared=row['arms']['shared'];bare=row['arms']['compact']
        w,a,p,q=(F(row[k]) for k in ('w','a','p','q'))
        whole=72*(w-a)-16*a-1152*q
        post=72*(w-a)-768*q
        assert F(shared['whole'])-F(bare['whole'])==whole
        assert F(shared['post'])-F(bare['post'])==post
        deltas.append((whole,post))
    return dict(verified=True,cases=len(rows),ledgers=80,
                exact_shuffle_armor_hit_probability='8/15',
                compact_comparison_nonpositive_whole=sum(x[0]<=0 for x in deltas),
                minimum_whole_advantage=str(min(x[0] for x in deltas)),
                minimum_post_advantage=str(min(x[1] for x in deltas)),
                scope='Bounds and ensemble expectations, not material identities or observed recovery')
