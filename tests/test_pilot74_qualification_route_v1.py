"""New-only admission/dispatch/source checks; no World or guardian execution."""
import copy,hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import digital_pilot74_qualification_admission_v1 as q
from experiments import digital_pilot74_lock_scope_v1 as scope
from experiments import digital_pilot74_qualification_controller_v1 as c

class Route(unittest.TestCase):
 def fixture(self):
  r=dict(schema=q.SCHEMA,mode=q.MODE,revision='a'*40,source_sha256='b'*64,configuration_sha256='c'*64,configuration=q.requests.CONFIG,root='D:/OraLab/runs/fresh/workload',operator_lock=dict(path='D:/OraLab/runs/fresh/qualification-owner.lock'),reviews={k:{} for k in q.REVIEWS},qualification=dict(plan={},grant={},preserved_failure_lock={}))
  p=dict(schema='PILOT74-WHOLE-WORKLOAD-PLAN-v1',revision=r['revision'],source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],ceilings=q.CEILINGS,counts=dict(roles=26,genesis=2,hydrates=15,vm_steps=34816),roles=[x['name'] for x in q.inventory.retained.plan()['roles']],production_admission=False,live_attachment=False,attempts=1,retry_permitted=False,caller_module='experiments.digital_pilot74_qualification_caller_v1',closure_reserve_ms=250)
  return r,p
 def test_exact_shape_no_execution(self):
  r,p=self.fixture();self.assertTrue(q.shape(r,p))
 def test_production_pair_cannot_enter_qualification(self):
  for key,value in [('schema','PILOT74-FINITE-REGISTRATION-v2'),('mode','finite_qualification')]:
   r,p=self.fixture();r[key]=value
   with self.assertRaises(AssertionError):q.shape(r,p)
 def test_no_fabricated_production_review_substitution(self):
  r,p=self.fixture();r['reviews']={k:{} for k in ['interface','custody','union_failure','source_fit','whole_source_ci']}
  with self.assertRaises(AssertionError):q.shape(r,p)
 def test_exact_workload_and_resource_caps(self):
  for key,value in [('roles',25),('genesis',0),('hydrates',14),('vm_steps',0)]:
   r,p=self.fixture();p['counts'][key]=value
   with self.assertRaises(AssertionError):q.shape(r,p)
  for key in q.CEILINGS:
   r,p=self.fixture();p['ceilings']=dict(q.CEILINGS);p['ceilings'][key]+=1
   with self.assertRaises(AssertionError):q.shape(r,p)
 def test_reorder_retry_and_launch_refused(self):
  for key,value in [('roles',[]),('attempts',2),('retry_permitted',True),('live_attachment',True),('production_admission',True),('closure_reserve_ms',0),('caller_module','untrusted.module')]:
   r,p=self.fixture();p[key]=value
   with self.assertRaises(AssertionError):q.shape(r,p)
 def test_old_failed_lock_not_adopted(self):
  r,p=self.fixture();r['operator_lock']['path']='D:/OraLab/state/operator.lock'
  with self.assertRaises(AssertionError):q.shape(r,p)
 def test_grant_binding_excludes_only_grant_pin(self):
  r,p=self.fixture();b=q.binding(r);r['qualification']['grant']={'sha256':'d'*64};self.assertEqual(b,q.binding(r))
  r['reviews']['source_scope']={'sha256':'e'*64};self.assertNotEqual(b,q.binding(r))
 def test_unscoped_qualification_lock_refused(self):
  with patch.dict(os.environ,{},clear=True):self.assertFalse(scope.allowed(dict(path='D:/OraLab/runs/fresh/qualification-owner.lock')))
  self.assertTrue(scope.allowed(dict(path='D:/OraLab/state/operator.lock')))
 def test_native_route_has_only_fixed_worker_choices(self):
  s=(ROOT/'experiments/native/pilot74_guardian_v1.c').read_text()
  self.assertIn('!registration_route(r)',s)
  self.assertIn('qualification_mode?L"experiments.digital_pilot74_qualification_worker_v1":L"experiments.digital_pilot74_parent_worker_v2"',s)
  self.assertIn('owner_path_allowed(p)',s)
 def test_production_validator_still_requires_all_five(self):
  from experiments import digital_pilot74_finite_controller_v2 as production
  self.assertEqual(production.GATES,{'interface','custody','union_failure','source_fit','whole_source_ci'})
  self.assertIs(c.Controller,production.Controller)
 def test_no_world_population_import(self):
  self.assertNotIn('experiments.digital_pilot74_population',sys.modules)
if __name__=='__main__':unittest.main()
