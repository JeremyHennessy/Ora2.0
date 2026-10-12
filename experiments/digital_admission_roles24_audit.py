"""Independent backward origin resolution for prepared role records only."""
import json,sys

def reachable(record):
    try:
        if type(record) is not dict or set(record)!=set(('alive_through_change','actions','reads')) or record.get('alive_through_change') is not True:return False
        actions,reads=record['actions'],record['reads']
        if type(actions) is not list or type(reads) is not list or not actions or not reads or max(len(actions),len(reads))>512:return False
        def ordered(rows):
            ticks=[x['tick'] for x in rows]
            return all(type(t) is int and 1<=t<=512 for t in ticks) and ticks==sorted(set(ticks))
        if not ordered(actions) or not ordered(reads):return False
        bytick={a['tick']:a for a in actions};post=[];fresh=[]
        for a in actions:
            if set(a)!=set(('tick','actor','attempt')) or type(a['actor']) is not int or a['actor']!=0:return False
            p=a['attempt']
            if p is None:continue
            if type(p) is not dict or set(p)!=set(('packet','port','success')) or not all(type(v) is int for v in p.values()):return False
            if p['packet'] not in range(64) or p['port'] not in (0,1) or p['success'] not in (0,1):return False
            if a['tick']>=64:
                post.append(p)
                if p['success']==1 and p['packet'] in range(16,32):fresh.append(p['packet'])
        if len(fresh)!=len(set(fresh)):return False
        identities=[];outcomes=[]
        for read in reads:
            if set(read)!=set(('tick','actor','origin','source_tick','value')) or type(read['actor']) is not int or read['actor']!=0 or type(read['value']) is not int or read['value'] not in (0,1) or read['tick'] in bytick:return False
            earlier=[t for t in bytick if t<read['tick']]
            last=bytick[max(earlier)] if earlier else None
            if last is None:
                if (read['origin'],read['source_tick'],read['value'])!=('initial',None,0):return False
            elif last['attempt'] is None:
                if (read['origin'],read['source_tick'],read['value'])!=('empty_reset',None,0):return False
            else:
                if read['origin']!='own_actual_attempt' or type(read['source_tick']) is not int or read['source_tick']!=last['tick'] or read['value']!=last['attempt']['success']:return False
                if last['tick']>=64:identities.append(last['tick']);outcomes.append(read['value'])
        return len(post)>=4 and sum(p['success'] for p in post)>=4 and len(fresh)==16 and len(set(identities))>=16 and set(outcomes)=={0,1}
    except (KeyError,TypeError):return False

if __name__=='__main__':
    data=json.load(open(sys.argv[1],encoding='utf-8'))
    assert data['contract']=='DIGITAL-ADMISSION-ROLES-24-v1' and data['software_only'] is True and data['new_world_histories']==0 and data['seeds_executed']==[]
    expected={'reactive_positive_without_cold_failure':True,'empty_reset_is_not_personal_failure':False,'repeated_latch_not_sixteen_distinct_post_attempts':False,'other_actor_history':False,'boolean_attempt_identity':False,'mismatched_feedback_value':False,'no_personal_failure_read':False,'fifteen_fresh_packets':False,'missing_survival':False,'future_attempt_as_past_history':False}
    assert len(data['records'])==10 and {r['name'] for r in data['records']}==set(expected)
    for r in data['records']:assert reachable(r['record']) is r['actual'] is r['expected'] is expected[r['name']]
    print(json.dumps(dict(verified=True,prepared_records=10,accepted=1,refused=9,new_world_histories=0,seeds_executed=[],learning=False,stage_credit=False,classification='PROSPECTIVE_ROLE_PREDICATES_ONLY'),sort_keys=True))
