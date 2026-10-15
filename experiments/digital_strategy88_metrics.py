"""Retained paid strategy histories only; no World/source/target/referee imports."""
import hashlib,json
ARMS=('adaptive','history_reset','credit_misbound','explore')
FIXED=('fixed0','fixed1','cue_identity','cue_inverse','fixed_alternation','latest_reactive')+tuple('rr'+str(i) for i in range(4))
ROLES=tuple(f'{a}:{i}' for a in ARMS for i in range(4))+FIXED
ENTRIES=(1,6,11,16);ACTS={2:0,7:1,12:2,18:3}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def summarize(row,proof):
 role=row['role'];assert role==proof['role'] and proof['physics']['verified']
 state=row['state'];events=state['events'];ledger=row['ledger'];assert len(events)==len(ledger)==proof['physics']['ticks']
 assert digest({k:v for k,v in state.items() if k!='events'})==proof['physics']['final_state_sha256']
 assert not state['births'] and not state['writes'] and all(e['memory']==[0,0] for e in state['entities'].values())
 formation=3*len(row['programme'])+10;penalty=sum(e.get('penalty',0) for e in events);fees=sum(e.get('release_energy',0) for e in events)
 captured=sum(e.get('captured',0) for e in events);attempts=[e['attempt'] for e in events if 'attempt' in e]
 successes=sum(a['success'] for a in attempts);cpu=len(events);cost=formation+cpu+penalty+fees
 assert cost==proof['physics']['charged_cost']<=512 and fees in (0,16)
 completed=sum(x['completion'] is not None for x in ledger);assert completed==proof['physics']['completed']<=60
 living=sum(e['energy'] for e in state['entities'].values());deathheat=sum(e.get('death',{}).get('dissipated',0) for e in events)
 cap=20*successes-captured;failed=20*(len(attempts)-successes)
 assert living+deathheat==112+captured-cpu-penalty
 assert state['heat']==formation+cpu+penalty+fees+deathheat+cap+failed
 assert state['heat']+living+state['constructor_remaining']+20*len(state['food'])==1536+20*state['admitted']
 assert state['offered']==state['admitted']+state['rejected']
 selected=None;validated=None;ordinal=0;uses=[];selections=[];late=[];last=None;sense=None;obs=None
 for i,(event,item) in enumerate(zip(events,ledger,strict=True)):
  pc=item['dispatch_pc'];entry=item['entry']
  if entry is not None and entry['active'] and role.startswith(('history_reset:','credit_misbound:')):
   if role.startswith('history_reset:') or entry['actual_entry']!=entry['projected_entry']:selected=validated=None
  if 'sense' in event:sense=event['sense']
  if 'read_feedback' in event:obs=i
  if event['decoded'][0]==6:
   last=None
   if 'attempt' in event:
    ordinal+=1;a=event['attempt'];is_source=':' in role
    strategy=ACTS[pc] if is_source else None
    sensed=is_source and strategy>=2
    if sensed:assert sense['packet']==a['packet'] and sense['cue']==a['cue']
    valid=bool(is_source and not role.startswith('explore:') and selected is not None and validated is not None
      and selected['selected_strategy']==strategy and ordinal-validated['ordinal']>=2 and a['success'])
    use=dict(packet=a['packet'],cue=a['cue'],ordinal=ordinal,correct=a['success'],strategy=strategy,
     sensed_cue=a['cue'] if sensed else None,selection=selected,validation=validated,valid_older=int(valid),late=int(item['completed_before']>=48))
    if is_source:uses.append(use)
    if item['completed_before']>=48:late.append(dict(packet=a['packet'],cue=a['cue'],success=a['success']))
    last=dict(attempt=a,strategy=strategy,ordinal=ordinal,event=i,tick=event['tick'],completed_before=item['completed_before'],sensed_cue=a['cue'] if sensed else None)
  if item['completion'] is not None and ':' in role and not role.startswith('explore:'):
   if last is not None:
    assert obs is not None and last['event']<obs<=i and events[obs]['read_feedback']==last['attempt']['success']
    if last['attempt']['success']==0:
     target=ENTRIES.index(item['completion']['entry']);assert target==(last['strategy']+1)%4
     selected=dict(ordinal=last['ordinal'],event=last['event'],tick=last['tick'],chosen_strategy=last['strategy'],
      selected_strategy=target,feedback=0,observed_cue=last['sensed_cue'],completed_before=last['completed_before'])
     selections.append(selected);validated=None
    elif selected is not None and selected['selected_strategy']==last['strategy'] and validated is None:
     validated=dict(ordinal=last['ordinal'],event=last['event'],feedback_event=obs,feedback=1,completed_before=last['completed_before'])
   last=None;obs=None
 stop='death' if not state['entities'] else 'decisions' if completed==60 else 'horizon' if state['tick']==1024 else 'cost_budget'
 assert row['stop_reason']==stop
 return dict(role=role,completed=completed,served=len(attempts),successes=successes,deaths=state['deaths'],
  cpu=cpu,formation=formation,penalty=penalty,fees=fees,C=cost,unused_budget=512-cost,captured=captured,cap_heat=cap,
  failed_packet_heat=failed,heat=state['heat'],living=living,constructor_remaining=state['constructor_remaining'],food=len(state['food']),
  offered=state['offered'],admitted=state['admitted'],rejected=state['rejected'],absence=sum(e['decoded'][0]==6 and 'attempt' not in e for e in events),
  N=20*successes-formation-cpu-penalty,O=captured-cpu-penalty,E=captured-cpu-penalty-formation-fees,
  late=late,uses=uses,selections=selections,observed_mixed=int(len({a['target'] for a in attempts})>1),
  warm_packets=[e['attempt']['packet'] for e,item in zip(events,ledger) if item['completed_before']<48 and 'attempt' in e],
  warm_sha256=digest([e for e,item in zip(events,ledger) if item['completed_before']<48]),stop_reason=stop)
def derive(body,proof):
 assert body['error'] is None and body['seed']==proof['seed'] and body['software_only'] is proof['software_only']
 assert [r['role'] for r in body['records']]==list(ROLES)==[r['role'] for r in proof['summaries']]
 rows=[summarize(r,p) for r,p in zip(body['records'],proof['summaries'],strict=True)];lookup={r['role']:r for r in rows};endpoints=[]
 for prior in range(4):
  causal={a:lookup[f'{a}:{prior}'] for a in ARMS[:3]}
  assert len({r['warm_sha256'] for r in causal.values()})==1
  opportunities={a:{(x['packet'],x['cue']):x['success'] for x in r['late']} for a,r in causal.items()}
  common=set.intersection(*(set(x) for x in opportunities.values()))
  intact=causal['adaptive'];valid=[u for u in intact['uses'] if u['late'] and u['valid_older'] and (u['packet'],u['cue']) in common]
  refs=[lookup[r] for r in FIXED]
  endpoints.append(dict(seed=body['seed'],prior=prior,completed=intact['completed'],common=len(common),
   correct=sum(opportunities['adaptive'][k] for k in common),reset=sum(opportunities['history_reset'][k] for k in common),
   misbound=sum(opportunities['credit_misbound'][k] for k in common),older_uses=len(valid),observed_mixed=intact['observed_mixed'],
   whole_correct=intact['successes'],explore_correct=lookup[f'explore:{prior}']['successes'],oracle_correct=max(r['successes'] for r in refs),
   N=intact['N'],E=intact['E'],C=intact['C'],oracle_N=max(r['N'] for r in refs),oracle_E=max(r['E'] for r in refs)))
 return dict(seed=body['seed'],software_only=body['software_only'],rows=rows,endpoints=endpoints,execution_admission=False,stage_credit=False)
