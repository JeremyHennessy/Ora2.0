"""Independent event interpretation; no producer or target-genome import."""
import json,sys
from experiments.digital_inheritance_audit import audit_world

ANCESTOR=[1,2,4,5,6,12]
MOBILE=[1,2,4,5,6,3]

def metrics(row):
    out=audit_world(row)
    births={e['birth']['child']['id']:e for e in row['events'] if 'birth' in e}
    remote={}
    for e in row['events']:
        if e.get('food',-1)>=16:remote[e['actor']]=remote.get(e['actor'],0)+1
    witnesses=[]
    for identity,event in births.items():
        program=[g[0] for g in event['birth']['child']['code']]
        children=[child for child,e in births.items() if e['actor']==identity and remote.get(child,0)>=1]
        if program!=row['genesis_program'] and remote.get(identity,0)>=4 and children:
            witnesses.append(dict(id=identity,parent=event['actor'],birth_tick=event['tick'],
                                  program=program,remote_food=remote[identity],
                                  useful_children=children,write_events=event['birth']['write_events']))
    out.update(label=row['label'],witnesses=witnesses,qualifying_lineages=len(witnesses),
               descendant_remote_food=sum(n for i,n in remote.items() if i!=0))
    return out

def evaluate(rows,phase):
    assert phase in ('primary','replication')
    seeds=range(24600,24664) if phase=='primary' else range(24664,24728)
    expected=[(s,label,m,p) for s in seeds for label,m,p in
              (('population','mutating',ANCESTOR),('population','faithful',ANCESTOR),
               ('population','copy_disabled',ANCESTOR),('fixed_mobile','faithful',MOBILE))]
    result=[]
    for i,row in enumerate(rows):
        assert i<len(expected) and (row['seed'],row['label'],row['mode'],row['genesis_program'])==expected[i]
        x=metrics(row);assert not row['final']['entities'] and x['ticks']<=1536
        result.append(x)
    assert len(result)==256
    mut=result[0::4];fixed=result[3::4];null=result[1::4]+result[2::4]
    assert all(x['births']==0 for x in result[2::4])
    ready=all(x['remote_food']>=4 and x['descendant_births']>=1 and x['descendant_remote_food']>=4 for x in fixed)
    count=sum(x['qualifying_lineages']>0 for x in mut)
    gate=ready and count>=2 and not any(x['qualifying_lineages'] for x in null)
    advantage=sum(c['remote_food']>b['remote_food'] and c['births']>=b['births'] for c,b in zip(mut,fixed))
    return dict(verified=True,phase=phase,worlds=256,rows=result,comparator_ready=ready,
                qualifying_mutation_worlds=count,gate=gate,ordinary_advantage_worlds=advantage,
                classification=('ENDOGENOUS_INHERITANCE_OCCURRENCE_GATE_PASSED' if gate else
                                'OCCURRENCE_GATE_FAILED' if ready else 'COMPARATOR_NOT_READY'),
                sustained_evolution=False,learning=False,repair=False)

def read_batches(manifest):
    names=json.load(open(manifest,encoding='utf-8'));assert len(names)<=64
    for name in names:
        rows=json.load(open(name,encoding='utf-8'));assert len(rows)<=4
        yield from rows

if __name__=='__main__':print(json.dumps(evaluate(read_batches(sys.argv[2]),sys.argv[1]),sort_keys=True))
