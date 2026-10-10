"""Prepared protection bounds only; no world, formation or repair dynamics."""
from fractions import Fraction as Q
from itertools import product


def ledger(w, a, p, q, arm):
    if min(w, a, p, q) <= 0:
        raise ValueError('Positive registered prices required')
    armor = {'shared': 16, 'independent': 0, 'compact': 0,
             'individual': 72, 'shuffle': 16}[arm]
    armor_hits = Q(8, 15) if arm == 'shuffle' else Q(int(armor > 0))
    lost_armor = 72 * armor_hits
    lost_workers = 74 - lost_armor
    initial = 9 * w + armor * a
    upkeep = 9 * p + armor * q
    repair = lost_workers * (w + Q(1, 4)) + lost_armor * (a + Q(1, 4))
    whole = 1296 - initial - 72 * upkeep - repair
    values = dict(input=2592, gross=1296, conversion_heat=1296,
                  construction=initial, maintenance=72*upkeep, repair=repair,
                  total_heat=1296+initial+72*upkeep+repair, whole=whole,
                  post_gross=864, post_maintenance=48*upkeep,
                  post=864-48*upkeep-repair,
                  first_repair_bank=432-initial-24*upkeep-repair/2,
                  lost_workers=lost_workers, lost_armor=lost_armor)
    assert values['input'] == values['whole'] + values['total_heat']
    return {k: str(v) for k, v in values.items()} | dict(
        live=9+armor, scrap=74, raw=109-armor,
        ensemble_moments=(arm == 'shuffle'))


def panel():
    return [dict(w=str(w), a=str(a), p=str(p), q=str(q),
                 arms={name: ledger(w,a,p,q,name) for name in
                       ('shared','independent','compact','individual','shuffle')})
            for w,a,p,q in product(map(Q,(2,4)),(Q(1,4),Q(1)),
                                  (Q(1,32),Q(1,8)),(Q(1,64),Q(1,16)))]


def decision(rows):
    opportunities={name: 0 for name in rows[0]['arms']}
    wins=[]
    for index,row in enumerate(rows):
        for name,v in row['arms'].items():
            opportunities[name] += int(Q(v['whole'])>0 and Q(v['post'])>0
                                       and Q(v['first_repair_bank'])>=0)
        v=row['arms']['shared']
        wins.append(all(Q(v[key])>Q(other[key]) for name,other in row['arms'].items()
                        if name!='shared' for key in ('whole','post')))
    admitted=all(wins) and all(v==len(rows) for v in opportunities.values())
    return dict(cases=len(rows),ledgers=5*len(rows),
                positive_funded_bound_by_arm=opportunities,
                shared_strict_advantage_cases=sum(wins),
                failed_comparison_case_indices=[i for i,x in enumerate(wins) if not x],
                registered_gate_pass=admitted, natural_worlds=0,
                autonomous_self_maintenance=False,
                decision='Proceed to complete-law design only' if admitted else
                         'STOP registered all-cost-case shelter gate; no worlds',
                scope='Conditional prepared upper bounds; full-shuffle expectation is not a sampled trajectory')
