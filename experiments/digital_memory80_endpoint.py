"""Producer-free paid birth/blank-state/own-resource endpoint; not a physics referee."""
def paid_viable_children(state):
 events=state['events'];writes={};children=[]
 for event in events:
  for w in event.get('writes',[]):
   assert w['write_id'] not in writes;writes[w['write_id']]=w
  if 'birth' not in event:continue
  birth=event['birth'];child=birth['child'];q=child['code'][1][0]
  assert q in (2,4,8) and len(child['state_units'])==q+8
  assert child['memory']==[0]*q and child['registers']==[0,0] and child['pc']==0 and child['feedback']==0 and child['energy']==112
  assert child['parent']==event['actor'] and not child['nursery'] and child['pending'] is None
  assert birth['state_energy']==q+8 and birth['startup_energy']==112 and birth['release_energy']==2
  assert event['kind']=='ordinary' and event['decoded'][0]==12
  residual=event['energy_before']-1-(q+8+112+2)
  assert birth['parent_energy_after_division']==residual and residual>=0
  if 'after' in event:assert event['after']['energy']==residual
  else:assert event['death']['dissipated']==residual
  copied=[writes[i] for i in birth['write_ids']]
  assert child['code']==[[w['value'],w['unit']] for w in copied]
  assert len(copied)==len(child['code']) and [w['index'] for w in copied]==list(range(len(copied)))
  assert all(w['value']==w['source_value'] or w['index']==1 and w['value'] in (2,4,8) for w in copied)
  later=[e for e in events if e['actor']==child['id'] and e['tick']>event['tick'] and e.get('attempt',{}).get('success')==1 and e.get('captured',0)>0]
  children.append(dict(child=child['id'],parent=child['parent'],generation=child['generation'],capacity=q,paid=True,blank=True,own_resource_viable=bool(later)))
 return children
