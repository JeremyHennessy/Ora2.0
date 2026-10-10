"""Prospective finite portable-load reachability gate; no natural samples."""
import argparse
from collections import deque
from fractions import Fraction
import hashlib
import json
import math
from functools import lru_cache

ARMS = ('candidate', 'independent', 'shuffled', 'bulk-diagnostic')
POTENTIAL = (0, 1, 4, 3)
# Aggregate state: F count, body conformation, labelled atom position bits,
# unloaded site0/site1, loaded site0/site1. Labels supply multiplicities.
ACTIONS = [(k, 0, d) for k in ('assemble', 'drive', 'waste', 'passive', 'relax') for d in (-1, 1)] + [('load', j, d) for j in range(2) for d in (-1, 1)] + [('lhop', j, 1) for j in range(4)] + [('hop', j, 1) for j in range(2)]

def pack(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def heat(s):
    return 68 - 6*s[0] - POTENTIAL[s[1]] - 2*(s[5]+s[6])

@lru_cache(maxsize=100000)
def multiplicity(s):
    return math.comb(10, s[0])*math.factorial(10)//math.prod(math.factorial(n) for n in s[3:])

def transition(s, action, arm):
    f, q, p, *loads = s
    k, j, d = action
    t = list(s)
    prefactor = 16
    count = 1
    if k in ('assemble', 'drive', 'waste'):
        if k == 'assemble':
            if q != (0 if d == 1 else 1) or p not in (0, 3):
                return None
            t[1] = 1 if d == 1 else 0
            prefactor = {'candidate':32, 'independent':17, 'shuffled':2, 'bulk-diagnostic':32}[arm]
        if k == 'drive':
            if q != (1 if d == 1 else 2):
                return None
            t[1] = 2 if d == 1 else 1
        if k == 'waste':
            prefactor = {'candidate':2, 'independent':17, 'shuffled':32, 'bulk-diagnostic':2}[arm]
        count = f if d == 1 else 10-f
        t[0] -= d
    elif k in ('passive', 'relax'):
        lo, hi = (0, 1) if k == 'passive' else (2, 3)
        if q != (lo if d == 1 else hi) or k == 'passive' and p not in (0, 3):
            return None
        t[1] = hi if d == 1 else lo
    elif k == 'load':
        if q != (3 if d == 1 else 1) or arm != 'bulk-diagnostic' and j != p//3:
            return None
        origin, target = (j, j+2) if d == 1 else (j+2, j)
        count = loads[origin]
        t[3+origin] -= 1
        t[3+target] += 1
        t[1] = 1 if d == 1 else 3
    elif k == 'lhop':
        count = loads[j]
        t[3+j] -= 1
        t[3+(j^1)] += 1
    elif k == 'hop':
        if q and j == 1:
            return None
        t[2] ^= 3 if q else 1 << j
    else:
        raise ValueError('Unknown action')
    t = tuple(t)
    if count == 0 or min(t[0], 10-t[0], *t[3:], heat(t)) < 0:
        return None
    rate = Fraction(prefactor, 64*2**max(0, heat(s)-heat(t)))
    return t, rate, count

def graph(arm):
    starts = {(10, 0, p, n, 10-n, 0, 0) for p in range(4) for n in range(11)}
    seen = set(starts)
    todo = deque(sorted(starts))
    edges = labelled = 0
    while todo:
        s = todo.popleft()
        for action in ACTIONS:
            r = transition(s, action, arm)
            if r is None:
                continue
            t, rate, count = r
            k, j, d = action
            inverse = (k, j^1 if k == 'lhop' else j, 1 if k in ('lhop', 'hop') else -d)
            back = transition(t, inverse, arm)
            assert back is not None and back[0] == s
            assert multiplicity(s)*2**heat(s)*rate*count == multiplicity(t)*2**heat(t)*back[1]*back[2]
            edges += 1
            labelled += count
            if t not in seen:
                seen.add(t)
                todo.append(t)
            if len(seen)>100000 or edges>2000000:
                raise ValueError('Prospective graph bound')
    return dict(arm=arm, states=len(seen), directed_channels=edges, labelled_proposals=labelled,
                state_sha256=hashlib.sha256(pack(sorted(seen))).hexdigest(),
                maximum_stored_work_with_heat_protected=max(2*(s[5]+s[6]) for s in seen if heat(s)>=8),
                complete_reverse_and_balance_checks=True)

def certificate(arm):
    # Authored opportunity proof, never a natural trajectory or screened seed.
    actions = [('assemble',0,1)]
    for token, load in zip((1,2,3),(0,1,2)):
        actions += [('drive',token,1),('relax',0,1),('load',load,1)]
        if load:
            actions += [('lhop',load,1)]
    actions += [('damage',0,1),('assemble',4,1)]
    for token, load in zip(range(5,10),range(3,8)):
        actions += [('drive',token,1),('relax',0,1),('load',load,1),('lhop',load,1)]
    tokens = [0]*10
    virgin = [True]*10
    sites = [0]*10
    loaded = [False]*10
    q = p = 0
    charge = None
    rows = []
    fresh = cost = postfresh = postcost = 0
    damaged = False
    beforework = beforeheat = None
    def state():
        counts = [sum(site == j%2 and flag == (j>=2) for site, flag in zip(sites,loaded)) for j in range(4)]
        return (tokens.count(0),q,p,*counts)
    for action in actions:
        s = state()
        k,j,d = action
        if k == 'damage':
            assert q and p == 0 and loaded[0] and sites[0] == 0
            beforework = 2*sum(loaded)
            beforeheat = heat(s)
            loaded[0] = False
            q = 0
            charge = None
            damaged = True
            cost += 2
            postcost += 2
        else:
            a = (k, sites[j] if k=='load' else sites[j]+2*int(loaded[j]) if k=='lhop' else 0, d)
            t, rate, count = transition(s, a, arm)
            q, p = t[1:3]
            if k in ('assemble','drive','waste'):
                assert tokens[j] == int(d == -1)
                if k == 'drive':
                    charge = bool(virgin[j]) if d == 1 else None
                tokens[j] = int(d == 1)
                virgin[j] = False
            if k == 'load':
                assert loaded[j] == (d == -1)
                loaded[j] = d == 1
                credit = 2*d if d == -1 or charge else 0
                fresh += credit
                postfresh += credit*int(damaged)
                charge = None if d == 1 else False
            if k == 'lhop':
                sites[j] ^= 1
            bill = 6*d if k == 'assemble' else d if k == 'passive' else 0
            cost += bill
            postcost += bill*int(damaged)
            assert state() == t
        rows.append(dict(action=list(action),before=list(s),after=list(state()),heat=heat(state())))
    final = state()
    store = 2*sum(loaded)
    score = dict(whole_stored_work=store, post_store_gain=store-beforework, fresh_gross_work=fresh,
                 formation_damage_bill=cost, linked_surplus=fresh-cost,
                 post_fresh_work=postfresh, post_bill=postcost, post_linked_surplus=postfresh-postcost,
                 final_heat=heat(final), predamage_heat=beforeheat,
                 endpoint=bool(store>0 and store-beforework>0 and fresh-cost>0 and postfresh-postcost>0 and heat(final)>=max(8,beforeheat) and q==1))
    return dict(arm=arm,controlled_only=True,rows=rows,score=score,load_sites=sites,loaded=loaded,
                tokens=tokens,virgin=virgin,resource_yoked_repair_state=next(row['after'] for row in rows if row['action'][0]=='damage'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--revision',required=True)
    args=parser.parse_args()
    print(json.dumps(dict(schema='export01-admission',source_revision=args.revision,natural_worlds=0,
                          graphs=[graph(arm) for arm in ARMS],certificates=[certificate(arm) for arm in ARMS]),sort_keys=True))

if __name__=='__main__':
    main()
