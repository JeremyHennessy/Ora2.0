"""Closed-data paid-path and origin diagnosis. Stdlib only, never a VM."""
import collections,hashlib,json,math,os,stat,sys
from pathlib import Path

M=1024**2
GROUPS=('intact','model_erased','model_misbound','fallback_misbound','history_disabled','references')
SEEDS=list(range(1009700,1009708))+list(range(1009900,1009908))
DS=[[q,r] for q in (2,4,8) for r in ('fallback0','model','fallback1')]
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def read(s,cap):
 p=Path(s['path']);a=p.lstat();assert not p.is_symlink() and stat.S_ISREG(a.st_mode) and a.st_nlink==1
 assert 0<s['extent']==a.st_size<=cap
 with p.open('rb') as f:
  b=os.fstat(f.fileno());assert (a.st_dev,a.st_ino,a.st_size)==(b.st_dev,b.st_ino,b.st_size);raw=f.read(cap+1)
 assert len(raw)==s['extent'] and hashlib.sha256(raw).hexdigest()==s['sha256']
 value=json.loads(raw);assert enc(value)==raw;return value
def add(dst,values):
 for k,v in values.items():dst[k]=dst.get(k,0)+v
def label(d):return json.dumps(d,separators=(',',':'))

def trace(row,metric,group):
 events=row['state']['events'];ledger=row['ledger'];reference=group=='references'
 assert len(events)==len(ledger)==metric['cpu']
 pc_counts=collections.Counter();phases={'warm':collections.Counter(),'late':collections.Counter()}
 paths={};loops={};origins=collections.Counter();cells={} if reference else {i:None for i in range(row['programme'][0][1])}
 pending_prediction=None;semantic=None;error=None;ordinal=0;uses=[];revisions=[]
 actual_observed=[{},{}]
 for i,(event,control) in enumerate(zip(events,ledger,strict=True)):
  pc=control['dispatch_pc'];pc_counts[pc]+=1;phase='late' if control['completed_before']>=48 else 'warm'
  phases[phase]['cpu']+=1
  loop=loops.setdefault(control['completed_before'],dict(pcs=[],cpu=0,completed=False,attempt=None,absence=False))
  if pc!=0:loop['pcs'].append(pc);loop['cpu']+=1
  if control['completion'] is not None:loop['completed']=True
  if not reference:
   p='header' if pc==0 else 'fallback0' if pc<=5 else 'model' if pc<=15 else 'fallback1'
   paths[p]=paths.get(p,0)+1
   if control['entry'] is not None and control['entry']['active'] and group=='history_disabled':semantic=None
   if pc==7:
    source=control['read']['source_address'];pending_prediction=None if source is None else cells[source]
  attempt=event.get('attempt')
  if event['decoded'][0]==6:
   phases[phase]['acts']+=1
   if attempt is None:
    phases[phase]['absence']+=1;loop['absence']=True
    if not reference and pc==8:error=None
   else:
    ordinal+=1;loop['attempt']=attempt;phases[phase]['served']+=1
    phases[phase]['successes']+=attempt['success'];phases[phase]['errors']+=1-attempt['success']
    phases[phase]['captured']+=event.get('captured',0);phases[phase]['penalty']+=event.get('penalty',0)
    phases[phase]['cap_heat']+=20*attempt['success']-event.get('captured',0)
    actual_observed[int(attempt['packet']>=48)][str(attempt['cue'])]=attempt['target']
    if not reference:
     channel='model' if pc==8 else 'semantic';origin=pending_prediction if pc==8 else semantic
     if pc==8:error=dict(attempt,ordinal=ordinal,event=i,tick=event['tick']) if not attempt['success'] else None
     bit=bool(origin is not None and origin['bit']==attempt['port'])
     cue=bool(origin is not None and origin['cue']==attempt['cue'])
     gap=None if origin is None else ordinal-origin['ordinal']
     valid=bool(origin is not None and bit and (channel!='model' or cue) and gap>=2 and attempt['success']==1)
     use=dict(packet=attempt['packet'],cue=attempt['cue'],port=attempt['port'],target=attempt['target'],success=attempt['success'],
      ordinal=ordinal,event=i,tick=event['tick'],channel=channel,origin=origin,bit_match=bit,cue_match=cue,served_gap=gap,valid_older_correct=valid,late=phase=='late')
     uses.append(use)
     prefix=phase+':'+channel+':'
     origins[prefix+'served']+=1;origins[prefix+'correct']+=attempt['success']
     origins[prefix+'no_acquired_origin']+=int(origin is None)
     if origin is not None:
      origins[prefix+'acquired_origin']+=1
      origins[prefix+'recent_gap_lt2']+=int(gap<2)
      origins[prefix+'older_gap_ge2']+=int(gap>=2)
      origins[prefix+'older_correct']+=int(valid)
      origins[prefix+'older_wrong']+=int(gap>=2 and bit and (channel!='model' or cue) and not attempt['success'])
      origins[prefix+'different_cue']+=int(not cue)
      origins[prefix+'bit_mismatch']+=int(not bit)
      if phase=='late':
       before_cut=ledger[origin['event']]['completed_before']<48
       origins[prefix+'precut_origin']+=int(before_cut)
       origins[prefix+'precut_older_correct']+=int(before_cut and valid)
       origins[prefix+'postcut_older_correct']+=int(not before_cut and valid)
  if not reference and pc==14 and event.get('after') is not None:
   assert error is not None and error['ordinal']==ordinal
   address=event['after']['registers'][1]%len(cells);bit=event['after']['registers'][0]&1
   origin=dict(error,store_event=i,store_tick=event['tick'],address=address,bit=bit);cells[address]=origin;revisions.append(origin)
  if not reference and pc==15 and control['completion'] is not None:
   assert revisions and revisions[-1]['ordinal']==ordinal
   semantic=revisions[-1];assert semantic['bit']==int(control['completion']['entry']==16)
 assert ordinal==metric['served'] and sum(pc_counts.values())==metric['cpu']
 if not reference:
  assert uses==metric['own']['uses'] and revisions==metric['own']['revisions']
  assert actual_observed==metric['own']['observed_maps']
  assert sum(paths.values())==metric['cpu']
 cost_distribution=collections.Counter();unfinished=0
 for loop in loops.values():
  if not loop['pcs']:continue
  if loop['completed'] and not reference:
   entry=loop['pcs'][0];assert entry in (1,6,16)
   outcome='absence' if loop['absence'] else 'success' if loop['attempt']['success'] else 'error'
   model=entry==6;expected=(9 if outcome=='error' else 6) if model else (4 if outcome=='error' else 5)
   assert loop['cpu']==expected
   cost_distribution[('model' if model else 'fallback')+':'+outcome+':'+str(expected)]+=1
  elif not loop['completed']:unfinished+=loop['cpu']
 for k in ('served','successes','captured','penalty','cap_heat'):
  assert sum(v[k] for v in phases.values())==metric[k]
 maps=[]
 for observed in actual_observed:
  maps.append(dict(observed_cues=len(observed),complete=len(observed)==8,
   mask=sum(int(v)<<int(k) for k,v in observed.items()) if len(observed)==8 else None))
 known=set(actual_observed[0])&set(actual_observed[1])
 return dict(pc_cpu={str(k):v for k,v in sorted(pc_counts.items())},path_cpu=paths,
  decision_phases={k:dict(v) for k,v in phases.items()},completed_loop_costs=dict(cost_distribution),
  unfinished_cpu=unfinished,origin_counts=dict(origins),revisions=len(revisions),observed_maps=maps,
  observed_changed_cues=sum(actual_observed[0][k]!=actual_observed[1][k] for k in known),
  observed_unchanged_cues=sum(actual_observed[0][k]==actual_observed[1][k] for k in known),
  phase_comparison_unknown_cues=8-len(known))

def main():
 request=json.loads(Path(sys.argv[1]).read_bytes());assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==request['source_sha256']
 assert [x['seed'] for x in request['batches']]==SEEDS
 final=read(request['final'],8*M);results=[];aggregates={};totals=collections.Counter();decompositions=[]
 for item in request['batches']:
  seed=item['seed'];metrics=read(item['metrics'],8*M);assert metrics['seed']==seed
  assert [b['group'] for b in metrics['batches']]==list(GROUPS)
  assert [g['group'] for g in item['groups']]==list(GROUPS)
  for inputs,batch in zip(item['groups'],metrics['batches'],strict=True):
   group=inputs['group'];body=read(inputs['body'],64*M);assert body['seed']==seed and body['group']==group and body['error'] is None
   assert body['software_only'] is False and len(body['records'])==len(batch['rows'])
   for row,metric in zip(body['records'],batch['rows'],strict=True):
    assert row['descriptor']==metric['descriptor']
    value=trace(row,metric,group);result=dict(seed=seed,group=group,descriptor=row['descriptor'],trace=value,
     costs={k:metric[k] for k in ('completed','deaths','cpu','served','successes','captured','penalty','formation','fees','cap_heat','N','O','E')})
    results.append(result);totals['histories']+=1
    for k in ('cpu','served','successes','deaths'):totals[k]+=metric[k]
    key=('primary' if seed<1009900 else 'unseen')+':'+group+':'+label(row['descriptor'])
    dest=aggregates.setdefault(key,dict(histories=0,costs={},path_cpu={},origin_counts={},decision_phases={'warm':{},'late':{}},completed_loop_costs={}))
    dest['histories']+=1;add(dest['costs'],result['costs']);add(dest['path_cpu'],value['path_cpu']);add(dest['origin_counts'],value['origin_counts']);add(dest['completed_loop_costs'],value['completed_loop_costs'])
    for phase in ('warm','late'):add(dest['decision_phases'][phase],value['decision_phases'][phase])
   del body
  refs=metrics['batches'][-1]['rows']
  for intact,endpoint in zip(metrics['batches'][0]['rows'],metrics['endpoints'],strict=True):
   pieces={}
   for score in ('N','E'):
    ref=max(refs,key=lambda r:r[score])
    d={k:intact[k]-ref[k] for k in ('successes','captured','formation','cpu','penalty','fees')}
    gain=20*d['successes']-d['formation']-d['cpu']-d['penalty'] if score=='N' else d['captured']-d['formation']-d['cpu']-d['penalty']-d['fees']
    assert gain==endpoint[score]-endpoint['fixed_oracle_'+score]
    pieces[score]=dict(reference=ref['descriptor'],gain=gain,components=d)
   decompositions.append(dict(seed=seed,descriptor=intact['descriptor'],decomposition=pieces))
  del metrics
 assert totals['histories']==816 and len(results)==816 and len(decompositions)==144
 bank_decompositions=[]
 for d,expected in zip(DS,final['descriptors'],strict=True):
  banks={}
  for bank,seeds in (('primary',SEEDS[:8]),('unseen',SEEDS[8:])):
   rows=[r for r in decompositions if r['descriptor']==d and r['seed'] in seeds];assert len(rows)==8
   banks[bank]={}
   for score in ('N','E'):
    pieces={};gain=sum(r['decomposition'][score]['gain'] for r in rows)
    for row in rows:add(pieces,row['decomposition'][score]['components'])
    assert gain==expected['banks'][bank][score+'_oracle_gain']
    banks[bank][score]=dict(gain=gain,components=pieces)
  bank_decompositions.append(dict(descriptor=d,banks=banks))
 out=dict(verified=True,new_worlds=0,new_targets=0,original_histories=816,raw_origin_records_independently_reproduced=True,
  source_imports=[],scope='Independent retained-event origin/path diagnosis; existing closed full literal/custody proof reused, not a new physics referee or acceptance rescore',
  totals=dict(totals),aggregates=aggregates,all816=results,all144_oracle_decompositions=decompositions,all9_bank_decompositions=bank_decompositions,stage_credit=False)
 raw=enc(out);assert len(raw)<=8*M;Path(request['output']).write_bytes(raw)
 print(enc(dict(verified=True,extent=len(raw),sha256=hashlib.sha256(raw).hexdigest(),worlds=0,targets=0,histories=816)).decode())
if __name__=='__main__':main()
