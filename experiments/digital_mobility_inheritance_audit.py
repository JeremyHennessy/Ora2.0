"""Claim evaluator reusing the separately implemented generic VM interpreter.

No producer import. Fresh founders are researcher installed; paid births alone
are offspring evidence. A useful inherited phenotype is not sustained evolution.
"""
import json,sys
from experiments.digital_inheritance_audit import audit_world

PROGRAMS=(('candidate',[1,2,4,3,6,12]),('ancestor',[1,2,4,5,6,12]),('fixed_mobile',[1,2,4,5,6,3]))

def metrics(row):
    result=audit_world(row)
    result.update(label=row['label'],descendant_food=sum('food' in e and e['actor']!=0 for e in row['events']),
                  descendant_remote_food=sum(e.get('food',-1)>=16 and e['actor']!=0 for e in row['events']))
    return result

def origin_certificate(rows):
    found={}
    for row in rows:
        if row['seed'] not in (24114,24156) or row['mode']!='mutating':continue
        assert row['genesis_program']==[1,2,4,5,6,12] and row['label']=='generation'
        audit_world(row)
        matches=[dict(seed=row['seed'],tick=e['tick'],parent=e['actor'],child=e['birth']['child']['id'],write_events=e['birth']['write_events'])
                 for e in row['events'] if 'birth' in e and [g[0] for g in e['birth']['child']['code']]==[1,2,4,3,6,12]]
        assert matches and row['seed'] not in found
        found[row['seed']]=matches
    assert set(found)=={24114,24156}
    return found

def evaluate(rows,phase):
    assert phase in ('primary','replication')
    seeds=range(24400,24408) if phase=='primary' else range(24408,24416)
    expected=[(s,label,m,p) for s in seeds for label,p in PROGRAMS for m in ('faithful','copy_disabled')]
    out=[]
    for index,row in enumerate(rows):
        assert index<48 and (row['seed'],row['label'],row['mode'],row['genesis_program'])==expected[index]
        x=metrics(row);assert not row['final']['entities'] and x['ticks']<=1536
        out.append(x)
    assert len(out)==48
    assert all(x['births']==0 for x in out if x['mode']=='copy_disabled')
    faithful={label:[x for x in out if x['label']==label and x['mode']=='faithful'] for label,_ in PROGRAMS}
    ready=all(x['remote_food']>=4 and x['descendant_births']>=1 and x['descendant_remote_food']>=4 for x in faithful['fixed_mobile'])
    passed=ready and all(c['descendant_remote_food']>=4 and c['descendant_births']>=1 and c['remote_food']>a['remote_food'] for c,a in zip(faithful['candidate'],faithful['ancestor']))
    advantage=all(c['remote_food']>b['remote_food'] and c['births']>=b['births'] for c,b in zip(faithful['candidate'],faithful['fixed_mobile']))
    return dict(verified=True,phase=phase,worlds=48,rows=out,comparator_ready=ready,gate=passed,
                classification=('PROVISIONAL_INHERITED_REMOTE_ACQUISITION' if passed else ('REPRODUCTIVE_REMOTE_INHERITANCE_GATE_FAILED' if ready else 'COMPARATOR_NOT_READY')),
                ordinary_comparator_advantage=advantage,functional_inheritance=False,evolution=False,learning=False,repair=False)

def read_batches(manifest):
    names=json.load(open(manifest,encoding='utf-8'));assert len(names)<=12
    for name in names:
        rows=json.load(open(name,encoding='utf-8'));assert len(rows)<=4
        yield from rows

if __name__=='__main__':
    if sys.argv[1]=='origins':print(json.dumps(origin_certificate(read_batches(sys.argv[2])),sort_keys=True))
    else:print(json.dumps(evaluate(read_batches(sys.argv[2]),sys.argv[1]),sort_keys=True))
