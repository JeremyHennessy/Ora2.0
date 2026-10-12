"""Literal event scan over independent numeric first effects; no producer import."""
from .digital_history36_independent import diagnose as numeric_effect

def diagnose(row):
    result=numeric_effect(row);earlier=[]
    for r in result['reads']:
        origin=r['origin_tick'];effect=r['effect_tick'];own=r['source']=='own'
        ordinal=1+sum(x==origin for x in earlier) if own else None
        if own:earlier.append(origin)
        last=None;count=0
        if effect is not None:
            for e in row['final']['events']:
                if e['tick']>=effect:break
                if e['decoded'][0]==6:
                    last=e['tick']
                    if origin is not None and e['tick']>origin:count+=1
        r['origin_read_ordinal']=ordinal
        r['repeat_of_own_origin']=ordinal is not None and ordinal>1
        r['latest_act_before_effect']=last
        r['intervening_act_count']=count
        r['retained_beyond_latch']=own and effect is not None and count>0
        r['retained_own_before_completion']=r['retained_beyond_latch'] and r['read_before_completion'] and r['effect_before_completion']
        if effect is None:relation='no_effect'
        elif r['source']=='unrelated':relation='unrelated'
        elif not own:relation='initial_or_empty'
        elif count:relation='replaced'
        else:relation='latest'
        r['latch_relation']=relation
    result['classification']='local_first_effect_latch_age_only'
    return result

if __name__=='__main__':
    import json,sys
    with open(sys.argv[1],encoding='utf-8') as f:batch=json.load(f)
    print(json.dumps([dict(role=x['role'],diagnosis=diagnose(x['row'])) for x in batch['histories']],sort_keys=True,separators=(',',':')))
