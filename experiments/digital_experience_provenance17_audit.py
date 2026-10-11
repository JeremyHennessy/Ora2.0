"""Independent historical read-to-outcome reconstruction; no measurement import."""
import json
from experiments.digital_contingency15_audit import audit as interpret

def audit(row,receipt):
    history=interpret(row)
    events=row['final']['events'];samples=[]
    for read in [e for e in events if e['decoded'][0]==1]:
        prior=[e for e in events if e['tick']<read['tick'] and
               e['actor']==read['actor'] and 'attempt' in e]
        last=prior[-1] if prior else None
        source=None if last is None else dict(actor=last['actor'],tick=last['tick'],
                    packet=last['attempt']['packet'],outcome=last['attempt']['success'])
        value=0 if source is None else source['outcome']
        if 'after' in read:
            assert read['after']['registers'][read['decoded'][1]%2]==value
        assert value==(0 if source is None else source['outcome'])
        samples.append(dict(actor=read['actor'],tick=read['tick'],value=value,source=source))
    ids={(s['actor'],s['source']['tick']) for s in samples if s['source'] is not None}
    ready=any(len({t for actor,t in ids if actor==s['actor']})>=2 for s in samples)
    expected=dict(contract='DIGITAL-EXPERIENCE-PROVENANCE-17-v1',verified=True,
                  history_hash=row['hash'],seed=row['seed'],route=row['route'],
                  feedback_reads=len(samples),distinct_sampled_attempts=len(ids),
                  initial_zero_reads=sum(s['source'] is None for s in samples),
                  repeat_reads=sum(s['source'] is not None for s in samples)-len(ids),
                  samples=samples,two_distinct_own_outcomes=ready,
                  replayed_ticks=history['ticks'],new_world_histories=0,
                  learning=False,stage_credit=False)
    # Exact serialized equality also refuses bool/int identity aliases.
    assert json.dumps(receipt,sort_keys=True)==json.dumps(expected,sort_keys=True)
    return dict(verified=True,feedback_reads=len(samples),distinct_sampled_attempts=len(ids),
                repeat_reads=expected['repeat_reads'],two_distinct_own_outcomes=ready,
                learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as a,open(sys.argv[2],encoding='utf-8') as b:
        print(json.dumps(audit(json.load(a)[0],json.load(b)),sort_keys=True))
