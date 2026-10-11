"""Independent exhaustive reserve-allocation interpreter; no producer import."""
from fractions import Fraction
import itertools
import json
from pathlib import Path
import sys


def allocations(stock):
    for a in range(stock+1):
        for b in range(stock-a+1):
            for c in range(stock-a-b+1):
                for d in range(stock-a-b-c+1):
                    yield (a,b,c,d)


def audit(payload):
    required={'schema','cases','common_cost','extra_apparatus_cost',
              'mechanism_admitted','natural_worlds'}
    if (set(payload) != required or payload['schema'] != 'repair-pool01-v1'
            or payload['common_cost'] != 'UNKNOWN'
            or payload['extra_apparatus_cost'] != 'UNKNOWN'
            or payload['mechanism_admitted'] is not False
            or type(payload['natural_worlds']) is not int
            or payload['natural_worlds'] != 0):
        raise ValueError('Prepared bound cannot admit a mechanism')
    rows=payload['cases']
    if len(rows) != 1728:
        raise ValueError('Complete census required')
    best={}; enumerated=0
    for s,r in itertools.product(range(1,13), repeat=2):
        coverage=0
        for allocation in allocations(s):
            coverage=max(coverage, sum(x >= r for x in allocation))
            enumerated+=1
        best[s,r]=coverage
    funded_positive=funded_nonpositive=unfunded=fully_covered=0
    for row,values in zip(rows,itertools.product(
            range(1,13),range(1,13),range(1,5),range(1,4))):
        s,r,g,t=values; n=best[s,r]; q=Fraction(n,4)
        independent=Fraction(s)+sum(Fraction(g,4) for _ in range(n))
        pool=s-(r+t)+(r+g)
        frontier=Fraction(pool)-independent
        witness=row['allocation']
        if (len(witness)!=4 or any(type(x) is not int or x<0 for x in witness)
                or sum(witness)>s or sum(x>=r for x in witness)!=n):
            raise ValueError('Attainable optimal local reserve witness required')
        expected=dict(stock=s,repair=r,gain=g,transfer=t,covered_losses=n,
                      allocation=witness,
                      independent_output=[independent.numerator,independent.denominator],
                      pool_output_before_extra_cost=pool,
                      extra_cost_frontier=[frontier.numerator,frontier.denominator],
                      pool_funded=s-r>=t,positive_frontier=frontier>0)
        if json.dumps(row,sort_keys=True)!=json.dumps(expected,sort_keys=True):
            raise ValueError('Case differs from exhaustive independent allocation')
        if not expected['pool_funded']:unfunded+=1
        elif frontier>0:funded_positive+=1
        else:funded_nonpositive+=1
        fully_covered+=int(n==4)
    return dict(cases=len(rows),allocations_examined=enumerated,
                funded_positive_frontier=funded_positive,
                funded_nonpositive_frontier=funded_nonpositive,
                unfunded_pool=unfunded,fully_covered_control_cases=fully_covered,
                common_cost='UNKNOWN',extra_apparatus_cost='UNKNOWN',
                mechanism_admitted=False,natural_worlds=0)


if __name__=='__main__':
    print(json.dumps(audit(json.loads(Path(sys.argv[1]).read_bytes())),sort_keys=True))
