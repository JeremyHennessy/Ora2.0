"""Separate scalar withdrawal and ownership-ledger accounting interpreter."""
from fractions import Fraction as F
from itertools import product


def evaluate(p,d,m,b,a):
    sites=[int(a[-1])] if a.startswith('single') else [0,1]
    shared=a=='connected';extra=a in ('connected','loop')
    N=len(sites)*2+4+extra;C=F(N,4)+F(3,2)*len(sites)+2+(b if extra else 0)
    A=F(9,4)+5+b
    capacity=[F(2)] if shared else ([F(1),F(1)] if len(sites)==2 else [F(2*(i in sites)) for i in range(2)])
    contents=[{0:F(0),1:F(0),2:F(0)} for _ in capacity]
    active={s:True for s in sites};stock=10-N;discard=0;replacement=None
    drawn=thermal=service=construction=delivered=late=renewed=renewed_in=F(0)
    damage_bank=None;failed=None;debt=F(0)
    def balance():return sum(sum(x.values()) for x in contents)
    def debit(value):
        available=balance();parts={i:F(0) for i in range(3)}
        if available:
            ratio=value/available
            for cell in contents:
                for i in cell:
                    take=cell[i]*ratio;parts[i]+=take;cell[i]-=take
        return parts
    tape=[(0,1)]+[(p//(2**(i%4))%2,) for i in range(16)]
    for t,ports in enumerate(tape):
        if t==8:
            damage_bank=balance()
            contents=[{0:sum(cell.values()),1:F(0),2:F(0)} for cell in contents]
            if d in active:active[d]=False;discard=1
        for s in ports:
            if not active.get(s,False):continue
            drawn+=4
            destination=0 if shared else s
            room=capacity[destination]-sum(contents[destination].values())
            net=min(room,F(2));thermal+=4-net
            category=2 if replacement is not None and s==d else int(t>=8)
            contents[destination][category]+=net
            if category==2:renewed_in+=net
        missing=int(d in active and not active[d]);due=(N-missing)*m
        if balance()<due:
            have=balance();debt=due-have;service+=have;debit(have);failed='upkeep';break
        service+=due;debit(due)
        if t>=8 and missing and stock>0 and balance()>=F(3,4):
            construction+=F(3,4);debit(F(3,4));stock-=1;active[d]=True;replacement=t
        transfer=max(F(0),min(F(1,2),balance()-1));origins=debit(transfer)
        delivered+=transfer;renewed+=origins[2]
        if t>=8:late+=transfer
    remaining=balance();live=N-int(d in active and not active[d])
    assert stock+discard+live==10
    assert drawn==thermal+service+construction+delivered+remaining
    assert 0<=drawn<=72
    return dict(fundable=failed is None,failure=failed,capital=str(C),allowance=str(A),returned=str(A-C),
        source=str(drawn),source_remaining=str(72-drawn),conversion_overflow_heat=str(thermal),upkeep=str(service),repair=str(construction),
        output=str(delivered),bank=str(remaining),bank_at_damage=None if damage_bank is None else str(damage_bank),post_output=str(late),
        whole=str(delivered+remaining-C),post=None if damage_bank is None else str(late+remaining-damage_bank),
        fresh_capture=str(renewed_in),fresh_output=str(renewed),repair_tick=replacement,raw=stock,live=live,scrap=discard,
        contacts=sorted(s for s in active if active[s]),rebuilt_contact=d if replacement is not None else None,unpaid_upkeep=str(debt),
        provenance=[[str(cell[i]) for i in range(3)] for cell in contents],whole_upper=str(F(21,2)-C),cutoff_upper_reject=m>=F(1,8))


def panel():
    answer=[]
    for p,d,m,b in product(range(16),range(2),(F(1,32),F(1,8)),(F(1,2),F(1))):
        answer.append(dict(pattern=p,damage=d,m=str(m),bus=str(b),arms={a:evaluate(p,d,m,b,a) for a in ('connected','balanced','single0','single1','loop')}))
    return answer
