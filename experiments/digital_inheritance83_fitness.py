"""Closed-record fitness and proposal accounting, never a physics validator.

Caller must establish native custody/full literal proof before interpretation.
This module checks history binding and paid accounting; it imports no VM/referee.
All values are finite-horizon endpoints under the frozen INHERITANCE83 contract.
"""
import hashlib
import json


def metrics(state, proof):
    raw=json.dumps(state,sort_keys=True,separators=(',',':')).encode('ascii')
    assert hashlib.sha256(raw).hexdigest()==proof['history_sha256']
    assert proof['physics']['verified'] and len(proof['offspring'])==state['births']
    events=state['events'];children={c['child']:c for c in proof['offspring']}
    post={i:0 for i in children};lineages={0:[]};actual=[];offered=[]
    for event in events:
        if 'birth' in event:
            child=event['birth']['child'];lineages[child['id']]=child['lineage']
        if 'attempt' in event:
            a=event['attempt'];actual.append([a['packet'],a['cue'],lineages[event['actor']]])
            if event['actor'] in post and event['tick']>=1536:post[event['actor']]+=1
        offered.extend([[p['packet'],p['cue'],p['outcome']] for p in event['input']])
    functional={i:int(c['completed_64_served_decisions'] and post[i]>=16 and c['paid_replacement_with_own_acquisition']) for i,c in children.items()}
    sessions={};episodes=[];by_session={};by_header={};writes={};changed_functional=[];deaths={}
    for event in events:
        actor=event['actor']
        if 'sampler_started' in event:sessions[actor]=event['sampler_started']['session']
        draw=event.get('draw');key=(actor,sessions.get(actor))
        if draw and draw['stage']=='gate' and draw['value']==0:
            assert key not in by_session
            ep=dict(actor=actor,session=key[1],tick=event['tick'],proposed=None,header_write_id=None,paid_child=None,child_fitness=0,status='pending')
            by_session[key]=ep;episodes.append(ep)
        ep=by_session.get(key)
        if draw and draw['stage']=='allele' and 'sampler_finished' in event:
            assert ep is not None
            finished=event['sampler_finished'];ep['proposed']=finished['proposed']
            ep['status']='aborted' if finished['abort'] else 'accepted'
            assert ep['proposed'] is None if finished['abort'] else ep['proposed'] in (2,4,8)
            headers=[w for w in event.get('writes',[]) if w['index']==1]
            assert len(headers)<=1
            if headers:
                wid=headers[0]['write_id'];ep['header_write_id']=wid;by_header[wid]=ep
        for w in event.get('writes',[]):
            assert w['write_id'] not in writes;writes[w['write_id']]=w
        if 'birth' in event:
            birth=event['birth'];identity=birth['child']['id'];wid=birth['write_ids'][1]
            header=writes[wid];assert header['index']==1
            if header['value']!=header['source_value'] and functional[identity]:changed_functional.append(identity)
            if wid in by_header:
                ep=by_header[wid];assert ep['paid_child'] is None
                ep.update(paid_child=identity,actual_capacity=header['value'],child_fitness=functional[identity],status='paid_birth')
        if 'death' in event:deaths[actor]=event['death']['cause']
    living={int(i) for i in state['entities']}
    for ep in episodes:
        if ep['paid_child'] is None:
            ep['parent_death']=deaths.get(ep['actor']);ep['right_censored']=ep['actor'] in living
        ep['score']=3*((ep['proposed']==8)-(ep['proposed']==2))*ep['child_fitness']
    heat=dict(initial_formation=61,cpu=state['tick'],copied_words=len(writes),
              state_formation=sum(e['birth']['state_energy'] for e in events if 'birth' in e),
              birth_release=sum(e['birth']['release_energy'] for e in events if 'birth' in e),
              world_release=sum(e.get('release_energy',0) for e in events),
              failed_packets=20*sum(not e['attempt']['success'] for e in events if 'attempt' in e),
              cap_losses=sum(20-e['captured'] for e in events if 'captured' in e),
              wrong_penalties=sum(e.get('penalty',0) for e in events),
              death_dissipation=sum(e['death']['dissipated'] for e in events if 'death' in e))
    assert sum(heat.values())==state['heat']
    captured=sum(e.get('captured',0) for e in events)
    actor_cost=sum(heat[k] for k in ('cpu','copied_words','state_formation','birth_release','wrong_penalties','death_dissipation'))
    living_energy=sum(e['energy'] for e in state['entities'].values())
    assert 112+captured-actor_cost==living_energy
    return dict(seed=state['seed'],mode=state['mode'],finite_horizon=16384,
                R=sum(functional.values()),functional_children=sorted(i for i,f in functional.items() if f),
                post_expansion_served=post,changed_functional_children=changed_functional,
                S_numerator=sum(e['score'] for e in episodes),S_denominator=max(1,len(episodes)),
                gate0_episodes=len(episodes),accepted_uniform_proposals=sum(e['proposed'] is not None for e in episodes),
                proposal_counts={str(q):sum(e['proposed']==q for e in episodes) for q in (2,4,8)},episodes=episodes,
                births=state['births'],deaths=state['deaths'],paid_dispatches=state['tick'],heat=heat,
                captured=captured,living_energy=living_energy,paid_actor_cost=actor_cost,retained_operating_surplus=captured-actor_cost,
                constructor_remaining=state['constructor_remaining'],offered=state['offered'],admitted=state['admitted'],rejected=state['rejected'],
                actual_served_opportunities=actual,actual_offered_packets=offered,
                operating_surplus_scope='Report physical captured/heat/remaining energy separately; R is not retained energy',
                physics_validator=False,new_worlds=0,selection_accepted=False)
