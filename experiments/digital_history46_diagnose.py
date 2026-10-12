"""Local first-effect age only, never alternative outcomes or learned gain."""
from bisect import bisect_left
from .digital_history36_diagnose import diagnose as first_effect

def diagnose(row):
    result=first_effect(row)
    acts=[e['tick'] for e in row['final']['events'] if e['decoded'][0]==6]
    seen={}
    for r in result['reads']:
        origin=r['origin_tick'];effect=r['effect_tick'];own=r['source']=='own'
        if own:
            seen[origin]=seen.get(origin,0)+1
        r['origin_read_ordinal']=seen[origin] if own else None
        r['repeat_of_own_origin']=own and seen[origin]>1
        at=bisect_left(acts,effect) if effect is not None else 0
        last=acts[at-1] if effect is not None and at else None
        count=at-bisect_left(acts,origin+1) if effect is not None and origin is not None else 0
        r['latest_act_before_effect']=last
        r['intervening_act_count']=count
        r['retained_beyond_latch']=own and effect is not None and count>0
        r['retained_own_before_completion']=r['retained_beyond_latch'] and r['read_before_completion'] and r['effect_before_completion']
        r['latch_relation']=('no_effect' if effect is None else 'unrelated' if r['source']=='unrelated' else 'initial_or_empty' if not own else 'replaced' if count else 'latest')
    result['classification']='local_first_effect_latch_age_only'
    return result

if __name__=='__main__':
    import json,sys
    with open(sys.argv[1],encoding='utf-8') as f:batch=json.load(f)
    print(json.dumps([dict(role=x['role'],diagnosis=diagnose(x['row'])) for x in batch['histories']],sort_keys=True,separators=(',',':')))
