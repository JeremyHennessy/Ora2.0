"""Complete-denominator arithmetic only; no task/target/metric imports or admission."""
from fractions import Fraction
from math import comb

PRIMARY=tuple(range(1010500,1010508));UNSEEN=tuple(range(1010700,1010708))
ARMS=('intact','credit_erased','recall_disabled','model_disabled','update_frozen')
REFERENCES=('fixed0','fixed1','retained_cue','retained_inverse','current_distractor','current_inverse','alternation0','alternation1','latest0','latest1')
ROLES=tuple(f'q{q}:{a}' for q in (2,4,8) for a in ARMS)+REFERENCES

def integer(value,lo,hi):assert type(value) is int and lo<=value<=hi

def sign(values):
 wins=sum(x>0 for x in values);losses=sum(x<0 for x in values);ties=len(values)-wins-losses;n=wins+losses
 p=Fraction(sum(comb(n,k) for k in range(wins,n+1)),2**n)
 return dict(wins=wins,losses=losses,ties=ties,p=str(p),passes=p<=Fraction(1,240))

def interpret(contexts):
 assert type(contexts) is list and len(contexts)==16
 assert all(type(c['seed']) is int for c in contexts)
 assert {c['seed'] for c in contexts}==set(PRIMARY+UNSEEN) and len({c['seed'] for c in contexts})==16
 by={c['seed']:c for c in contexts};allend={}
 for seed,c in by.items():
  assert c['execution_admission'] is False and c['source_free'] is True
  assert c['roles']==list(ROLES) and type(c['rows']) is list and len(c['rows'])==25
  assert {r['role'] for r in c['rows']}==set(ROLES) and len({r['role'] for r in c['rows']})==25
  actors={r['role']:r for r in c['rows']}
  for row in actors.values():
   assert row['execution_admission'] is False and row['source_free'] is True
   integer(row['completed'],0,60);integer(row['physical']['correct'],0,60)
   assert type(row['trials']) is list and len(row['trials'])<=60
   assert len({t['trial'] for t in row['trials']})==len(row['trials'])
   assert sorted(t['trial'] for t in row['trials'])==list(range(len(row['trials'])))
   for t in row['trials']:
    integer(t['trial'],0,59);integer(t['completed'],0,1);integer(t['served'],0,1);integer(t['success'],0,t['served'])
    integer(t['cue'],0,7)
    for key in ('pre','post'):
     if t[key] is not None:integer(t[key],0,7)
     if t['completed']:assert t[key] is not None
   assert row['completed']==sum(t['completed'] for t in row['trials'])
   assert row['physical']['correct']==sum(t['success'] for t in row['trials'])
  assert type(c['endpoints']) is list and len(c['endpoints'])==3
  assert [e['capacity'] for e in c['endpoints']]==[2,4,8]
  for e in c['endpoints']:
   assert type(e['seed']) is int and e['seed']==seed
   integer(e['capacity'],2,8);integer(e['intact_completed'],0,60);integer(e['common_count'],0,12)
   integer(e['older_changed_uses'],0,12);integer(e['whole_correct'],0,60);integer(e['reference_oracle_correct'],0,60)
   assert set(e['common_correct'])==set(ARMS)
   for a in ARMS:integer(e['common_correct'][a],0,e['common_count'])
   q=e['capacity'];family={a:actors[f'q{q}:{a}'] for a in ARMS}
   tables={a:{(t['trial'],t['cue'],t['pre'],t['post']):t for t in r['trials'] if t['trial']>=48 and t['completed'] and t['served']} for a,r in family.items()}
   common=set.intersection(*(set(t) for t in tables.values()))
   assert e['common_keys']==[list(k) for k in sorted(common)] and e['common_count']==len(common)
   assert all(e['common_correct'][a]==sum(tables[a][k]['success'] for k in common) for a in ARMS)
   assert e['intact_completed']==family['intact']['completed'] and e['whole_correct']==family['intact']['physical']['correct']
   assert e['older_changed_uses']==sum(u['trial']>=48 for u in family['intact']['older_changed_uses'])
   assert e['reference_oracle_correct']==max(actors[r]['physical']['correct'] for r in REFERENCES)
   allend[seed,e['capacity']]=e
 results=[]
 for q in (2,4,8):
  signs={a:sign([allend[s,q]['common_correct']['intact']-allend[s,q]['common_correct'][a] for s in PRIMARY+UNSEEN]) for a in ARMS[1:]}
  banks={}
  for name,seeds in (('primary',PRIMARY),('unseen',UNSEEN)):
   rows=[allend[s,q] for s in seeds]
   gains={a:sum(r['common_correct']['intact']-r['common_correct'][a] for r in rows) for a in ARMS[1:]}
   common=sum(r['common_count'] for r in rows);finished=sum(r['intact_completed']==60 for r in rows)
   uses=sum(r['older_changed_uses'] for r in rows)
   independent=sum(allend[s,q]['older_changed_uses']>0 for s in seeds[2:])
   oracle_gain=sum(r['whole_correct']-r['reference_oracle_correct'] for r in rows)
   flags=dict(intact_complete=finished==8,common_opportunities=common>=80,all_control_gains=all(v>=8 for v in gains.values()),
    changed_origin_use=uses>=4 and independent>=3,strong_reference=oracle_gain>=8)
   banks[name]=dict(finished=finished,common=common,control_gains=gains,older_changed_uses=uses,
     independent_contexts_with_uses=independent,whole_correct_oracle_gain=oracle_gain,gates=flags,passes=all(flags.values()))
  causal=all(s['passes'] for s in signs.values())
  results.append(dict(capacity=q,signs=signs,banks=banks,causal_sign_family=causal,
    functional_acceptance=causal and all(b['passes'] for b in banks.values())))
 return dict(verified=True,version='TEMPORAL89-v1',scope='Frozen capacity-specific functional vector; external physics/custody mandatory',
  capacity_results=results,confirmatory_tests=12,threshold='1/240',all_contexts=16,execution_admission=False,
  retained_energy_superiority_registered=False,architecture_supplied=True,evolved_architecture=False,stage_credit=False)
