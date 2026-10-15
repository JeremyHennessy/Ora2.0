"""Independent closed metric census; stdlib only, no source/VM/referee/metric imports."""
import hashlib,json,math,sys
from fractions import Fraction
from pathlib import Path

def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode('ascii')
def read(spec):
 p=Path(spec['path']);assert p.is_absolute() and 0<spec['extent']<=8*1024**2
 raw=p.read_bytes();assert len(raw)==spec['extent'] and hashlib.sha256(raw).hexdigest()==spec['sha256']
 value=json.loads(raw);assert enc(value)==raw;return value
def sign(values):
 w=sum(v>0 for v in values);l=sum(v<0 for v in values);n=w+l
 p=Fraction(sum(math.comb(n,k) for k in range(w,n+1)),2**n) if n else Fraction(1)
 return dict(wins=w,losses=l,ties=16-w-l,p=str(p),passes=p<=Fraction(1,180))
def main():
 request=json.loads(Path(sys.argv[1]).read_bytes())
 assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==request['source_sha256']
 final=read(request['final']);assert final['logical_original_histories']==816
 seeds=list(range(1009700,1009708))+list(range(1009900,1009908))
 ds=[[q,r] for q in (2,4,8) for r in ('fallback0','model','fallback1')]
 groups=('intact','model_erased','model_misbound','fallback_misbound','history_disabled','references')
 assert [x['seed'] for x in request['batches']]==seeds
 totals={};by_group={};endpoints=[];intact=[];sources={};observed=[]
 for item in request['batches']:
  value=read(item['metrics']);assert value['seed']==item['seed'] and len(value['endpoints'])==9
  assert [x['group'] for x in value['batches']]==list(groups)
  endpoints.extend(value['endpoints'])
  references=value['batches'][-1]['rows'];on=max(x['N'] for x in references);oe=max(x['E'] for x in references)
  for e in value['endpoints']:assert e['fixed_oracle_N']==on and e['fixed_oracle_E']==oe
  for batch in value['batches']:
   group=batch['group'];assert len(batch['rows'])==(6 if group=='references' else 9)
   for row in batch['rows']:
    assert row['N']==20*row['successes']-row['formation']-row['cpu']-row['penalty']
    assert row['O']==row['captured']-row['cpu']-row['penalty']
    assert row['E']==row['O']-row['formation']-row['fees']
    assert row['fees'] in (0,16)
    assert 20*row['successes']==row['captured']+row['cap_heat']
    assert 20*(row['served']-row['successes'])==row['failed_packet_heat']
    assert row['offered']==row['admitted']+row['rejected']
    assert row['heat']+row['living']+row['constructor_remaining']+20*row['food']==1536+20*row['admitted']
    death_heat=row['heat']-row['formation']-row['cpu']-row['penalty']-row['fees']-row['cap_heat']-row['failed_packet_heat']
    assert death_heat>=0 and row['living']+death_heat==112+row['O']
    counts={k:row[k] for k in ('cpu','served','successes','deaths','captured','penalty','formation','fees','cap_heat','failed_packet_heat','heat','living','constructor_remaining','food','offered','admitted','rejected','N','O','E')}
    counts.update(histories=1,completed60=int(row['completed']==60),death_heat=death_heat)
    for dest in (totals,by_group.setdefault(group,{})):
     for k,v in counts.items():dest[k]=dest.get(k,0)+v
    if group=='intact':
     intact.append(dict(seed=item['seed'],descriptor=row['descriptor'],completed=row['completed'],deaths=row['deaths']))
     observed.append(dict(seed=item['seed'],descriptor=row['descriptor'],observed_maps=row['own']['observed_maps'],personally_sensed_maps=row['own']['personally_sensed_maps']))
  del value
 assert totals['histories']==816 and len(endpoints)==144
 results=[]
 for d,expected in zip(ds,final['descriptors'],strict=True):
  rows=[x for x in endpoints if x['descriptor']==d];assert [r['seed'] for r in rows]==seeds
  paired=sign([r['correct_intact']-r['correct_joint'] for r in rows]);assert paired==expected['joint_sign']
  banks={}
  for bank,rs in (('primary',rows[:8]),('unseen',rows[8:])):
   n=sum(r['N']-r['fixed_oracle_N'] for r in rs);e=sum(r['E']-r['fixed_oracle_E'] for r in rs)
   common=sum(r['common'] for r in rs);delta=sum(r['correct_intact']-r['correct_joint'] for r in rs)
   older=sum(r['older_uses'] for r in rs if r['observed_mixed']);origins=sum(bool(r['observed_mixed'] and r['older_uses']) for r in rs)
   all_complete=all(r['completed']==60 for r in rs)
   mech=all_complete and common>=80 and delta>=8 and older>=4 and origins>=3 and n>=16
   actual=dict(N_oracle_gain=n,E_oracle_gain=e,common=common,joint_gain=delta,older_uses=older,origin_contexts=origins,all_intact_complete=all_complete,mechanism_gates=mech)
   for key in actual:
    assert actual[key]==(expected['banks'][bank]['deltas']['joint'] if key=='joint_gain' else expected['banks'][bank][key])
   banks[bank]=actual
  mechanistic=paired['passes'] and all(b['mechanism_gates'] for b in banks.values())
  energy=mechanistic and all(b['E_oracle_gain']>0 for b in banks.values())
  assert mechanistic==expected['arithmetic_mechanistic_paid_choice'] and energy==expected['arithmetic_finite_cohort_net_energy']
  results.append(dict(descriptor=d,banks=banks,joint_sign=paired,mechanistic=mechanistic,net_energy=energy))
 out=dict(verified=True,new_worlds=0,target_queries=0,original_histories=816,totals=totals,by_group=by_group,
  intact_completion=intact,observed_maps=observed,all9=results,all_mechanistic_false=all(not r['mechanistic'] for r in results),
  all_energy_false=all(not r['net_energy'] for r in results),scope='Independent metric-table accounting and all-nine arithmetic; not an additional raw-physics referee or independent origin rederivation',stage_credit=False)
 raw=enc(out);assert len(raw)<=2*1024**2;Path(request['output']).write_bytes(raw)
 print(enc(dict(verified=True,extent=len(raw),sha256=hashlib.sha256(raw).hexdigest(),worlds=0,targets=0)).decode())
if __name__=='__main__':main()
