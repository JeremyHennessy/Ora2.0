"""Complete retained paths/origins only; no biological/source/metric imports."""
import collections,hashlib,json,os,stat,sys
from pathlib import Path
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def pairs(items):
 d={}
 for k,v in items:assert k not in d;d[k]=v
 return d
def read(s):
 p=Path(s['path']);assert p.is_absolute() and 0<s['extent']<=64*1024**2
 for q in (p,*p.parents):
  a=q.lstat();assert not stat.S_ISLNK(a.st_mode) and not getattr(a,'st_file_attributes',0)&0x400
 a=p.lstat();assert stat.S_ISREG(a.st_mode) and a.st_nlink==1 and a.st_size==s['extent']
 with p.open('rb') as f:
  b=os.fstat(f.fileno());assert (a.st_dev,a.st_ino,a.st_size)==(b.st_dev,b.st_ino,b.st_size);data=f.read(64*1024**2+1)
 b=p.lstat();assert (a.st_dev,a.st_ino,a.st_size)==(b.st_dev,b.st_ino,b.st_size)
 assert len(data)==s['extent'] and hashlib.sha256(data).hexdigest()==s['sha256']
 v=json.loads(data,object_pairs_hook=pairs);assert enc(v)==data;return v
ENTRIES=(1,6,11,16);ACTS={2:0,7:1,12:2,18:3}
def trace(row,metric):
 events=row['state']['events'];ledger=row['ledger'];source=':' in row['role'];role=row['role'];uses=[];selections=[]
 choice=None;confirmation=None;ordinal=0;pending=None;feedback_index=None;sense=None
 pc_counts=collections.Counter();paths=collections.Counter();loops={};origin_counts=collections.Counter();observed=[{},{}];predictions=[]
 for index,(event,control) in enumerate(zip(events,ledger,strict=True)):
  pc=control['dispatch_pc'];loop=control['completed_before'];pc_counts[pc]+=1
  part=loops.setdefault(loop,dict(cpu=0,pcs=[],attempt=None,complete=False));part['cpu']+=1;part['pcs'].append(pc)
  if pc==0:paths['header']+=1
  else:paths[('late' if loop>=48 else 'warm')+':'+str(pc)]+=1
  entry=control['entry']
  if entry and entry['active'] and source and (role.startswith('history_reset:') or role.startswith('credit_misbound:') and entry['actual_entry']!=entry['projected_entry']):choice=confirmation=None
  if 'sense' in event:sense=event['sense']
  if 'read_feedback' in event:feedback_index=index
  if event['decoded'][0]==6:
   pending=None
   if 'attempt' in event:
    a=event['attempt'];ordinal+=1;strategy=ACTS[pc] if source else None;sensed=source and strategy>=2
    if sensed:assert sense['packet']==a['packet'] and sense['cue']==a['cue']
    # Only a real SENSE with the same leased packet can attach personally observed bit to cue.
    if sense and sense['packet']==a['packet']:
     bit=a['port'] if a['success'] else 1-a['port'];assert bit==a['target'];observed[int(a['packet']>=48)][str(sense['cue'])]=bit
    old=bool(source and not role.startswith('explore:') and choice is not None and confirmation is not None and choice['selected_strategy']==strategy and ordinal-confirmation['ordinal']>=2 and a['success'])
    if source:
     u=dict(packet=a['packet'],cue=a['cue'],ordinal=ordinal,correct=a['success'],strategy=strategy,sensed_cue=a['cue'] if sensed else None,
      selection=choice,validation=confirmation,valid_older=int(old),late=int(loop>=48));uses.append(u)
     prefix='late:' if loop>=48 else 'warm:';origin_counts[prefix+'served']+=1;origin_counts[prefix+'correct']+=a['success']
     origin_counts[prefix+('default_or_unvalidated' if confirmation is None else 'validated')]+=1
     if choice is not None:
      origin_counts[prefix+('selected_precut' if choice['completed_before']<48 else 'selected_postcut')]+=1
      if confirmation is not None and ordinal-confirmation['ordinal']>=2:
       origin_counts[prefix+('older_correct' if a['success'] else 'older_wrong')]+=1
       origin_counts[prefix+('precut_older_correct' if choice['completed_before']<48 else 'postcut_older_correct')]+=int(old)
     predictions.append(dict(packet=a['packet'],cue=a['cue'],port=a['port'],target=a['target'],correct=a['success'],strategy=strategy,late=int(loop>=48),origin=choice,validated=confirmation,older_correct=int(old),sensed=int(sensed)))
    pending=dict(attempt=a,strategy=strategy,ordinal=ordinal,event=index,tick=event['tick'],completed_before=loop,sensed_cue=a['cue'] if sensed else None)
    part['attempt']=a
  if control['completion'] is not None:
   part['complete']=True
   if source and not role.startswith('explore:'):
    if pending:
     assert feedback_index is not None and pending['event']<feedback_index<=index and events[feedback_index]['read_feedback']==pending['attempt']['success']
     if not pending['attempt']['success']:
      target=ENTRIES.index(control['completion']['entry']);assert target==(pending['strategy']+1)%4
      choice=dict(ordinal=ordinal,event=pending['event'],tick=pending['tick'],chosen_strategy=pending['strategy'],selected_strategy=target,feedback=0,observed_cue=pending['sensed_cue'],completed_before=pending['completed_before']);selections.append(choice);confirmation=None
     elif choice and choice['selected_strategy']==pending['strategy'] and confirmation is None:
      confirmation=dict(ordinal=ordinal,event=pending['event'],feedback_event=feedback_index,feedback=1,completed_before=pending['completed_before'])
    pending=None;feedback_index=None
 assert ordinal==metric['served'] and sum(pc_counts.values())==metric['cpu']==len(events)
 if source:assert uses==metric['uses'] and selections==metric['selections']
 completed_costs=collections.Counter();unfinished=0
 for loop,v in loops.items():
  if v['pcs'][0]==0:v['pcs']=v['pcs'][1:];v['cpu']-=1
  if not v['pcs']:continue
  if source and v['complete']:
   outcome='absence' if v['attempt'] is None else 'success' if v['attempt']['success'] else 'error'
   strategy=next((ACTS[p] for p in v['pcs'] if p in ACTS),None)
   expect=(5 if outcome=='error' else 6) if strategy==3 else (4 if outcome=='error' else 5)
   assert v['cpu']==expect;completed_costs[str(strategy)+':'+outcome+':'+str(expect)]+=1
  elif not v['complete']:unfinished+=v['cpu']
 cpu=len(events);penalty=sum(e.get('penalty',0) for e in events);captured=sum(e.get('captured',0) for e in events);fees=sum(e.get('release_energy',0) for e in events);formation=3*len(row['programme'])+10
 assert (cpu,penalty,captured,fees,formation)==tuple(metric[k] for k in ('cpu','penalty','captured','fees','formation'))
 assert metric['N']==20*sum(e.get('attempt',{}).get('success',0) for e in events)-formation-cpu-penalty
 assert metric['E']==captured-cpu-penalty-formation-fees
 return dict(role=role,pc_cpu={str(k):v for k,v in sorted(pc_counts.items())},path_cpu=dict(paths),completed_loop_costs=dict(completed_costs),unfinished_cpu=unfinished,
  origin_counts=dict(origin_counts),use_count=len(uses),selection_count=len(selections),predictions=predictions,observed_maps=observed,actual_entry_changes=sum(bool(l['entry'] and l['entry']['actual_entry']!=l['entry']['projected_entry']) for l in ledger),
  costs={k:metric[k] for k in ('cpu','served','successes','deaths','formation','penalty','fees','N','O','E','C')})
def main():
 q=json.loads(Path(sys.argv[1]).read_bytes());assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==q['source_sha256']
 assert [b['seed'] for b in q['batches']]==list(range(1010100,1010106))+list(range(1010300,1010306))
 all_rows=[];contrasts=[];contexts=[];totals=collections.Counter();misbound=collections.Counter();prior2_losses=[];aggregates={}
 for b in q['batches']:
  body=read(b['body']);metrics=read(b['metrics']);proof=read(b['proof']);assert body['seed']==metrics['seed']==proof['seed']==b['seed']
  assert body['error'] is None and len(body['records'])==len(metrics['rows'])==len(proof['summaries'])==26
  assert [r['role'] for r in body['records']]==[r['role'] for r in metrics['rows']]==[r['role'] for r in proof['summaries']]
  rows=[];maps=[{},{}]
  for raw,m,p in zip(body['records'],metrics['rows'],proof['summaries'],strict=True):
   assert p['physics']['verified'] and p['role']==raw['role'];r=trace(raw,m);r['seed']=b['seed'];rows.append(r);all_rows.append(r)
   totals['histories']+=1;totals['source_histories']+=int(':' in r['role']);totals['uses_independently_reproduced']+=r['use_count'];totals['selections_independently_reproduced']+=r['selection_count']
   for k,v in r['costs'].items():totals[k]+=v
   for phase in range(2):
    for cue,bit in r['observed_maps'][phase].items():assert cue not in maps[phase] or maps[phase][cue]==bit;maps[phase][cue]=bit
   arm=r['role'].split(':')[0] if ':' in r['role'] else 'references';key=('primary:' if b['seed']<1010300 else 'unseen:')+arm
   dst=aggregates.setdefault(key,collections.Counter());dst.update(r['origin_counts'])
  known=set(maps[0])&set(maps[1]);cm=dict(seed=b['seed'],paid_sensed_maps=maps,complete=[len(m)==8 for m in maps],
   observed_masks=[sum(int(bit)<<int(cue) for cue,bit in m.items()) if len(m)==8 else None for m in maps],changed_cues=sum(maps[0][c]!=maps[1][c] for c in known),unchanged_cues=sum(maps[0][c]==maps[1][c] for c in known),unknown_cues=8-len(known));contexts.append(cm)
  lookup={r['role']:r for r in rows}
  for prior,endpoint in enumerate(metrics['endpoints']):
   a=lookup[f'adaptive:{prior}'];reset=lookup[f'history_reset:{prior}'];mis=lookup[f'credit_misbound:{prior}']
   late={r['role']:{(v['packet'],v['cue']):v for v in r['predictions'] if v['late']} for r in (a,reset,mis)};common=set.intersection(*(set(v) for v in late.values()));assert len(common)==endpoint['common']
   ac=sum(late[a['role']][k]['correct'] for k in common);rc=sum(late[reset['role']][k]['correct'] for k in common);mc=sum(late[mis['role']][k]['correct'] for k in common)
   assert (ac,rc,mc)==tuple(endpoint[k] for k in ('correct','reset','misbound'))
   assert sum(late[a['role']][k]['older_correct'] for k in common)==endpoint['older_uses']
   key='gain' if ac>mc else 'loss' if ac<mc else 'tie';misbound[key]+=1
   item=dict(seed=b['seed'],prior=prior,observed_masks=cm['observed_masks'],common=len(common),adaptive=ac,history_reset=rc,misbound=mc,
    reset_delta=ac-rc,misbound_delta=ac-mc,actual_misbound_entry_changes=mis['actual_entry_changes'],whole_adaptive=a['costs']['successes'],whole_reset=reset['costs']['successes'],whole_misbound=mis['costs']['successes'],
    differing_reset_opportunities=[dict(packet=k[0],cue=k[1],adaptive=late[a['role']][k],reset=late[reset['role']][k]) for k in sorted(common) if late[a['role']][k]['correct']!=late[reset['role']][k]['correct']])
   contrasts.append(item)
   if prior==2 and ac<rc:prior2_losses.append(item)
  del body,metrics,proof,raw,m,p,rows,lookup,late,a,reset,mis
 assert totals['histories']==312 and totals['source_histories']==192 and len(contrasts)==48
 out=dict(verified=True,new_worlds=0,new_targets=0,scope='Independent retained-event origin/path diagnosis,not another raw physics replay or acceptance rescore',totals=dict(totals),all312=all_rows,all48_contrasts=contrasts,all12_observed_contexts=contexts,prior2_losses=prior2_losses,misbinding_late_pair_counts=dict(misbound),origin_aggregates={k:dict(v) for k,v in aggregates.items()},stage_credit=False)
 data=enc(out);assert len(data)<=8*1024**2;Path(q['output']).write_bytes(data)
 print(enc(dict(verified=True,histories=312,source_histories=192,worlds=0,targets=0,extent=len(data),sha256=hashlib.sha256(data).hexdigest())).decode())
if __name__=='__main__':main()
