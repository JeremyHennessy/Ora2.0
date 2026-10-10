"""Frozen finite-capacity accounting; installed apparatus, no natural worlds."""
from fractions import Fraction as Q
from itertools import product

ARMS=('connected','balanced','single0','single1','loop')

def ratio(value):
    size=max(value.numerator.bit_length(),value.denominator.bit_length())
    if size<=14000:return str(value)
    if size>262144:raise ValueError('Registered integer representation bound')
    return dict(numerator_hex=hex(value.numerator),denominator_hex=hex(value.denominator))


def certificate(pattern,damage,m,bus,arm):
    collectors={0,1} if arm not in ('single0','single1') else {int(arm[-1])}
    linked=arm=='connected';has_bus=arm in ('connected','loop')
    capacities=[Q(2)] if linked else ([Q(1),Q(1)] if len(collectors)==2 else [Q(2) if i in collectors else Q(0) for i in (0,1)])
    formed=2*len(collectors)+4+int(has_bus)
    capital=Q(formed,4)+Q(3,2)*len(collectors)+2+(bus if has_bus else 0)
    allowance=Q(9,4)+3+2+bus
    banks=[[Q(0),Q(0),Q(0)] for _ in capacities]
    contacts=set(collectors);raw=10-formed;scrap=0;rebuilt=False;repair_tick=None
    used=heat=upkeep=repair=output=post_output=fresh_output=Q(0)
    before_damage=None;failure=None;fresh_capture=Q(0);unpaid=Q(0)
    def energy():return sum(sum(bank) for bank in banks)
    def withdraw(amount):
        total=energy();assert 0<=amount<=total
        if not total:return [Q(0)]*3
        removed=[sum(bank[j] for bank in banks)*amount/total for j in range(3)]
        for bank in banks:
            for j in range(3):bank[j]*=(total-amount)/total
        return removed
    for tick in range(17):
        if tick==8:
            before_damage=energy()
            for bank in banks:bank[:]=[sum(bank),Q(0),Q(0)]
            if damage in contacts:contacts.remove(damage);scrap=1
        offered=(0,1) if tick==0 else (((pattern>>((tick-1)%4))&1),)
        for source in offered:
            if source not in contacts:continue
            used+=4;heat+=2
            index=0 if linked else source
            accepted=min(Q(2),capacities[index]-sum(banks[index]))
            tag=2 if rebuilt and source==damage else (1 if tick>=8 else 0)
            banks[index][tag]+=accepted;heat+=2-accepted
            if tag==2:fresh_capture+=accepted
        live=formed-int(damage in collectors and damage not in contacts)
        charge=live*m
        if energy()<charge:
            unpaid=charge-energy();upkeep+=energy();withdraw(energy());failure='upkeep';break
        withdraw(charge);upkeep+=charge
        if tick>=8 and damage in collectors and damage not in contacts and raw and energy()>=Q(3,4):
            withdraw(Q(3,4));repair+=Q(3,4);raw-=1;contacts.add(damage);rebuilt=True;repair_tick=tick
        delivered=min(Q(1,2),max(Q(0),energy()-1))
        removed=withdraw(delivered);output+=delivered;fresh_output+=removed[2]
        if tick>=8:post_output+=delivered
    live=formed-int(damage in collectors and damage not in contacts)
    assert raw+live+scrap==10
    assert allowance+used==allowance-capital+capital+heat+upkeep+repair+output+energy()
    assert used<=72 and all(0<=sum(bank)<=cap for bank,cap in zip(banks,capacities))
    return dict(fundable=failure is None,failure=failure,capital=ratio(capital),allowance=ratio(allowance),returned=ratio(allowance-capital),
        source=ratio(used),source_remaining=ratio(72-used),conversion_overflow_heat=ratio(heat),upkeep=ratio(upkeep),repair=ratio(repair),
        output=ratio(output),bank=ratio(energy()),bank_at_damage=None if before_damage is None else ratio(before_damage),post_output=ratio(post_output),
        whole=ratio(output+energy()-capital),post=None if before_damage is None else ratio(post_output+energy()-before_damage),
        fresh_capture=ratio(fresh_capture),fresh_output=ratio(fresh_output),repair_tick=repair_tick,raw=raw,live=live,scrap=scrap,
        contacts=sorted(contacts),rebuilt_contact=damage if rebuilt else None,unpaid_upkeep=ratio(unpaid),
        provenance=[[ratio(x) for x in bank] for bank in banks],whole_upper=ratio(Q(17,2)+2-capital),
        cutoff_upper_reject=m>=Q(1,8))


def panel():
    return [dict(pattern=p,damage=d,m=str(m),bus=str(b),arms={a:certificate(p,d,m,b,a) for a in ARMS})
            for p,d,m,b in product(range(16),range(2),(Q(1,32),Q(1,8)),(Q(1,2),Q(1)))]


def decision(rows):
    number=lambda v: Q(int(v['numerator_hex'],16),int(v['denominator_hex'],16)) if isinstance(v,dict) else Q(v)
    complete=qualifying=positive=restored=0;failures={a:0 for a in ARMS};upper=0
    for row in rows:
        arms=row['arms'];c=arms['connected'];upper+=int(c['cutoff_upper_reject'])
        for a in ARMS:failures[a]+=int(not arms[a]['fundable'])
        positive+=int(c['fundable'] and number(c['whole'])>0 and c['post'] is not None and number(c['post'])>0)
        restored+=int(number(c['fresh_output'])>0)
        if not all(a['fundable'] for a in arms.values()):continue
        complete+=1
        controls=[arms[a] for a in ARMS if a!='connected']
        qualifying+=int(number(c['whole'])>0 and number(c['post'])>0 and number(c['fresh_output'])>0
            and all(number(c['whole'])>number(a['whole']) and number(c['post'])>number(a['post']) for a in controls))
    return dict(cases=len(rows),arm_ledgers=len(rows)*5,complete_cases=complete,qualifying_cases=qualifying,
        positive_candidate_cases=positive,fresh_rebuilt_output_cases=restored,failed_by_arm=failures,
        early_cutoff_upper_rejections=upper,natural_worlds=0,natural_admission=False,
        decision='CONDITIONAL PREPARED FEASIBILITY ONLY' if qualifying else 'REJECT UNDER FROZEN LAW',
        limitations='Installed collectors, stores, cutoff, load and constructor; natural primitive/formation costs and rates remain uncalibrated')
