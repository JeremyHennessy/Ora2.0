"""Separate enumerative algebra check. Imports neither producer nor VM."""
import hashlib
import json
from pathlib import Path


def certificate():
    truth=[]
    for port in (0,1):
        for target in (0,1):
            outcome=int(port==target)
            possibilities=[x for x in (0,1) if int(port==x)==outcome]
            assert possibilities==[target]
            truth.append([port,outcome,possibilities[0]])
    # A zero feedback value has both an empty and a real-failure explanation.
    explanations=('initial','empty','real_failure')
    assert len(explanations)>1
    widths=[len([None for _ in range(3*n)]+[None for _ in range(16)]) for n in range(1,33)]
    assert all(128-c-16>=0 for c in widths)
    count=0
    for c in widths:
        for t in range(64,513):
            last_time=t-1
            last_work=c+t-55-1
            last=last_time if last_time<last_work else last_work
            for x in (0,last-1,last,last+1,512):
                failures=(x>=t,55+x>=c+t)
                assert (not any(failures))==(x<=last)
                count+=1
    energy_cases=0
    for start in range(1,65):
        for distance in range(1,66):
            # Before the last step no gain is allowed: inspect prefix balances.
            dead=any(start-paid<=0 for paid in range(1,distance))
            end=None if dead else start-distance+20
            if end is not None and end>64:end=64
            expected=None if distance>start else min(64,start-distance+20)
            assert end==expected
            energy_cases+=1
    states=13*2
    for _ in range(10):states*=16
    slots=list(range(64,64+16))
    assert len(set(slots))==16 and slots[-1]==79
    return dict(contract='DIGITAL-INFORMATION-41-v1',
        classification='abstract_necessary_bounds_only',
        real_attempt_truth_table=truth,formation_sizes=len(widths),
        energy_gap_cases=energy_cases,strict_comparison_cases=count,
        fixed_genotype_state_ceiling=states,earliest_fresh_completion=max(slots),
        minimum_thirteen_triple_work=widths[12]+max(slots),
        reachable_capacity_verified=False,viability_verified=False,
        predictive_gain_verified=False,probability_model_verified=False,
        world_histories=0,organism_actions=0,seeds_queried=[],
        candidate_policies_created=0,learning=False,stage_credit=False)


if __name__=='__main__':
    import sys
    pins=json.loads(Path(sys.argv[1]).read_bytes())['source_sha256']
    for name,expected in pins.items():
        p=Path(name)
        assert not p.is_absolute() and '..' not in p.parts and p.parts[0]=='experiments' and p.suffix=='.py'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
    result=certificate();result['reviewed_source_sha256']=pins
    print(json.dumps(result,sort_keys=True,separators=(',',':')))
