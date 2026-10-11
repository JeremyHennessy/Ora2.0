"""Configuration checks plus independent old-law interpreters; no producer import."""
import json
from .digital_singlecopy09_audit import audit as matched_audit
from .digital_release07_audit import audit as ordinary_audit

DOUBLE=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]
ANCESTOR=[[4,1,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]

def endpoint(metrics):
    return metrics['births']>=1 and metrics['descendant_births']>=1 and metrics['fresh_packets']>=1 and metrics['descendant_fresh']>=1

def audit(record):
    assert set(record)=={'contract','configuration','history'}
    assert record['contract']=='DIGITAL-ORDINARY-ADMISSION-10-v1'
    name=record['configuration'];row=record['history']
    assert type(row['seed']) is int and row['seed'] in (25890,25891)
    if name=='actual_ordinary':
        assert row['route']=='ancestor' and row['mode']=='faithful' and row['genesis_program']==ANCESTOR
        metrics=ordinary_audit(row)
    else:
        assert name in ('matched_double','disabled_double')
        assert row['route']=='admission10_double' and row['genesis_program']==DOUBLE
        assert row['mode']==('copy_disabled' if name=='disabled_double' else 'faithful')
        assert 3*len(row['genesis_program'])+18+16<=128
        metrics=matched_audit(row)
    metrics['configuration']=name
    events=row['final']['events']
    metrics['first_birth_tick']=next((e['tick'] for e in events if 'birth' in e),None)
    metrics['paid_sampling_draws']=sum(len(e.get('sampling',[])) for e in events)
    metrics['selector_store_energy']=sum(e.get('selector_store_energy',0) for e in events)
    metrics['descendant_food']=sum(bool(e.get('attempt',{}).get('success')) and e['actor']!=0 for e in events)
    metrics['descendant_fresh']=sum(bool(e.get('attempt',{}).get('success')) and e['actor']!=0 and 16<=e['attempt']['packet']<32 for e in events if 'attempt' in e)
    metrics['ordinary_endpoint']=endpoint(metrics)
    return metrics

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:print(json.dumps(audit(json.load(f)),sort_keys=True))
