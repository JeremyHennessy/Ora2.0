"""Stdlib-only complete closed metric-table cross-check; zero Worlds or targets."""
import hashlib,json,sys
from fractions import Fraction
from math import comb
from pathlib import Path
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def read(spec):
 p=Path(spec['path']);data=p.read_bytes();assert 0<len(data)==spec['extent']<=8*1024**2
 assert hashlib.sha256(data).hexdigest()==spec['sha256'];v=json.loads(data);assert enc(v)==data;return v
def main():
 q=json.loads(Path(sys.argv[1]).read_bytes());assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==q['source_sha']
 seeds=tuple(range(1010100,1010106))+tuple(range(1010300,1010306));assert [s['seed'] for s in q['batches']]==list(seeds)
 final=read(q['final']);totals={};arms={};endpoints=[];physical=0;minimum=512;maximum=0
 fields=('completed','served','successes','deaths','cpu','formation','penalty','fees','C','captured','cap_heat','failed_packet_heat','heat','living','constructor_remaining','food','offered','admitted','rejected','absence','N','O','E')
 for s in q['batches']:
  v=read(s['spec']);assert v['seed']==s['seed'] and v['software_only'] is False and len(v['rows'])==26
  assert len({r['role'] for r in v['rows']})==26 and len(v['endpoints'])==4
  for r in v['rows']:
   assert r['C']==r['formation']+r['cpu']+r['penalty']+r['fees']<=512
   assert r['N']==20*r['successes']-r['formation']-r['cpu']-r['penalty']
   assert r['O']==r['captured']-r['cpu']-r['penalty'] and r['E']==r['O']-r['formation']-r['fees']
   assert r['heat']+r['living']+r['constructor_remaining']+20*r['food']==1536+20*r['admitted']
   assert r['offered']==r['admitted']+r['rejected'];physical+=1;minimum=min(minimum,r['C']);maximum=max(maximum,r['C'])
   arm=r['role'].split(':')[0] if ':' in r['role'] else 'efficient_references';dest=arms.setdefault(arm,{})
   for k in fields:totals[k]=totals.get(k,0)+r[k];dest[k]=dest.get(k,0)+r[k]
  endpoints.extend(v['endpoints']);del v
 assert physical==312 and len(endpoints)==48
 priors=[]
 for i,expected in enumerate(final['priors']):
  rows=[r for r in endpoints if r['prior']==i];assert len(rows)==12
  w=sum(r['correct']>r['reset'] for r in rows);l=sum(r['correct']<r['reset'] for r in rows);n=w+l
  p=Fraction(sum(comb(n,k) for k in range(w,n+1)),2**n) if n else Fraction(1)
  assert expected['paired_sign']==dict(wins=w,losses=l,ties=12-w-l,p=str(p),passes=p<=Fraction(1,80))
  banks={}
  for name,ss in (('primary',seeds[:6]),('unseen',seeds[6:])):
   rs=[r for r in rows if r['seed'] in ss];older=[r for r in rs if r['seed']%100>=2 and r['observed_mixed']]
   b=dict(all_complete=all(r['completed']==60 for r in rs),common=sum(r['common'] for r in rs),reset_gain=sum(r['correct']-r['reset'] for r in rs),
    explore_gain=sum(r['whole_correct']-r['explore_correct'] for r in rs),older_uses=sum(r['older_uses'] for r in older),origin_contexts=sum(r['older_uses']>0 for r in older),
    oracle_correct_gain=sum(r['whole_correct']-r['oracle_correct'] for r in rs),N_oracle_gain=sum(r['N']-r['oracle_N'] for r in rs),E_oracle_gain=sum(r['E']-r['oracle_E'] for r in rs),
    charged_cost=sum(r['C'] for r in rs),correct=sum(r['whole_correct'] for r in rs))
   b['functional_gates']=b['all_complete'] and b['common']>=60 and b['reset_gain']>=6 and b['explore_gain']>=6 and b['older_uses']>=6 and b['origin_contexts']>=3
   b['correct_per_paid_C']=str(Fraction(b['correct'],max(1,b['charged_cost'])));assert b==expected['banks'][name];banks[name]=b
  functional=p<=Fraction(1,80) and all(b['functional_gates'] for b in banks.values())
  result=dict(prior=i,banks=banks,paired_sign=expected['paired_sign'],functional_selection=functional,
   strong_reference_value=functional and all(b['oracle_correct_gain']>=1 for b in banks.values()),nominal_costed_value=functional and all(b['N_oracle_gain']>0 for b in banks.values()),finite_cohort_energy_gain=all(b['E_oracle_gain']>0 for b in banks.values()))
  assert result==expected;priors.append(result)
 assert final['robust_functional_selection']==all(r['functional_selection'] for r in priors)
 assert final['robust_strong_reference_value']==all(r['strong_reference_value'] for r in priors)
 out=dict(verified=True,original_histories=physical,new_worlds=0,new_targets=0,scope='Metric-table census,not raw physics/origin replay',totals=totals,by_arm=arms,charged_cost_range=[minimum,maximum],priors=priors,
  robust_functional_selection=final['robust_functional_selection'],robust_strong_reference_value=final['robust_strong_reference_value'],stage_credit=False)
 data=enc(out);assert len(data)<=2*1024**2;Path(q['output']).write_bytes(data)
 print(enc(dict(verified=True,worlds=0,targets=0,histories=physical,extent=len(data),sha256=hashlib.sha256(data).hexdigest())).decode())
if __name__=='__main__':main()
