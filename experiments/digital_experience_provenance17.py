"""Read-only measurement of genuine outcome identities; no VM/organism changes."""
import json
from experiments.digital_contingency15_audit import audit as validate_history

def two_distinct_own_outcomes(samples):
    try:
        assert type(samples) is list
        seen={}
        for sample in samples:
            actor,tick,value=sample['actor'],sample['tick'],sample['value']
            assert all(type(x) is int for x in (actor,tick,value))
            assert actor>=0 and tick>0 and value in (0,1)
            source=sample['source']
            if source is None:
                assert value==0
                continue  # Initial supplied zero is not personal experience.
            assert type(source) is dict
            assert all(type(source[k]) is int for k in ('actor','tick','packet','outcome'))
            assert source['actor']==actor and 0<source['tick']<tick
            assert 0<=source['packet']<64 and source['outcome']==value
            seen.setdefault(actor,set()).add((actor,source['tick']))
        return any(len(ids)>=2 for ids in seen.values())
    except (AssertionError,KeyError,TypeError):
        return False

def measure(row):
    metrics=validate_history(row)
    latest={};samples=[]
    for event in row['final']['events']:
        actor=event['actor']
        if 'attempt' in event:
            attempt=event['attempt']
            latest[actor]=dict(actor=actor,tick=event['tick'],packet=attempt['packet'],
                               outcome=attempt['success'])
        if event['decoded'][0]==1:
            source=latest.get(actor)
            value=0 if source is None else source['outcome']
            if 'after' in event:
                assert event['after']['registers'][event['decoded'][1]%2]==value
            assert source is None and value==0 or source is not None and source['outcome']==value
            samples.append(dict(actor=actor,tick=event['tick'],value=value,
                                source=None if source is None else dict(source)))
    unique={(s['actor'],s['source']['tick']) for s in samples if s['source'] is not None}
    return dict(contract='DIGITAL-EXPERIENCE-PROVENANCE-17-v1',verified=True,
                history_hash=row['hash'],seed=row['seed'],route=row['route'],
                feedback_reads=len(samples),distinct_sampled_attempts=len(unique),
                initial_zero_reads=sum(s['source'] is None for s in samples),
                repeat_reads=sum(s['source'] is not None for s in samples)-len(unique),
                samples=samples,two_distinct_own_outcomes=two_distinct_own_outcomes(samples),
                replayed_ticks=metrics['ticks'],new_world_histories=0,
                learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as stream:
        print(json.dumps(measure(json.load(stream)[0]),sort_keys=True))
