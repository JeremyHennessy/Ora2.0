"""Closed-data paid paths and own-feedback origins; no producer/target imports.

Caller must bind complete literal/parity/native/source/config/grant evidence.
This module never grants execution or substitutes for physical reconstruction.
"""
import hashlib,json

ARMS=('intact','credit_erased','recall_disabled','model_disabled','update_frozen')
REFERENCES=('fixed0','fixed1','retained_cue','retained_inverse','current_distractor','current_inverse','alternation0','alternation1','latest0','latest1')
ROLES=tuple(f'q{q}:{a}' for q in (2,4,8) for a in ARMS)+REFERENCES

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def derive_row(row):
 role=row['role'];assert type(role) is str and role in ROLES
 state=row['state'];events=state['events'];ledger=row['ledger'];program=row['programme'];capacity=program[0][1]
 assert type(events) is list and len(events)==state['tick']==len(ledger) and capacity in (2,4,8)
 assert state['births']==state['writes']==0
 formation=3*len(program)+capacity+8;cpu=len(events)
 penalty=sum(e.get('penalty',0) for e in events);fees=sum(e.get('release_energy',0) for e in events)
 captured=sum(e.get('captured',0) for e in events)
 attempted=[e for e in events if 'attempt' in e];successes=sum(e['attempt']['success'] for e in attempted)
 absent=sum(e.get('decoded',[None])[0]==6 and 'attempt' not in e for e in events)
 capheat=sum(20-e.get('captured',0) for e in attempted if e['attempt']['success'])
 failedheat=20*(len(attempted)-successes);deathheat=sum(e.get('death',{}).get('dissipated',0) for e in events)
 living=sum(e['energy'] for e in state['entities'].values())
 assert formation+cpu+penalty+fees+capheat+failedheat+deathheat==state['heat']
 assert 112+captured==cpu+penalty+living+deathheat
 assert state['constructor_remaining']==256-formation-112-fees
 assert state['heat']+living+state['constructor_remaining']+20*len(state['food'])==1536+20*state['admitted']
 offers=[i for e in events for i in e['input']]
 assert len(offers)==state['offered'] and sum(i['outcome']=='admitted' for i in offers)==state['admitted']
 assert state['offered']==state['admitted']+state['rejected']
 assert len(state['food'])==64+state['admitted']-len(attempted)
 C=formation+cpu+penalty+fees;assert C<=1024
 N=20*successes-formation-cpu-penalty;O=captured-cpu-penalty;E=O-formation-fees
 phase='cue';completed=0;current=None;trials=[];origins=[];uses=[];last_write={}
 seen=[{},{}];previous=dict(pc=0,registers=[0,0],memory=[0]*capacity)
 warm_hash=None;warm_energy=None;store_count=0;read_count=0;charged=formation
 for ordinal,(event,annotation) in enumerate(zip(events,ledger),1):
  pc=previous['pc'];op,a,b=program[pc]
  assert event['decoded']==[op,a,b] and event['tick']==annotation['tick']==ordinal
  assert annotation['pc']==pc and annotation['trial']==completed and annotation['phase_before']==phase
  registers=previous['registers'][:]
  if annotation['cut'] is not None:
   cut=annotation['cut'];assert cut['register']==1 and cut['before']==registers[1] and cut['after']==0
   registers[1]=0
  if op==0:
   symbol=event['sense']['cue'];channel=annotation['observation']['channel']
   assert annotation['observation']['value']==symbol
   if phase=='cue':
    assert channel=='cue';current=dict(trial=completed,cue=symbol,pre=None,post=None,served=0,success=0,
      port=None,packet=None,act_tick=None,feedback_tick=None,observed_label=None,completed=0,model_origin=None)
    trials.append(current);phase='pre'
   elif phase=='pre':assert channel=='pre';current['pre']=symbol;phase='act'
   else:assert phase=='post' and channel=='post';current['post']=symbol;phase='ready'
  elif op==19:
   read=annotation['read'];assert read is not None;read_count+=1
   if pc==3:
    origin=last_write.get(read['index'])
    used=not(completed>=48 and role.endswith(':model_disabled'))
    current['model_origin']=dict(origin) if used and origin is not None and origin['bit']==read['returned']%2 else None
   elif pc==9:current['updater_read_tick']=ordinal
  elif op==6:
   assert phase=='act';phase='post';attempt=event.get('attempt')
   if attempt is not None:
    current.update(served=1,success=attempt['success'],port=attempt['port'],packet=attempt['packet'],act_tick=ordinal)
    origin=current['model_origin']
    if (origin is not None and current['success'] and origin['cue']==current['cue'] and
        completed-origin['trial']>=2 and origin['changed_map'] and origin['physical_revision']):
     uses.append(dict(trial=completed,cue=current['cue'],port=current['port'],origin=origin,act_tick=ordinal))
  elif op==1 and phase=='ready' and current['served'] and event['read_feedback'] in (0,1):
   value=event['read_feedback'];label=current['port'] if value==1 else 1-current['port']
   bound=(':' in role and registers[1]==current['cue'])
   current.update(feedback_tick=ordinal,observed_label=label,negative=int(value==0),bound_observation=int(bound))
   bank=int(completed>=48);cue=current['cue']
   if bound:
    assert cue not in seen[bank] or seen[bank][cue]==label,'Contradictory personally bound map'
    seen[bank][cue]=label
  elif op==21 and pc==10 and ':' in role:current['updater_not_tick']=ordinal
  elif op==20:
   store_count+=1;store=annotation['store'];assert store is not None
   if store['applied']:
    index=store['index'];last_write.pop(index,None)
    correct_binding=(current.get('negative')==1 and current.get('bound_observation')==1 and current['feedback_tick'] is not None and
       current['feedback_tick']<current.get('updater_read_tick',0)<current.get('updater_not_tick',0)<ordinal and
       registers[1]==current['cue'] and index==current['cue']%capacity and
       store['attempted']%2==current['observed_label'])
    if correct_binding and 'after' in event:
     assert event['after']['memory'][index]==store['attempted']
     old=seen[0].get(current['cue'])
     origin=dict(write_tick=ordinal,index=index,cue=current['cue'],bit=store['attempted']%2,
       trial=completed,act_tick=current['act_tick'],feedback_tick=current['feedback_tick'],
       physical_revision=int(store['before']%2!=store['attempted']%2),
       changed_map=int(completed>=48 and old is not None and old!=current['observed_label']))
     last_write[index]=origin;origins.append(origin)
  after=event.get('after')
  entry=2 if role.startswith(('latest','alternation')) else 1
  completion=after is not None and pc!=0 and op==7 and after['pc']==entry
  assert (annotation['completion'] is not None)==completion
  if completion:
   assert phase=='ready' and current is not None;current['completed']=1;current['finish_tick']=ordinal
   completed+=1;phase='cue';assert annotation['completion']['completed']==completed
   if completed==48:
    warm_hash=digest(dict(events=events[:ordinal],ledger=ledger[:ordinal]));warm_energy=after['energy']
  assert annotation['phase_after']==phase
  if after is not None:previous=after
  else:assert ordinal==len(events)
  charged+=1+event.get('penalty',0)+event.get('release_energy',0)
  assert annotation['cost_after']==charged
 assert len(trials)<=60 and sum(t['served'] for t in trials)==len(attempted)
 assert sum(t['success'] for t in trials)==successes
 observations={}
 for index,name in enumerate(('warm','late')):
  observations[name]=dict(bits={str(c):v for c,v in sorted(seen[index].items())},
    full_mask=sum(v<<c for c,v in seen[index].items()) if len(seen[index])==8 else None,
    unseen_cues=[c for c in range(8) if c not in seen[index]])
 physical=dict(C=C,N=N,O=O,E=E,formation=formation,CPU=cpu,penalty=penalty,fee=fees,captured=captured,
  cap_heat=capheat,failed_packet_heat=failedheat,death_heat=deathheat,heat=state['heat'],living=living,
  constructor=state['constructor_remaining'],food=len(state['food']),offered=state['offered'],admitted=state['admitted'],
  rejected=state['rejected'],served=len(attempted),correct=successes,absence=absent,deaths=state['deaths'],births=0)
 return dict(role=role,capacity=capacity,completed=completed,stop_reason=row['stop_reason'],physical=physical,
  trials=trials,origins=origins,older_changed_uses=uses,observations=observations,model_READs=read_count,paid_STOREs=store_count,
  warm_prefix_sha256=warm_hash,warm_energy=warm_energy,
  cold_or_warm_prefix_sha256=warm_hash if warm_hash is not None else digest(dict(events=events,ledger=ledger)),
  source_free=True,execution_admission=False)

def context(seed,rows):
 assert type(seed) is int and type(rows) is list and len(rows)==25
 assert len({r['role'] for r in rows})==25 and {r['role'] for r in rows}==set(ROLES)
 by={r['role']:r for r in rows};oracle=max(by[r]['physical']['correct'] for r in REFERENCES);endpoints=[]
 for q in (2,4,8):
  actors={a:by[f'q{q}:{a}'] for a in ARMS}
  assert len({r['cold_or_warm_prefix_sha256'] for r in actors.values()})==1,'Independent warm-prefix mismatch'
  tables={a:{(t['trial'],t['cue'],t['pre'],t['post']):t for t in row['trials']
    if t['trial']>=48 and t['completed'] and t['served']} for a,row in actors.items()}
  common=set.intersection(*(set(t) for t in tables.values()))
  common_correct={a:sum(tables[a][k]['success'] for k in common) for a in ARMS}
  intact=actors['intact']
  endpoints.append(dict(seed=seed,capacity=q,intact_completed=intact['completed'],common_count=len(common),
   common_keys=[list(k) for k in sorted(common)],common_correct=common_correct,
   older_changed_uses=sum(u['trial']>=48 for u in intact['older_changed_uses']),
   whole_correct=intact['physical']['correct'],reference_oracle_correct=oracle,
   physical={a:r['physical'] for a,r in actors.items()},warm_energy={a:r['warm_energy'] for a,r in actors.items()}))
 return dict(seed=seed,rows=rows,endpoints=endpoints,roles=list(ROLES),execution_admission=False,source_free=True,stage_credit=False)
