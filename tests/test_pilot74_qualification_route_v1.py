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
class AdmissionCalls(unittest.TestCase):
 def actual_fixture(self):
  from unittest.mock import Mock
  r,plan=Route.fixture(self);lock=r['operator_lock'];lock.update(extent=3,sha256='f'*64,device=1,inode=2)
  r['qualification']={k:dict(path=k) for k in ('plan','grant','preserved_failure_lock')}
  r['qualification']['preserved_failure_lock'].update(path='D:/OraLab/state/operator.lock',extent=3,sha256='f'*64,device=4,inode=5)
  r['reviews']={k:dict(path=k) for k in q.REVIEWS}
  reviews={k:dict(schema='PILOT74-QUALIFICATION-PREFLIGHT-REVIEW-v1',kind=k,verdict='PASS',scope='one_full_workload_qualification_only',revision=r['revision'],source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],plan=r['qualification']['plan'],reviewer_identity='fixture-only',review_evidence=['fixture'],production_admission=False,head_sha=r['revision'],conclusion='success',old_suites_rerun=False) for k in q.REVIEWS}
  grant=dict(schema='PILOT74-FULL-QUALIFICATION-OWNER-GRANT-v1',verdict='PASS',registration_body_sha256=q.binding(r),plan=r['qualification']['plan'],source_sha256=r['source_sha256'],operator_lock=lock,reviewer_identity='fixture-only',review_evidence=['fixture'],issued_monotonic_ns=90*10**9,expires_monotonic_ns=200*10**9,attempts=1,production_admission=False,owner=dict(pid=123,creation_filetime_decimal='456'))
  data=dict(reviews,plan=plan,grant=grant);data[lock['path']]=dict(schema='PILOT74-QUALIFICATION-OWNER-LOCK-v1',**grant['owner'])
  k=Mock();k.OpenProcess.return_value=1;k.WaitForSingleObject.return_value=258;k.CloseHandle.return_value=True
  return r,data,k
 def invoke(self,r,data,k,birth=456):
  with patch.object(q,'parsed',side_effect=lambda pin,*args:data[pin['path']]),patch.object(q.physical,'read_exact',return_value=(b'old',(4,5))),patch.object(q.time,'monotonic_ns',return_value=100*10**9),patch.object(q.guardian,'_kernel',return_value=k),patch.object(q.guardian,'_birth',return_value=birth):return q.validate(r)
 def test_actual_validate_mocked_owner_and_reviews(self):
  r,d,k=self.actual_fixture();self.assertEqual(set(self.invoke(r,d,k)),q.REVIEWS);k.CloseHandle.assert_called_once_with(1)
 def test_expired_and_future_grants_fail_before_process_query(self):
  for key,value in [('expires_monotonic_ns',99*10**9),('issued_monotonic_ns',101*10**9)]:
   r,d,k=self.actual_fixture();d['grant'][key]=value
   with self.assertRaises(AssertionError):self.invoke(r,d,k)
   k.OpenProcess.assert_not_called()
 def test_changed_review_plan_and_registration_refused(self):
  for target in ('review','plan','registration'):
   r,d,k=self.actual_fixture()
   if target=='review':d['source_scope']['revision']='0'*40
   elif target=='plan':d['plan']['counts']['genesis']=0
   else:r['configuration_sha256']='0'*64
   with self.assertRaises(AssertionError):self.invoke(r,d,k)
   k.OpenProcess.assert_not_called()
 def test_mismatched_owner_birth_is_closed_and_refused(self):
  r,d,k=self.actual_fixture()
  with self.assertRaises(AssertionError):self.invoke(r,d,k,birth=999)
  k.CloseHandle.assert_called_once_with(1)

class OwnerDescriptor(unittest.TestCase):
 def descriptor(self,path):
  raw=b'owner';path.write_bytes(raw);fd=os.open(path,os.O_RDWR);i=os.fstat(fd)
  return fd,dict(path=str(path),extent=len(raw),sha256=hashlib.sha256(raw).hexdigest(),device=i.st_dev,inode=i.st_ino)
 def test_changed_bytes_and_closed_descriptor_refused(self):
  from experiments.digital_pilot74_qualification_owner_v1 import recheck_descriptor
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'lock';fd,lock=self.descriptor(p)
   try:
    recheck_descriptor(fd,lock);p.write_bytes(b'other')
    with self.assertRaises(AssertionError):recheck_descriptor(fd,lock)
   finally:os.close(fd)
   with self.assertRaises(OSError):recheck_descriptor(fd,lock)
 def test_swapped_descriptor_refused(self):
  from experiments.digital_pilot74_qualification_owner_v1 import recheck_descriptor
  with tempfile.TemporaryDirectory() as d:
   a,lock=self.descriptor(Path(d)/'a');b,_=self.descriptor(Path(d)/'b')
   try:
    with self.assertRaises(AssertionError):recheck_descriptor(b,lock)
   finally:os.close(a);os.close(b)
 def test_owner_rechecks_before_creation_and_reused_claim_refused(self):
  from experiments import digital_pilot74_qualification_owner_v1 as owner
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);fd,lock=self.descriptor(root/'lock');r=dict(root=str(root/'workload'),source_root=str(ROOT),operator_lock=lock,python=dict(path=sys.executable),qualification=dict(grant=dict(path='grant'),plan=dict(path='plan')))
   grant=dict(owner=dict(pid=os.getpid(),creation_filetime_decimal='fixture'))
   plan=dict(closure_reserve_ms=250,caller_module='experiments.digital_pilot74_qualification_caller_v1')
   values={'grant':grant,'plan':plan}
   def outer(request,admit):
    self.assertTrue(admit(request));return {'fixture_only':True}
   try:
    with patch.object(owner.controller,'validate_guardian',return_value=r),patch.object(owner.admission,'parsed',side_effect=lambda pin:values[pin['path']]),patch.object(owner.outer,'launch',side_effect=outer) as launch:
     self.assertTrue(owner.launch(dict(path='fixture',extent=1,sha256='f'*64),'f'*64,fd,250)['fixture_only'])
     with self.assertRaises(FileExistsError):owner.launch(dict(path='fixture',extent=1,sha256='f'*64),'f'*64,fd,250)
     self.assertEqual(launch.call_count,1)
   finally:os.close(fd)
if __name__=='__main__':unittest.main()
