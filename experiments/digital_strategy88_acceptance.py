"""Separate complete-denominator functional arithmetic; no execution admission."""
from fractions import Fraction
from math import comb
PRIMARY=tuple(range(1010100,1010106));UNSEEN=tuple(range(1010300,1010306))
FIELDS={'seed','prior','completed','common','correct','reset','misbound','older_uses','observed_mixed','whole_correct','explore_correct','oracle_correct','N','E','C','oracle_N','oracle_E'}
def tail(w,l):
 n=w+l;return Fraction(sum(comb(n,k) for k in range(w,n+1)),2**n) if n else Fraction(1)
def interpret(rows):
 assert type(rows) is list and len(rows)==48
 cells={}
 for r in rows:
  assert type(r) is dict and set(r)==FIELDS and all(type(v) is int for v in r.values())
  assert r['seed'] in PRIMARY+UNSEEN and r['prior'] in range(4)
  assert 0<=r['common']<=12 and 0<=r['completed']<=60 and 0<=r['C']<=512
  assert all(0<=r[k]<=r['common'] for k in ('correct','reset','misbound','older_uses'))
  assert all(0<=r[k]<=60 for k in ('whole_correct','explore_correct','oracle_correct')) and r['observed_mixed'] in (0,1)
  key=(r['seed'],r['prior']);assert key not in cells;cells[key]=r
 assert set(cells)=={(s,i) for s in PRIMARY+UNSEEN for i in range(4)}
 results=[]
 for prior in range(4):
  current=[cells[s,prior] for s in PRIMARY+UNSEEN];deltas=[r['correct']-r['reset'] for r in current]
  w=sum(x>0 for x in deltas);l=sum(x<0 for x in deltas);p=tail(w,l);banks={}
  for name,seeds in (('primary',PRIMARY),('unseen',UNSEEN)):
   rs=[cells[s,prior] for s in seeds]
   older=[r for r in rs if r['seed']%100>=2 and r['observed_mixed']]
   values=dict(all_complete=all(r['completed']==60 for r in rs),common=sum(r['common'] for r in rs),
    reset_gain=sum(r['correct']-r['reset'] for r in rs),explore_gain=sum(r['whole_correct']-r['explore_correct'] for r in rs),
    older_uses=sum(r['older_uses'] for r in older),origin_contexts=sum(r['older_uses']>0 for r in older),
    oracle_correct_gain=sum(r['whole_correct']-r['oracle_correct'] for r in rs),N_oracle_gain=sum(r['N']-r['oracle_N'] for r in rs),
    E_oracle_gain=sum(r['E']-r['oracle_E'] for r in rs),charged_cost=sum(r['C'] for r in rs),correct=sum(r['whole_correct'] for r in rs))
   values['functional_gates']=values['all_complete'] and values['common']>=60 and values['reset_gain']>=6 and values['explore_gain']>=6 and values['older_uses']>=6 and values['origin_contexts']>=3
   values['correct_per_paid_C']=str(Fraction(values['correct'],max(1,values['charged_cost'])))
   banks[name]=values
  functional=p<=Fraction(1,80) and all(b['functional_gates'] for b in banks.values())
  results.append(dict(prior=prior,banks=banks,paired_sign=dict(wins=w,losses=l,ties=12-w-l,p=str(p),passes=p<=Fraction(1,80)),
   functional_selection=functional,strong_reference_value=functional and all(b['oracle_correct_gain']>=1 for b in banks.values()),
   nominal_costed_value=functional and all(b['N_oracle_gain']>0 for b in banks.values()),
   finite_cohort_energy_gain=all(b['E_oracle_gain']>0 for b in banks.values())))
 return dict(priors=results,robust_functional_selection=all(r['functional_selection'] for r in results),
  robust_strong_reference_value=all(r['strong_reference_value'] for r in results),family_size=4,threshold='1/80',
  logical_originals=312,scientific_geneses_if_complete=624,numeric_interface_only=True,execution_admission=False,
  requires_external_full_literal_parity_native_source_grant_archive=True,energy_population_claim=False,stage_credit=False)
