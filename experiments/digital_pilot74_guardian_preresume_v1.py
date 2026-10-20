"""One explicitly granted pre-create/pre-resume owned-Job observation.

No registration builder, native launch on import or old worker entrypoint.
The one-role worker requires exact externally granted source and reservations.
Retained v2 and its closed failures remain untouched.
"""
import ctypes,json,os,struct,sys,threading,time,traceback
from ctypes import wintypes as wt
from pathlib import Path
from experiments import digital_pilot74_guardian_boundary_qualifier_v2 as retained
MIB=1024**2
START=retained.START;STARTEX=retained.STARTEX;PI=retained.PI
kernel=retained.kernel;checked=retained.checked;birth=retained.birth
enc=retained.enc;sha=retained.sha;read=retained.read;write=retained.write


def observe_job_live(job,known_process=None,known_pid=None,known_birth=None,open_listed_handles=True):
 """One current owned-Job sample, <=4 opens, original handle never closed.

 Each query's fact survives failures in other queries. Image failure does not
 erase exact-handle exit/wait/birth facts. Post-exit missing image stays null;
 before-resume image is separately captured, never backfilled into this row.
 No polling for favourable counts, old PID lookup or authority from PID alone.
 """
 k=kernel();out=dict(schema='PILOT74-OWNED-JOB-LIVE-OBSERVATION-v1',
  complete=True,observed_monotonic_ns=time.monotonic_ns(),usage=None,
  listed_pids=None,handles=[],errors=[],open_listed_handles=open_listed_handles)
 def failed(where,error):
  out['complete']=False;out['errors'].append(dict(where=where,error=repr(error)))
 def row(handle,pid,origin,expected_birth=None):
  value=dict(pid=int(pid),origin=origin,actual_pid=None,membership=None,birth=None,
             image=None,exit_code=None,wait_result=None,errors=[])
  def attempt(field,query):
   try:value[field]=query()
   except BaseException as error:
    out['complete']=False;value['errors'].append(dict(field=field,error=repr(error)))
  def identity():
   actual=int(k.GetProcessId(handle));assert actual==pid;return actual
  def membership():
   member=wt.BOOL();checked(k.IsProcessInJob(handle,job.handle,ctypes.byref(member)))
   assert member.value;return True
  def creation():
   actual=birth(k,handle)
   if expected_birth is not None:assert actual==expected_birth
   return str(actual)
  def image():
   text=ctypes.create_unicode_buffer(1024);length=wt.DWORD(1024)
   checked(k.QueryFullProcessImageNameW(handle,0,text,ctypes.byref(length)))
   assert 0<length.value<1024;return text[:length.value]
  def exit_code():
   code=wt.DWORD();checked(k.GetExitCodeProcess(handle,ctypes.byref(code)));return int(code.value)
  def wait():
   result=int(k.WaitForSingleObject(handle,0));assert result in (0,258);return result
  for field,query in [('actual_pid',identity),('membership',membership),('birth',creation),('image',image),('exit_code',exit_code),('wait_result',wait)]:attempt(field,query)
  return value
 try:out['usage']=job.usage()
 except BaseException as error:failed('usage',error)
 try:out['listed_pids']=[int(pid) for pid in job.pids()]
 except BaseException as error:failed('owned_job_pid_list',error)
 if known_process:out['handles'].append(row(known_process,known_pid,'original_CreateProcess_handle',known_birth))
 if open_listed_handles and out['listed_pids'] is not None:
  if len(out['listed_pids'])>4:
   failed('bounded_handle_observation',RuntimeError('Listed count exceeds4; no extra handles opened'))
  else:
   for pid in out['listed_pids']:
    if known_process and pid==known_pid:continue
    handle=None
    try:
     handle=k.OpenProcess(0x1000|0x100000,False,pid);checked(handle)
     out['handles'].append(row(handle,pid,'current_owned_job_list_opened_handle'))
    except BaseException as error:failed('open_current_job_list_handle:'+str(pid),error)
    finally:
     if handle:
      try:checked(k.CloseHandle(handle))
      except BaseException as error:failed('close_observation_handle:'+str(pid),error)
 # Full bodies are retained or refused, never sliced. New caller must reserve
 # these bounds prospectively; this source does not precharge or admit them.
 if len(enc(out))>65536:raise ValueError('Observation full encoded extent exceeds64KiB')
 return out


def same_original_exit(observation,pid,creation,exit_code):
 """Image belongs to the pre-resume record; require independent exit facts."""
 rows=[row for row in observation.get('handles',[]) if row.get('origin')=='original_CreateProcess_handle']
 if len(rows)!=1:return False
 row=rows[0]
 return (row.get('actual_pid')==pid and row.get('membership') is True
  and row.get('birth')==str(creation) and row.get('wait_result')==0
  and row.get('exit_code')==exit_code)


def one_case(r,name,owner):
 assert name=='external_birth_mismatch' and r['schema']=='PILOT74-PRECREATE-PRERESUME-REGISTRATION-v1'
 assert r['max_guardian_launches']==1 and r['worlds']==r['vm_steps']==0
 assert read(r['preresume_observer'],65536)==Path(__file__).read_bytes()
 assert read(r['retained_harness'],65536)==Path(retained.__file__).read_bytes()
 """Host retains Job handle for negative-case observation, not sole-owner proof."""
 entered=time.monotonic()
 import msvcrt,subprocess
 from experiments import process_limits as caps
 from experiments.digital_pilot74_output_capture_v2 import Capture
 k=kernel();root=Path(r['root']);pi=PI();job=None;attributes=None;initialized=False;fds=[];thread=None;sink=None;stream=None;command=None;original_birth=None;started=entered;usage=None;capture=None;first=None;return_code=None;facts={};received=0;out_w=None;monitor=None;job_guard=threading.RLock();capture_claim=threading.Lock()
 def stop_job():
  with job_guard:
   if job is not None and job.handle:job.terminate()
 def close_job():
  with job_guard:
   if job is not None:job.close()
 try:
  origin_tick=k.GetTickCount64();memory=1024*MIB if name=='wrong_root_limit_readback' else 2048*MIB
  job=caps.Job(caps.Limits(memory_bytes=memory,cpu_seconds=2400,processes=4,wall_seconds=5))
  facts['empty_job_before_create']=observe_job_live(job,open_listed_handles=False)
  write(r['slots']['raw/prelaunch/empty-job.json'],enc(facts['empty_job_before_create']))
  assert facts['empty_job_before_create']['complete'] and facts['empty_job_before_create']['listed_pids']==[]
  assert facts['empty_job_before_create']['usage']['started_processes']==0 and facts['empty_job_before_create']['usage']['active_before_close']==0
  from experiments.digital_pilot74_job_events_v1 import JobEvents
  monitor=JobEvents(job,stop_job);monitor.start()
  br,bw=os.pipe();out_r,out_w=os.pipe();nul=os.open(os.devnull,os.O_RDONLY|os.O_BINARY);fds=[br,bw,out_r,out_w,nul]
  handles=[job.handle,msvcrt.get_osfhandle(br),msvcrt.get_osfhandle(out_w),msvcrt.get_osfhandle(nul)]
  for h in handles:checked(k.SetHandleInformation(h,1,1))
  n=ctypes.c_size_t();k.InitializeProcThreadAttributeList(None,2,0,ctypes.byref(n));assert n.value>0;attributes=ctypes.create_string_buffer(n.value);checked(k.InitializeProcThreadAttributeList(attributes,2,0,ctypes.byref(n)));initialized=True
  jobs=(wt.HANDLE*1)(job.handle);inherited=(wt.HANDLE*4)(*handles);checked(k.UpdateProcThreadAttribute(attributes,0,0x2000D,jobs,ctypes.sizeof(jobs),None,None));checked(k.UpdateProcThreadAttribute(attributes,0,0x20002,inherited,ctypes.sizeof(inherited),None,None))
  actual_start=origin_tick;fixture_start=actual_start
  if name=='expired_original_stop_window':assert actual_start>=3590000;fixture_start=actual_start-3590000
  request=r['registration_fixture'];command=[r['artifact']['path'],str(int(job.handle)),str(fixture_start),request['path'],str(request['extent']),'0'*64,str(handles[1])]
  grant=dict(version='PILOT74-NATIVE-CAPTURE-GRANT-v2',root=r['root'],source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],role=name,command_sha256=sha(enc(command)),operator_lock=owner,raw={key:r['slots']['raw/stdout/'+name+'.bin'][key] for key in ('path','limit','device','inode')},overflow={key:r['slots']['failure/native-first-output.bin'][key] for key in ('path','limit','device','inode')})
  write(r['slots']['raw/grants/'+name+'.json'],enc(grant));sink=Capture(grant,sha(enc(grant)),r['source_sha256'],r['configuration_sha256'],name,command)
  def drain(nonblocking=False):
   nonlocal received
   if not capture_claim.acquire(blocking=False):return
   try:
    if nonblocking:os.set_blocking(stream.fileno(),False)
    while True:
     block=os.read(stream.fileno(),65536)
     if not block:sink.eof=True;break
     received+=len(block);sink.append(block)
     if received>MIB:stop_job()
   except BaseException as e:
    sink.errors.append(repr(e))
    try:stop_job()
    except BaseException as later:sink.errors.append(repr(later))
  stream=os.fdopen(out_r,'rb',buffering=0);fds.remove(out_r)
  si=STARTEX();si.startup.cb=ctypes.sizeof(si);si.startup.flags=0x100;si.startup.input=handles[3];si.startup.output=si.startup.error=handles[2];si.attributes=ctypes.cast(attributes,ctypes.c_void_p)
  if name=='expired_original_stop_window':assert fixture_start+3580000<=k.GetTickCount64()<fixture_start+3600000,'Fixture must remain inside stop window before hard deadline'
  # DETACHED_PROCESS avoids console attachment; explicit IPC handles and
  # creation-time Job containment remain unchanged (no Job breakaway).
  line=ctypes.create_unicode_buffer(subprocess.list2cmdline(command));assert time.monotonic()-started<5,'Case setup consumed original5s deadline; do not create G';checked(k.CreateProcessW(r['artifact']['path'],line,None,None,True,0x80000|0x4|0x8,None,r['source_root'],ctypes.byref(si),ctypes.byref(pi)))
  # The sole pipe reader starts immediately after CreateProcess, before
  # any fallible birth/membership/receipt query. Late startup cannot steal
  # pipe ownership from the synchronous failure fallback.
  try:
   thread=threading.Thread(target=drain,daemon=True);thread.start()
  except BaseException as startup_error:
   sink.errors.append('Capture thread startup:'+repr(startup_error))
   try:stop_job()
   except BaseException as later:sink.errors.append('Startup stop:'+repr(later))
   os.close(out_w);fds.remove(out_w)
   drain(nonblocking=True)
   raise
  original_birth=birth(k,pi.process);handed=original_birth+1 if name=='external_birth_mismatch' else original_birth;assert handed<2**64
  member=wt.BOOL();checked(k.IsProcessInJob(pi.process,job.handle,ctypes.byref(member)));assert member.value;actual=caps.ExtendedLimits();checked(caps.kernel().QueryInformationJobObject(job.handle,9,ctypes.byref(actual),ctypes.sizeof(actual),None));assert actual.job_memory==memory and actual.basic.job_cpu==2400*10_000_000 and actual.basic.active_processes==4 and actual.basic.flags&(0x4|0x8|0x200|0x2000)==(0x4|0x8|0x200|0x2000);facts.update(root_membership_observed=True,root_limit_readback=dict(memory_bytes=int(actual.job_memory),cpu_ticks=int(actual.basic.job_cpu),processes=int(actual.basic.active_processes),flags=int(actual.basic.flags)))
  facts.update(pid=pi.pid,creation_filetime_decimal=str(original_birth),handed_birth_decimal=str(handed),actual_case_start_tick=actual_start,fixture_original_tick=fixture_start,root_limits=vars(job.limits) if hasattr(job,'limits') else dict(memory_bytes=memory,cpu_seconds=2400,processes=4),root_job_membership_from_creation_requested=True,command=command)
  facts['suspended_before_resume']=observe_job_live(job,pi.process,pi.pid,original_birth)
  write(r['slots']['raw/prelaunch/suspended-job.json'],enc(facts['suspended_before_resume']))
  assert facts['suspended_before_resume']['complete'],'Suspended original/current owned Job identity incomplete; no resume'
  original_rows=[row for row in facts['suspended_before_resume']['handles'] if row['origin']=='original_CreateProcess_handle']
  assert len(original_rows)==1 and original_rows[0]['wait_result']==258 and original_rows[0]['exit_code']==259
  assert Path(original_rows[0]['image']).resolve()==Path(r['artifact']['path']).resolve()
  write(r['slots']['raw/native/'+name+'.start.json'],enc(facts))
  assert os.write(bw,struct.pack('<Q',handed))==8;os.close(bw);fds.remove(bw)
  assert time.monotonic()-started<5,'Case setup consumed original5s deadline; do not resume G'
  if name=='expired_original_stop_window':assert fixture_start+3580000<=k.GetTickCount64()<fixture_start+3600000
  facts['setup_elapsed_seconds']=time.monotonic()-started;assert k.ResumeThread(pi.thread)==1
  os.close(out_w);fds.remove(out_w)
  while k.WaitForSingleObject(pi.process,10)==258:
   if time.monotonic()-started>=5:raise TimeoutError('NEW boundary case exceeded5s; closure authority incomplete until exact handles observed')
  assert k.WaitForSingleObject(pi.process,0)==0 and birth(k,pi.process)==original_birth;code=wt.DWORD();checked(k.GetExitCodeProcess(pi.process,ctypes.byref(code)));return_code=code.value
  thread.join(2);assert not thread.is_alive();capture=sink.finish();usage=job.usage()
  # Retain ALL already observed values before any conformance assertion.
  facts.update(exit_code=return_code,stdout_capture=capture,usage=usage,exact_process_handle_signaled=True,observed_before_assertions=True)
  facts['before_owned_handle_release']=observe_job_live(job,pi.process,pi.pid,original_birth)
  assert return_code==125 and capture['capture_complete'] and capture['eof'] and not capture['errors'] and received==0
  assert usage['started_processes']==1 and usage['active_before_close']==0,'Unexpected worker/descendant; no valid worker or World is permitted'
  assert same_original_exit(facts['before_owned_handle_release'],pi.pid,original_birth,return_code)
  # The live image was pinned before resume. A later image-query failure
  # does not erase same-original-handle PID/birth/membership/exit observations.
  # Keep all errors and complete=False in the raw post-exit snapshot.
  facts['post_exit_identity_verified_from_retained_handle']=True
  facts.update(schema='PILOT74-NEW-NATIVE-BOUNDARY-RESULT-v1',case=name,exit_code=return_code,exact_process_handle_signaled=True,stdout_capture=capture,usage=usage,elapsed_seconds=time.monotonic()-started,passed=True,worlds=0,vm_steps=0,finite_admission=False)
  # Final result is written only after successful native-handle cleanup below.
 except BaseException as e:
  first=e
  if job:
   try:stop_job()
   except BaseException as later:e.add_note('Job stop error:'+repr(later))
  if pi.process:
   wait=k.WaitForSingleObject(pi.process,2000);facts['exact_process_handle_signaled']=wait==0
   if original_birth is None:
    try:original_birth=birth(k,pi.process)
    except BaseException as later:e.add_note('Birth unknown:'+repr(later))
  if out_w in fds:
   try:os.close(out_w);fds.remove(out_w)
   except BaseException as later:e.add_note('Parent output writer close:'+repr(later))
  if thread and thread.ident is not None:thread.join(2)
  if sink and not(thread and thread.is_alive()):
   try:capture=sink.finish()
   except BaseException as later:e.add_note('Failure capture facts:'+repr(later))
  if job:
   try:usage=job.usage()
   except BaseException as later:e.add_note('Failure usage facts:'+repr(later))
  if pi.process and facts.get('exact_process_handle_signaled'):
   try:
    code=wt.DWORD();checked(k.GetExitCodeProcess(pi.process,ctypes.byref(code)));return_code=code.value
   except BaseException as later:e.add_note('Failure original exit facts:'+repr(later))
  facts.update(case=name,command=command,pid=pi.pid or None,creation_filetime_decimal=None if original_birth is None else str(original_birth),exception=repr(e),traceback=''.join(traceback.format_exception(e)),closure_unknown=True,passed=False,available_capture_errors=[] if sink is None else sink.errors,raw_EOF_known=False if sink is None else sink.eof)
  facts.update(exit_code=return_code,stdout_capture=capture,usage=usage,observations_missing_explicitly_unknown=True)
  try:write(r['slots']['failure/first-exception.json'],enc(facts))
  except BaseException as later:e.add_note('First exception write incomplete:'+repr(later))
  raise
 finally:
  # If a capture thread cannot join, its files/EOF are UNKNOWN. No final
  # archive acceptance is allowed while such a writer is active.
  errors=[]
  def cleanup(action):
   try:action()
   except BaseException as error:errors.append(repr(error));return False
   return True
  if thread and thread.is_alive():thread.join(2)
  if sink and not(thread and thread.is_alive()):cleanup(sink.close)
  if stream and not(thread and thread.is_alive()):cleanup(stream.close)
  for fd in fds:cleanup(lambda fd=fd:os.close(fd))
  thread_released=cleanup(lambda:checked(k.CloseHandle(pi.thread))) if pi.thread else None
  process_released=cleanup(lambda:checked(k.CloseHandle(pi.process))) if pi.process else None
  facts['owned_handle_release_results']=dict(thread=thread_released,process=process_released)
  if initialized:cleanup(lambda:k.DeleteProcThreadAttributeList(attributes))
  # No waiting for counts to become favourable. One immediate fresh Job
  # sample after our references close; keep original assertions unchanged.
  if job and job.handle:
   try:facts['after_owned_handle_release_attempts']=observe_job_live(job,open_listed_handles=False)
   except BaseException as error:errors.append('Post-release observation unknown:'+repr(error))
  if monitor:
   try:
    facts['job_events']=monitor.finish()
    write(r['slots']['raw/prelaunch/job-events.json'],enc(facts['job_events']))
    if not facts['job_events']['monitor_complete']:errors.append('Event observation incomplete; no identity census inferred')
   except BaseException as error:errors.append('Event finalization:'+repr(error))
  if job:cleanup(close_job)
  if thread and thread.is_alive():errors.append('Capture writer still active; no archive authority')
  facts['cleanup_errors']=errors
  if errors:
   facts['passed']=False;facts['closure_unknown']=True
   if first is not None:first.add_note('Native cleanup incomplete:'+repr(errors))
  if first is not None:facts['traceback_after_cleanup']=''.join(traceback.format_exception(first))
  # Distinct already-precharged final case record even on failure; never
  # overwrite the earlier first-exception or any post-archive evidence.
  try:write(r['slots']['raw/native/'+name+'.json'],enc(facts))
  except BaseException as error:
   if first is not None:first.add_note('Final native case custody incomplete:'+repr(error))
   else:raise
  if errors and first is None:raise RuntimeError('Native cleanup incomplete:'+repr(errors))
 return facts


def collect_registered(registration,review):
 """One future independently registered source-bound observation, no CLI.

 This helper issues no grants and never calls a retained closed worker. New
 exact source/input/physical reservation/caps/native issuer ancestry must be
 reviewed separately before ANY caller invokes it.
 """
 rr=read(registration,131072);vr=read(review,131072)
 r=json.loads(rr);v=json.loads(vr);assert enc(r)==rr and enc(v)==vr
 assert r['schema']=='PILOT74-PRECREATE-PRERESUME-REGISTRATION-v1'
 assert v['schema']=='PILOT74-INDEPENDENT-PRERESUME-EXECUTION-GRANT-v1'
 assert v['registration']==registration and v['verdict']=='PASS'
 assert v['reviewer_identity'] and v['review_evidence'] and v['finite_admission'] is False
 assert v['max_guardian_launches']==r['max_guardian_launches']==1
 assert r['worlds']==r['vm_steps']==0 and r['case']=='external_birth_mismatch'
 assert v['observer']==r['preresume_observer'] and v['source_sha256']==r['source_sha256']
 assert v['operator_lock']==r['operator_lock'] and v['owner_birth']==r['owner_birth']
 assert type(v['issued_monotonic_ns']) is int and type(v['expires_monotonic_ns']) is int
 assert v['issued_monotonic_ns']<=time.monotonic_ns()<v['expires_monotonic_ns']
 assert v['expires_monotonic_ns']-v['issued_monotonic_ns']<=3600*10**9
 assert r['parent_limits']==dict(memory_bytes=2048*MIB,cpu_seconds=60,wall_seconds=90,processes=4)
 assert r['artifact']['sha256']=='c22a3668dd57bedf2e55def8e39ad867e1ce6c2a4657c583bf067cd5cd46e391'
 assert read(r['registration_fixture'],2)==b'{}'
 assert r['source_sha256']==sha(enc(r['source_files']))
 for pin in r['input_pins']:read(pin,pin['extent'])
 retained.origins(r)
 owner=json.loads(read(r['operator_lock'],16384))
 from experiments.digital_pilot74_journal import birth as current_birth
 assert current_birth(owner['pid'])==r['owner_birth']
 assert Path(__file__).resolve()==Path(r['preresume_observer']['path']).resolve()
 # Caller must already be the single reviewed capped diagnostic worker.
 from experiments import process_limits as caps
 limit=caps.ExtendedLimits();k=caps.kernel()
 checked(k.QueryInformationJobObject(None,9,ctypes.byref(limit),ctypes.sizeof(limit),None))
 assert limit.job_memory==2048*MIB and limit.basic.job_cpu==60*10_000_000 and limit.basic.active_processes==4
 assert kernel().GetTickCount64()>=3590000
 first=None
 try:one_case(r,r['case'],r['operator_lock'])
 except BaseException as error:first=error
 native=retained.spec(Path(r['slots']['raw/native/'+r['case']+'.json']['path']),MIB)
 raw=read(native,MIB);facts=json.loads(raw);assert enc(facts)==raw
 pre=facts.get('suspended_before_resume') or {}
 rows=[row for row in pre.get('handles',[]) if row.get('origin')=='original_CreateProcess_handle']
 original=rows[0] if len(rows)==1 else {}
 empty=facts.get('empty_job_before_create') or {}
 usage=facts.get('usage') or {};after=facts.get('after_owned_handle_release_attempts') or {}
 capture=facts.get('stdout_capture') or {}
 bound_errors=[]
 for field,value,ceiling in [('case',facts,393216),('pre',pre,65536),('empty',empty,65536),('events',facts.get('job_events'),65536),('after',after,8192),('capture',capture,8192),('traceback',facts.get('traceback'),32768),('cleanup_traceback',facts.get('traceback_after_cleanup'),32768)]:
  extent=len(enc(value))
  if extent>ceiling:bound_errors.append(dict(field=field,extent=extent,ceiling=ceiling))
 collected=bool(not bound_errors and (facts.get('job_events') or {}).get('monitor_complete') and empty.get('complete') and pre.get('complete') and original.get('image')
  and original.get('pid')==facts.get('pid') and original.get('birth')==facts.get('creation_filetime_decimal')
  and facts.get('exact_process_handle_signaled') and facts.get('observed_before_assertions')
  and facts.get('exit_code')==125 and type(usage.get('started_processes')) is int
  and type(usage.get('active_before_close')) is int and after.get('complete')
  and capture.get('capture_complete') and capture.get('eof') and not capture.get('errors')
  and not capture.get('stdout_limit_exceeded') and not facts.get('cleanup_errors'))
 return dict(schema='PILOT74-PRERESUME-COLLECTION-v1',native=native,
  diagnostic_collected=collected,guardian_conformance_passed=facts.get('passed') is True,
  before_resume_identity_source='actual original CreateProcess handle while suspended',
  post_exit_image_not_backfilled=True,actual_started_processes=usage.get('started_processes'),
  actual_active_processes=usage.get('active_before_close'),case_first_exception_present=first is not None,
  first_exception_path=r['slots']['failure/first-exception.json']['path'] if first is not None else None,
  encoding_bound_errors=bound_errors,no_historical_pid_lookup=True,worlds=0,vm_steps=0,finite_admission=False)


def worker(request,request_sha256):
 """One capped, externally reviewed role; never issues its own grant."""
 assert request['sha256']==request_sha256
 raw=read(request,32768);req=json.loads(raw);assert enc(req)==raw
 assert set(req)=={'schema','registration','review'} and req['schema']=='PILOT74-PRERESUME-REQUEST-v1'
 body=read(req['registration'],131072);r=json.loads(body);assert enc(r)==body
 assert r['source_root']==str(Path(__file__).resolve().parents[1])
 assert r['source_sha256']==sha(enc(r['source_files']))
 for pin in r['input_pins']:read(pin,pin['extent'])
 retained.origins(r,worker_main=True)
 for name in sys.modules:
  if name.startswith('experiments.'):
   assert not any(word in name for word in ('_engine','_world','_child','_publication','_registry','_referee'))
 outcome=collect_registered(req['registration'],req['review']);outcome['kind']=r['kind']
 raw=enc(outcome);assert len(raw)<=65536
 write(r['slots']['raw/diagnostic-outcome.json'],raw)
 summary=enc(dict(diagnostic_collected=outcome['diagnostic_collected'],guardian_conformance_passed=outcome['guardian_conformance_passed'],native=outcome['native'],finite_admission=False))
 assert len(summary)<=4096;sys.stdout.buffer.write(summary+b'\n');sys.stdout.buffer.flush()
 retained.origins(r,worker_main=True)
 return 0 if outcome['diagnostic_collected'] else 2


if __name__=='__main__':
 assert len(sys.argv)==4 and sys.argv[1]=='--worker'
 sys.exit(worker(json.loads(sys.argv[2]),sys.argv[3]))
