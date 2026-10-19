"""One prospective changed-code lifecycle collector; no launch on import.

A collected diagnostic is not guardian conformance or recovery acceptance.
The old four-case worker and sealed failures are never called/reopened.
"""
import ctypes,json,sys,traceback
from pathlib import Path

KIND='PILOT74-SINGLE-POSTEXIT-LIFECYCLE-v1'
CASE='external_birth_mismatch'
MIB=1024**2


def validate(request,request_sha256,worker=False):
 from experiments import digital_pilot74_guardian_boundary_qualifier_v2 as h
 assert request['sha256']==request_sha256
 raw=h.read(request,32768);req=json.loads(raw);assert h.enc(req)==raw
 assert req['schema']=='PILOT74-SINGLE-LIFECYCLE-REQUEST-v1' and req['kind']==KIND
 assert set(req)=={'schema','kind','registration','review'}
 rr=h.read(req['registration'],131072);r=json.loads(rr);assert h.enc(r)==rr
 vr=h.read(req['review'],131072);v=json.loads(vr);assert h.enc(v)==vr
 assert r['schema']=='PILOT74-SINGLE-LIFECYCLE-REGISTRATION-v1' and r['kind']==KIND
 assert v['schema']=='PILOT74-INDEPENDENT-SINGLE-LIFECYCLE-EXECUTION-GRANT-v1' and v['verdict']=='PASS'
 assert v['registration']==req['registration'] and v['kind']==KIND
 assert v['reviewer_identity'] and v['review_evidence'] and v['finite_admission'] is False
 assert v['max_guardian_launches']==r['max_guardian_launches']==1
 assert r['case']==CASE and r['worlds']==r['vm_steps']==0
 assert v['source_sha256']==r['source_sha256'] and v['operator_lock']==r['operator_lock']
 assert r['parent_limits']==dict(memory_bytes=2048*MIB,cpu_seconds=60,wall_seconds=90,processes=4)
 assert r['slot_total_bytes']+r['zip_header_bound']<=64*MIB
 assert r['archive_limit']==r['restore_limit']==64*MIB and r['controller_limit']==8*MIB
 assert r['configuration_sha256']==h.sha(h.enc(r['configuration']))
 assert r['source_sha256']==h.sha(h.enc(r['source_files']))
 assert r['project_source_sha256']==h.sha(h.enc(r['project_source_manifest']))
 assert v['project_source_sha256']==r['project_source_sha256']
 assert r['configuration']['project_source_sha256']==r['project_source_sha256']
 assert r['configuration']['kind']==KIND and r['configuration']['guardian_launches']==1
 assert r['artifact']['sha256']=='c22a3668dd57bedf2e55def8e39ad867e1ce6c2a4657c583bf067cd5cd46e391'
 assert h.read(r['registration_fixture'],2)==b'{}'
 for pin in r['input_pins']:h.read(pin,pin['extent'])
 h.read(r['operator_lock'],16384)
 assert Path(__file__).resolve()==Path(r['source_root'])/'experiments/digital_pilot74_lifecycle_diagnostic_v1.py'
 h.origins(r,worker_main=worker)
 # Actual registration/grant/native issuer ancestry remains external.
 # These bindings never issue a review or authorize a World/VM/controller.
 return h,r


def encoded_bounds(h,facts):
 """Refuse collection admission on full encoded sizes, never slice data.

 Full case/first-failure records remain in their separate precharged leaves.
 These NEW diagnostic bounds don't alter either old conformance predicate.
 """
 errors=[]
 def bound(name,value,limit):
  needed=len(h.enc(value))
  if needed>limit:errors.append(dict(field=name,required_bytes=needed,ceiling=limit))
 bound('case',facts,196608)
 before=facts.get('before_owned_handle_release');after=facts.get('after_owned_handle_release_attempts')
 bound('before',before,98304);bound('after',after,8192)
 bound('capture',facts.get('stdout_capture'),8192)
 for name in ('traceback','traceback_after_cleanup'):bound(name,facts.get(name),32768)
 bound('exception',facts.get('exception'),4096)
 if type(before) is dict:
  rows=before.get('handles',[])
  if len(rows)>5:errors.append(dict(field='handle_rows',required=len(rows),ceiling=5))
  for index,row in enumerate(rows):
   bound('handle:'+str(index),row,16384)
   bound('image:'+str(index),row.get('image'),12288)
   bound('handle_errors:'+str(index),row.get('errors'),4096)
 return errors


def worker(request,request_sha256):
 h,r=validate(request,request_sha256,True)
 from experiments import process_limits as caps
 limits=caps.ExtendedLimits();k=caps.kernel()
 caps.checked(k.QueryInformationJobObject(None,9,ctypes.byref(limits),ctypes.sizeof(limits),None))
 assert limits.job_memory==2048*MIB and limits.basic.job_cpu==60*10_000_000 and limits.basic.active_processes==4
 assert h.kernel().GetTickCount64()>=3590000
 for name in sys.modules:
  if name.startswith('experiments.'):
   assert not any(word in name for word in ('_engine','_world','_child','_publication','_registry','_referee'))
 error=None;first_receipt=None
 try:
  h.one_case(r,CASE,r['operator_lock'])
 except BaseException as first:
  error=first
 # Never rerun the failed case or replace its first-exception receipt.
 case=h.spec(Path(r['slots']['raw/native/'+CASE+'.json']['path']),MIB)
 raw=h.read(case,MIB);facts=json.loads(raw);assert h.enc(facts)==raw
 before=facts.get('before_owned_handle_release')
 after=facts.get('after_owned_handle_release_attempts')
 releases=facts.get('owned_handle_release_results',{})
 capture=facts.get('stdout_capture')
 if error is not None:
  first_receipt=h.spec(Path(r['slots']['failure/first-exception.json']['path']),262144)
  if first_receipt['extent']:h.read(first_receipt,262144)
 bound_errors=encoded_bounds(h,facts)
 collected=bool(not bound_errors and facts.get('observed_before_assertions') and facts.get('exact_process_handle_signaled')
  and type(facts.get('usage')) is dict and type(before) is dict and before.get('complete')
  and type(after) is dict and after.get('complete') and after.get('open_listed_handles') is False
  and releases.get('thread') is True and releases.get('process') is True
  and (error is None or first_receipt['extent']>0)
  and not facts.get('cleanup_errors') and type(capture) is dict and capture.get('capture_complete')
  and capture.get('eof') and not capture.get('errors'))
 outcome=dict(schema='PILOT74-SINGLE-LIFECYCLE-OUTCOME-v1',kind=KIND,case_receipt=case,
  diagnostic_collected=collected,first_exception_receipt=first_receipt,guardian_conformance_passed=error is None and facts.get('passed') is True,
  original_exception=None if error is None else dict(type=type(error).__name__,case_receipt=case,first_exception_receipt=first_receipt),encoding_bound_errors=bound_errors,
  count_predicate_unchanged=True,counts_not_rescored=True,guardian_launches=1,
  positive_custody_or_recovery_qualified=False,finite_admission=False,worlds=0,vm_steps=0,
  external_actual_registration_and_native_ancestry_required=True)
 h.write(r['slots']['raw/diagnostic-outcome.json'],h.enc(outcome))
 # Only a small bounded summary is printed, not a duplicate full native body.
 summary=dict(kind=KIND,diagnostic_collected=collected,
  guardian_conformance_passed=outcome['guardian_conformance_passed'],case_receipt=case,finite_admission=False)
 raw=h.enc(summary);assert len(raw)<=4096;sys.stdout.buffer.write(raw+b'\n');sys.stdout.buffer.flush()
 h.origins(r,True)
 return 0 if collected else 2


if __name__=='__main__':
 assert len(sys.argv)==3
 sys.exit(worker(json.loads(sys.argv[1]),sys.argv[2]))
