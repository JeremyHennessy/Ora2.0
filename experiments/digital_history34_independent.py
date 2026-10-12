"""Independent backward-origin extraction and literal History33 predicate.

No producer, scorer or World import. Full VM truth/custody is a caller precondition.
"""
import hashlib
import json


def extract(row):
    es=row['final']['events'];code=row['genesis_program'];mode=row['control_mode']
    if mode not in ('intact','retained_disabled','own_disrupted') or not 1<=len(es)<=512 or not 1<=len(code)<=32: raise ValueError('scope')
    for triple in code:
        if type(triple) is not list or len(triple)!=3 or any(type(v) is not int or v<0 or v>31 for v in triple) or triple[0] not in (1,2,3,4,5,6,7,8,18): raise ValueError('code')
    success=[];death=[];readrows=[]
    for i,e in enumerate(es):
        if type(e['tick']) is not int or e['tick']!=i+1 or type(e['actor']) is not int or e['actor']!=0: raise ValueError('identity')
        if type(e['decoded'][0]) is not int or e['decoded'][0] not in (1,2,3,4,5,6,7,8,18): raise ValueError('channel')
        if 'death' in e:death.append(e['tick'])
        if 'attempt' in e:
            a=e['attempt']
            if e['decoded'][0]!=6 or any(type(a[k]) is not int for k in ('packet','port','success')) or a['packet'] not in range(32) or a['port'] not in (0,1) or a['success'] not in (0,1):raise ValueError('attempt')
            if a['success']==1:success.append((a['packet'],e['tick']))
        if e['decoded'][0]==1:
            earlier=[x for x in es[:i] if x['decoded'][0]==6]
            previous=earlier[-1] if earlier else None
            origin=previous['tick'] if previous and previous.get('attempt') is not None else None
            outcome=previous['attempt']['success'] if origin is not None else 0
            s=e['control']['personal_read']
            if (s['own_source_tick']!=origin or origin is not None and type(s['own_source_tick']) is not int
                    or type(s['original']) is not int or s['original']!=outcome
                    or type(s['value']) is not int or s['value'] not in (0,1)
                    or mode!='own_disrupted' and s['value']!=outcome):raise ValueError('origin')
            readrows.append((e['tick'],origin,outcome))
    if len({p for p,t in success})!=len(success) or death and death!=[len(es)]:raise ValueError('duplicate win or post-death event')
    t=max((t for p,t in success),default=None) if len(success)==32 else None
    stop=t if t is not None else len(es)+1
    before=[r for r in readrows if r[0]<stop and r[1] is not None and r[1]>=64]
    ids=set(r[1] for r in before);outs=sorted(set(r[2] for r in before));own=mode!='own_disrupted' and bool(ids)
    bill=3*len(code)+16
    m=dict(formation=bill,food=len(success),fresh=len([p for p,_ in success if p>=16]),own_origins=len(ids) if own else 0,
           terminal_tick=len(es),completed=t is not None,survived64=len(es)>=64 and (not death or death[0]>64),
           delivered_own=own,both_own_outcomes=own and outs==[0,1],completion_tick=t,paid_work=bill+t if t is not None else None)
    check(m)
    return dict(metric=m,diagnostic=dict(native_distinct_origins_before_cutoff=len(ids),native_outcomes_before_cutoff=outs,
                ignored_post_completion_reads=len([r for r in readrows if r[0]>=stop]),before_completion_cutoff=t,
                death_tick=death[0] if death else None,scope='measurement only; no historical endpoint rescore'),
                input_sha256=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest())


def check(m):
    if any(type(m[k]) is not int for k in ('formation','food','fresh','own_origins','terminal_tick')):raise ValueError('integer')
    if any(type(m[k]) is not bool for k in ('completed','survived64','delivered_own','both_own_outcomes')):raise ValueError('flag')
    if m['formation'] not in range(19,113,3) or not 0<=m['fresh']<=16 or not m['fresh']<=m['food']<=32 or not 0<=m['own_origins']<=512 or not 1<=m['terminal_tick']<=512:raise ValueError('range')
    if m['completed']:
        if type(m['completion_tick']) is not int or not 64<=m['completion_tick']<=m['terminal_tick'] or type(m['paid_work']) is not int or m['paid_work']-m['completion_tick']!=m['formation'] or (m['food'],m['fresh'],m['survived64'])!=(32,16,True):raise ValueError('bill')
    elif m['completion_tick'] is not None or m['paid_work'] is not None or m['food']==32:raise ValueError('null bill')
    if m['both_own_outcomes'] and not m['delivered_own']:raise ValueError('delivery')


def compare(arms,references):
    modes=('intact','retained_disabled','own_disrupted');roles=tuple('affine'+str(i) for i in range(8))+('alternating','fixed0','fixed1')
    if set(arms)!=set(modes) or set(references)!=set(roles):raise ValueError('denominator')
    for m in list(arms.values())+list(references.values()):check(m)
    if arms['own_disrupted']['delivered_own'] or len(set(m['formation'] for m in arms.values()))!=1:raise ValueError('matched control')
    a=arms['intact'];reasons=[];allcomplete=all(arms[k]['completed'] for k in modes)
    if not allcomplete:reasons.append('incomplete_candidate_or_control_exposure')
    if a['own_origins']<16 or not a['delivered_own'] or not a['both_own_outcomes']:reasons.append('insufficient_personal_opportunity_before_completion')
    if not references['affine3']['completed'] or not references['alternating']['completed']:reasons.append('ordinary_reference_failure')
    rs=[references[k] for k in roles if references[k]['completed']]
    if allcomplete and rs:
        competitors=rs+[arms['retained_disabled'],arms['own_disrupted']]
        if a['completion_tick']>=min(m['completion_tick'] for m in competitors) or a['paid_work']>=min(m['paid_work'] for m in competitors):reasons.append('no_strict_latency_and_paid_work_advantage')
    return dict(qualified=len(reasons)==0,reasons=reasons,incomplete_references=[k for k in roles if not references[k]['completed']],classification='prepared_predicate_or_scoped_retained_history_advantage',learning=False,stage_credit=False)


if __name__ == '__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:batch=json.load(f)
    print(json.dumps([dict(role=item['role'],**extract(item['row'])) for item in batch['histories']],sort_keys=True))
