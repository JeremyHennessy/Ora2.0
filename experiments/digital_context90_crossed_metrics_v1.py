"""Independent fixed metrics over validated literal/origin proof rows only."""
from fractions import Fraction
from math import comb
CELLS=('AA','AC','CA','CC')
REFERENCES=('overwrite2','overwrite4','overwrite8','fixed0','fixed1','retained_cue','retained_inverse','current_distractor','current_inverse','alternation0','alternation1','latest0','latest1')
ACTORS=tuple('q'+str(q)+':'+e for q in (2,4,8) for e in ('A','B'))+REFERENCES

def integer(v,lo=None,hi=None):
 if type(v) is not int or lo is not None and v<lo or hi is not None and v>hi:raise ValueError('metric integer')
 return v

def sign(values):
 for v in values:integer(v)
 w=sum(v>0 for v in values);l=sum(v<0 for v in values);n=w+l
 p=Fraction(sum(comb(n,k) for k in range(w,n+1)),2**n) if n else Fraction(1)
 return dict(wins=w,losses=l,ties=len(values)-n,p=[p.numerator,p.denominator],threshold=[1,300],passes=p<=Fraction(1,300))

def aggregate(rows,mode):
 if mode not in ('software','primary') or type(rows) is not list:raise ValueError('metric scope')
 n=1 if mode=='software' else 9;index={}
 for row in rows:
  if type(row) is not dict or set(row)!= {'index','cell','role','Q','R','N','O','E'}:raise ValueError('metric row')
  i=integer(row['index'],0,n-1);cell=row['cell'];role=row['role']
  if cell not in CELLS or role not in ACTORS:raise ValueError('metric role')
  integer(row['Q'],0,15);integer(row['R'],0,row['Q'])
  for metric in ('N','O','E'):integer(row[metric])
  key=(i,cell,role)
  if key in index:raise ValueError('duplicate proof row')
  index[key]=row
 if len(index)!=n*4*19:raise ValueError('complete planned cohort required')
 capacities=[]
 for q in (2,4,8):
  ds={k:[] for k in ('Q','R','N','O','E')};dq=dr=gain=0
  def value(i,c,e,k):return index[i,c,'q'+str(q)+':'+e][k]
  def best(i,c,k):return max(index[i,c,r][k] for r in REFERENCES)
  for i in range(n):
   for k in ('Q','R'):
    ds[k].append(min(value(i,'AA',e,k)+value(i,'CC',e,k)-value(i,'AC',e,k)-value(i,'CA',e,k) for e in ('A','B')))
   for k in ('N','O','E'):ds[k].append(sum(min(value(i,c,e,k) for e in ('A','B'))-best(i,c,k) for c in CELLS))
   for c in ('AA','CC'):
    one=min(value(i,c,e,'Q') for e in ('A','B'));dq+=one;dr+=min(value(i,c,e,'R') for e in ('A','B'));gain+=one-best(i,c,'Q')
  tests={k:sign(v) for k,v in ds.items()};confirm=mode=='primary'
  functional=confirm and tests['Q']['passes'] and tests['R']['passes'] and dq>=216 and dr>=126 and gain>=9
  capacities.append(dict(q=q,differences=ds,tests=tests,diagonal_Q=dq,diagonal_R=dr,strong_Q_gain=gain,functional=functional,paid_advantage={k:confirm and tests[k]['passes'] and sum(ds[k])>0 for k in ('N','O','E')}))
 return dict(software_only=mode=='software',confirmatory=mode=='primary',family_tests=15,tuple_units=n,capacities=capacities,stage_credit=False)

def prefix_pair(left,right):
 def project(row):
  if type(row) is not dict or not {'role','programme','state','ledger'}<=set(row):raise ValueError('prefix record')
  events=row['state']['events'];ledger=row['ledger']
  if len(events)!=len(ledger):raise ValueError('prefix event/ledger extent')
  pairs=[(e,l) for e,l in zip(events,ledger) if l['trial']<=96]
  terminal=row['state'] if not ledger or ledger[-1]['trial']<=96 else None
  return row['role'],row['programme'],pairs,terminal
 if project(left)!=project(right):raise ValueError('complete physical/task prefix mismatch')
 return True
