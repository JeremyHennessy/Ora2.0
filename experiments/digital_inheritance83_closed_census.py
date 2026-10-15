"""Independent closed-data census: stdlib only, no producer/referee/metrics."""
import hashlib,json,math,sys
from fractions import Fraction
from pathlib import Path

def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode('ascii')
def read(spec):
 p=Path(spec['path']);assert p.is_absolute() and 0<spec['extent']<=8*1024**2
 raw=p.read_bytes();assert len(raw)==spec['extent'] and hashlib.sha256(raw).hexdigest()==spec['sha256']
 value=json.loads(raw);assert enc(value)==raw
 return value
def sign(values):
 wins=sum(v>0 for v in values);losses=sum(v<0 for v in values);n=wins+losses
 p=Fraction(sum(math.comb(n,k) for k in range(wins,n+1)),2**n) if n else Fraction(1)
 return dict(wins=wins,losses=losses,ties=len(values)-n,p=dict(numerator=p.numerator,denominator=p.denominator),passes=p<=Fraction(1,60))

def main():
 request=json.loads(Path(sys.argv[1]).read_bytes())
 assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==request['source_sha256']
 final=read(request['final']);assert final['complete_original_cells']==80
 assert [i['seed'] for i in request['batches']]==list(range(1008900,1008908))+list(range(1009100,1009108))
 modes=('variation','no_variation','inheritance_disabled','model_disabled','history_misbound')
 rows=[];by_seed={};by_mode={};by_cap={};totals={}
 for item in request['batches']:
  batch=read(item['metrics']);seed=item['seed'];assert batch['seed']==seed
  assert [m['mode'] for m in batch['metrics']]==list(modes)
  by_seed[seed]={}
  for m,proof_spec in zip(batch['metrics'],item['proofs'],strict=True):
   mode=m['mode'];proof=read(proof_spec);assert proof['physics']['verified']
   assert m['seed']==seed and proof['physics']['births']==m['births'] and proof['physics']['deaths']==m['deaths']
   assert m['paid_dispatches']==proof['physics']['ticks']
   children=proof['offspring'];capacities={0:2,**{c['child']:c['capacity'] for c in children}}
   functional={c['child'] for c in children if c['served_decisions']>=64 and m['post_expansion_served'][str(c['child'])]>=16 and c['paid_replacement_with_own_acquisition']}
   assert functional==set(m['functional_children']) and len(functional)==m['R']
   changed={c['child'] for c in children if c['capacity']!=capacities[c['parent']]}
   assert changed&functional==set(m['changed_functional_children'])
   for c in children:
    assert c['paid'] and c['blank']
    key=mode+':q'+str(c['capacity']);d=by_cap.setdefault(key,dict(births=0,functional=0,served64=0,post16=0,paid_replacement=0,own_food=0,deaths=0,right_censored=0,changed_headers=0))
    for k,v in dict(births=1,functional=c['child'] in functional,served64=c['served_decisions']>=64,
     post16=m['post_expansion_served'][str(c['child'])]>=16,paid_replacement=c['paid_replacement_with_own_acquisition'],
     own_food=c['own_resource_viable'],deaths=c['death'] is not None,right_censored=c['right_censored'],changed_headers=c['child'] in changed).items():d[k]+=v
   numerator=0
   for e in m['episodes']:
    f=int(e['paid_child'] in functional);assert e['child_fitness']==f
    value=3*((e['proposed']==8)-(e['proposed']==2))*f
    assert e['score']==value;numerator+=value
   assert numerator==m['S_numerator'] and m['S_denominator']==max(1,len(m['episodes']))
   assert 112+m['captured']-m['paid_actor_cost']==m['living_energy']
   assert sum(m['heat'].values())==proof['physics']['heat']
   successes=(m['captured']+m['heat']['cap_losses'])//20;failures=m['heat']['failed_packets']//20
   assert successes*20==m['captured']+m['heat']['cap_losses']
   assert successes+failures==len(m['actual_served_opportunities'])
   values=dict(R=m['R'],paid_dispatches=m['paid_dispatches'],resource_attempts=successes+failures,acquisitions=successes,
    captured=m['captured'],births=m['births'],deaths=m['deaths'],changed_paid_headers=len(changed),changed_functional=len(changed&functional),
    paid_actor_cost=m['paid_actor_cost'],retained_operating_surplus=m['retained_operating_surplus'],heat=sum(m['heat'].values()),
    offered=m['offered'],admitted=m['admitted'],rejected=m['rejected'],uniform_proposals=m['accepted_uniform_proposals'],
    gate0_episodes=m['gate0_episodes'],ended_before_expansion=int(m['paid_dispatches']<1536),
    max_generation=max((c['generation'] for c in children),default=0),
    right_censored_children=sum(c['right_censored'] for c in children))
   rows.append(dict(seed=seed,mode=mode,**values));by_seed[seed][mode]=dict(R=m['R'],S=Fraction(numerator,m['S_denominator']))
   d=by_mode.setdefault(mode,{k:0 for k in values})
   for k,v in values.items():
    if k=='max_generation':d[k]=max(d[k],v)
    else:d[k]+=v;totals[k]=totals.get(k,0)+v
 for key,control,field in [('R_no_variation','no_variation','R'),('R_inheritance_disabled','inheritance_disabled','R'),('S_inheritance_disabled','inheritance_disabled','S')]:
  actual=sign([v['variation'][field]-v[control][field] for v in by_seed.values()])
  assert all(actual[k]==final['paired_sign_tests'][key][k] for k in actual)
 for name,seeds in [('primary',range(1008900,1008908)),('unseen',range(1009100,1009108))]:
  bank=final['banks'][name]
  for key,control,field in [('R_no_variation','no_variation','R'),('R_inheritance_disabled','inheritance_disabled','R'),('S_inheritance_disabled','inheritance_disabled','S')]:
   value=sum((by_seed[s]['variation'][field]-by_seed[s][control][field] for s in seeds),Fraction(0))
   assert dict(numerator=value.numerator,denominator=value.denominator)==bank['contrasts'][key]
  for mode in modes:
   assert sum(r['retained_operating_surplus'] for r in rows if r['seed'] in seeds and r['mode']==mode)==bank['retained_operating_surplus'][mode]
 value=dict(verified=True,original_cells=80,seed_count=16,new_worlds=0,target_queries=0,
  scope='Independent closed all-roster accounting/R/S/sign diagnosis; no new thresholds or causal attribution',
  numeric_criteria_met=final['registered_numeric_criteria_met'],totals=totals,by_mode=by_mode,by_capacity=by_cap,
  all80=rows,paired_sign_tests=final['paired_sign_tests'],banks=final['banks'],actual_common_opportunities=final['actual_common_opportunities'],
  scientific_scope='Inherited capacity under supplied machinery only; no new own-history attribution from endpoints')
 data=enc(value);assert len(data)<=2*1024**2
 path=Path(request['output']);assert path.exists() and path.stat().st_size==0
 with path.open('wb') as f:f.write(data)
 print(enc(dict(verified=True,extent=len(data),sha256=hashlib.sha256(data).hexdigest(),new_worlds=0,target_queries=0)).decode())

if __name__=='__main__':main()
