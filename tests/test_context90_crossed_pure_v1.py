"""Seven NEW groups; synthetic arithmetic/proofs, no World or OS entropy."""
import ast,copy,unittest
from pathlib import Path
from experiments import digital_context90_crossed_registry_v1 as r
from experiments import digital_context90_crossed_programme_v1 as p
from experiments import digital_context90_crossed_metrics_v1 as m
BASE=Path(__file__).resolve().parent

class Pure(unittest.TestCase):
 def test_new_full_roster(self):
  self.assertEqual(len(p.ACTORS),19);self.assertEqual([len(v) for v in p.BATCHES.values()],[6,3,5,5])
  old=BASE/'qualified-programme.py'
  if not old.exists():old=BASE.parent/'experiments/digital_temporal89_programme.py'
  tree=ast.parse(old.read_bytes());ref=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REFERENCES' for t in n.targets));self.assertEqual(p.REFERENCES,ast.literal_eval(ref))
  for q in (2,4,8):
   source=p.programme('overwrite'+str(q));self.assertEqual(len(source),13);self.assertEqual(3*len(source)+q+8,47+q)
   self.assertEqual(len(p.programme('q'+str(q)+':A')),29)
  for role in p.ACTORS:
   x=p.programme(role);x[0][0]=99;self.assertNotEqual(p.programme(role)[0][0],99)
 def test_new_factor_decoder(self):
  for c in range(8):
   for a in range(256):
    bit=(a>>c)&1;cs=[x for x in range(256) if x!=a and (x>>c)&1==bit];bs=[x for x in range(256) if (x>>c)&1!=bit]
    self.assertEqual((len(cs),len(bs)),(127,128))
    for ci in (0,63,126):
     for bi in (0,64,127):
      rank=(((c*256+a)*127+ci)*128+bi);self.assertEqual(r.decode_rank(rank),dict(c=c,A=a,C=cs[ci],B=bs[bi]))
  for bad in (True,-1,r.FAMILY):
   with self.assertRaises(ValueError):r.decode_rank(bad)
 def test_new_entropy_arithmetic(self):
  limit=(2**256//r.FAMILY)*r.FAMILY
  word=lambda n:format(n,'064x')
  self.assertEqual(r.decode_words([word(0)]),0);self.assertEqual(r.decode_words([word(limit-1)]),r.FAMILY-1);self.assertEqual(r.decode_words([word(limit),word(1)]),1)
  for words in ([],[word(2**256-1)]*8,[word(0),word(1)],['F'*64],[False]):
   with self.assertRaises(ValueError):r.decode_words(words)
  t=r.tuple_for('software',0);self.assertEqual(t,dict(c=0,A=45,C=213,B=154));r.definition(t)
  with self.assertRaises(ValueError):r.tuple_for('primary',0)
  with self.assertRaises(ValueError):r.mask(dict(t,A=True),'AA',0)
 def req(self,mode,role):
  spec=dict(path=str(Path.cwd()/'SYNTHETIC'),extent=1,sha256='0'*64);kind=r.kind(role)
  inputs=None if kind=='sample' else dict(body=spec if kind=='audit' else None,draw=spec if mode=='primary' else None)
  return dict(configuration=r.config(mode),source_files={},source_sha='0'*64,config_sha='0'*64,role=role,kind=kind,input=inputs,grant={},seal='0'*64)
 def test_new_graph_scope(self):
  for mode,n in (('software',48),('primary',433)):
   roles=r.roles(mode);self.assertEqual(len(roles),n);self.assertEqual(len(set(roles)),n)
   for role in roles:self.assertEqual(r.scope(self.req(mode,role)),r.kind(role))
   request=self.req(mode,roles[-1]);request['configuration']['startup']=True
   with self.assertRaises(ValueError):r.scope(request)
  with self.assertRaises(ValueError):r.scope(self.req('software','primary:sampler'))
  for seed in ('1010600','1010800'):self.assertNotIn(seed,str(r.config('primary')))
  self.assertEqual([r.capacity('original:0:AA:'+b+':generate')//r.M for b in p.BATCHES],[56,28,44,44])
 def synthetic(self,n):
  rows=[]
  for i in range(n):
   for c in r.CELLS:
    for role in m.ACTORS:
     learner=role.startswith('q');diag=c in ('AA','CC');q=15 if learner and diag else 5 if learner else 10;origin=14 if learner and diag else 4 if learner else 0
     rows.append(dict(index=i,cell=c,role=role,Q=q,R=origin,N=-1 if learner else 10,O=-2 if learner else 10,E=-3 if learner else 10))
  return rows
 def test_new_complete_metrics(self):
  rows=self.synthetic(9);v=m.aggregate(rows,'primary');self.assertEqual(v['family_tests'],15)
  for q in v['capacities']:
   self.assertTrue(q['functional']);self.assertFalse(any(q['paid_advantage'].values()));self.assertEqual(q['tests']['Q']['p'],[1,512])
  self.assertFalse(m.aggregate(self.synthetic(1),'software')['confirmatory'])
  for bad in (rows[:-1],rows+[rows[0]],copy.deepcopy(rows)):
   if len(bad)==len(rows):bad[0]['Q']=True
   with self.assertRaises(ValueError):m.aggregate(bad,'primary')
 def test_new_sign_family(self):
  self.assertEqual(m.sign([1]*9)['p'],[1,512]);self.assertTrue(m.sign([1]*9)['passes']);self.assertFalse(m.sign([1]*8+[0])['passes']);self.assertEqual(m.sign([0]*9)['p'],[1,1])
 def test_new_prefix_integrity(self):
  a=dict(role='fixed0',programme=[[7,2,1]],state=dict(events=[dict(tick=1),dict(tick=2)]),ledger=[dict(trial=96),dict(trial=97)])
  b=copy.deepcopy(a);b['state']['events'][1]['tick']=999;self.assertTrue(m.prefix_pair(a,b));b['state']['events'][0]['tick']=999
  with self.assertRaises(ValueError):m.prefix_pair(a,b)
  a['ledger'][-1]['trial']=96;b=copy.deepcopy(a);b['state']['food']={}
  with self.assertRaises(ValueError):m.prefix_pair(a,b)

if __name__=='__main__':unittest.main()
