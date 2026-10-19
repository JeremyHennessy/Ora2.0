"""UNQUALIFIED new native-boundary harness. No automatic preparation or launch.

Only four new early refusals, no valid worker/World registration. An external
review receipt and separately pinned concrete registration precede execution.
The closed argc/build groups are never called. No VM/producer/controller import.
"""
import ctypes,hashlib,json,os,stat,struct,sys,threading,time,traceback,zipfile
from ctypes import wintypes as wt
from pathlib import Path
MIB=1024**2
CASES=('external_birth_mismatch','wrong_root_limit_readback','expired_original_stop_window','registration_hash_mismatch')

def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def plain(p,directory=False):
 i=p.lstat();assert not stat.S_ISLNK(i.st_mode) and not getattr(i,'st_file_attributes',0)&0x400
 assert stat.S_ISDIR(i.st_mode) if directory else stat.S_ISREG(i.st_mode) and i.st_nlink==1
 return i
def read(spec,cap):
 p=Path(spec['path']);before=plain(p);assert 0<=before.st_size==spec['extent']<=cap
 for x in p.parents:plain(x,True)
 with p.open('rb') as f:
  inside=os.fstat(f.fileno());assert (inside.st_dev,inside.st_ino)==(before.st_dev,before.st_ino);raw=f.read(cap+1)
 after=plain(p);assert (after.st_dev,after.st_ino,after.st_size)==(before.st_dev,before.st_ino,before.st_size) and len(raw)==spec['extent'] and sha(raw)==spec['sha256'];return raw
def spec(p,cap):
 i=plain(p);assert i.st_size<=cap;raw=p.read_bytes();assert len(raw)==i.st_size
 return dict(path=str(p),extent=len(raw),sha256=sha(raw))
def write(slot,raw):
 assert len(raw)<=slot['limit'];p=Path(slot['path']);before=plain(p);assert before.st_size==0 and (before.st_dev,before.st_ino)==(slot['device'],slot['inode'])
 with p.open('r+b') as f:
  now=os.fstat(f.fileno());assert now.st_size==0 and (now.st_dev,now.st_ino)==(before.st_dev,before.st_ino)
  assert f.write(raw)==len(raw);f.flush();os.fsync(f.fileno())
 return spec(p,slot['limit'])

class START(ctypes.Structure):
 _fields_=[('cb',wt.DWORD),('reserved',wt.LPWSTR),('desktop',wt.LPWSTR),('title',wt.LPWSTR),('x',wt.DWORD),('y',wt.DWORD),('xs',wt.DWORD),('ys',wt.DWORD),('xc',wt.DWORD),('yc',wt.DWORD),('fill',wt.DWORD),('flags',wt.DWORD),('show',wt.WORD),('reserved_n',wt.WORD),('reserved_ptr',ctypes.c_void_p),('input',wt.HANDLE),('output',wt.HANDLE),('error',wt.HANDLE)]
class STARTEX(ctypes.Structure):_fields_=[('startup',START),('attributes',ctypes.c_void_p)]
class PI(ctypes.Structure):_fields_=[('process',wt.HANDLE),('thread',wt.HANDLE),('pid',wt.DWORD),('tid',wt.DWORD)]

def kernel():
 assert os.name=='nt';k=ctypes.WinDLL('kernel32',use_last_error=True)
 signatures={'GetTickCount64':([],ctypes.c_ulonglong),'GetProcessTimes':([wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p],wt.BOOL),'SetHandleInformation':([wt.HANDLE,wt.DWORD,wt.DWORD],wt.BOOL),'InitializeProcThreadAttributeList':([ctypes.c_void_p,wt.DWORD,wt.DWORD,ctypes.POINTER(ctypes.c_size_t)],wt.BOOL),'UpdateProcThreadAttribute':([ctypes.c_void_p,wt.DWORD,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p],wt.BOOL),'DeleteProcThreadAttributeList':([ctypes.c_void_p],None),'CreateProcessW':([wt.LPCWSTR,wt.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,wt.BOOL,wt.DWORD,ctypes.c_void_p,wt.LPCWSTR,ctypes.c_void_p,ctypes.POINTER(PI)],wt.BOOL),'ResumeThread':([wt.HANDLE],wt.DWORD),'WaitForSingleObject':([wt.HANDLE,wt.DWORD],wt.DWORD),'GetExitCodeProcess':([wt.HANDLE,ctypes.POINTER(wt.DWORD)],wt.BOOL),'CloseHandle':([wt.HANDLE],wt.BOOL),'IsProcessInJob':([wt.HANDLE,wt.HANDLE,ctypes.POINTER(wt.BOOL)],wt.BOOL)}
 for n,(a,v) in signatures.items():getattr(k,n).argtypes=a;getattr(k,n).restype=v
 return k
def checked(ok):
 if not ok:raise ctypes.WinError(ctypes.get_last_error())
def birth(k,h):
 values=[ctypes.c_ulonglong() for unused in range(4)];checked(k.GetProcessTimes(h,*[ctypes.byref(v) for v in values]));assert 0<values[0].value<2**64;return values[0].value

def admission(registration,registration_sha256,review,review_sha256):
 assert registration['sha256']==registration_sha256 and review['sha256']==review_sha256
 rr=read(registration,128*1024);vr=read(review,128*1024);r=json.loads(rr);v=json.loads(vr);assert enc(r)==rr and enc(v)==vr
 assert r['schema']=='PILOT74-NEW-NATIVE-BOUNDARY-REGISTRATION-v1' and r['cases']==list(CASES) and r['worlds']==r['vm_steps']==0
 assert v['schema']=='PILOT74-INDEPENDENT-NATIVE-HARNESS-REVIEW-v1' and v['contract_sha256']==r['contract_sha256'] and v['harness_sha256']==r['harness_sha256'] and v['verdict']=='PASS' and v['cases']==list(CASES) and v['finite_admission'] is False
 # Receipt identity/execution ancestry is an external premise; these checks
 # never manufacture a reviewer, source grant, CI or finite registration.
 assert v['reviewer_identity'] and v['review_evidence'] and v['source_and_reservations_reviewed'] is True
 for pin in r['input_pins']:read(pin,pin['extent'])
 assert sha(Path(__file__).read_bytes())==r['harness_sha256'] and str(Path(__file__).resolve())==r['harness_path']
 assert r['parent_limits']==dict(memory_bytes=2048*MIB,cpu_seconds=60,wall_seconds=90,processes=4)
 assert r['per_case_wall_seconds']==5 and r['maximum_case_launches']==4 and r['new_groups_only'] is True
 assert r['source_sha256']==sha(enc(r['source_files'])) and r['configuration_sha256']==sha(enc(r['configuration'])) and r['artifact']['extent']<=512*1024
 read(r['python'],16*MIB);assert Path(sys.executable).resolve()==Path(r['python']['path']).resolve()==Path('D:/OraLab/tools/Python312/python.exe').resolve()
 read(r['artifact'],512*1024);assert r['artifact']['sha256']=='c22a3668dd57bedf2e55def8e39ad867e1ce6c2a4657c583bf067cd5cd46e391'
 assert r['slot_total_bytes']<=64*MIB and r['archive_limit']==r['restore_limit']==64*MIB and r['controller_limit']==8*MIB
 assert set(r['slots'])==set(r['expected_slot_names']) and len(set(x['path'] for x in r['slots'].values()))==len(r['slots'])
 assert r['finite_pilot_refused'] is True and r['valid_worker_registrations_allowed']==0
 return r

def origins(r,worker_main=False):
 root=Path(r['source_root'])
 for n,m in list(sys.modules.items()):
  if n=='experiments' or n.startswith('experiments.') or (worker_main and n=='__main__'):
   p=Path(m.__file__).resolve();relative=p.relative_to(root).as_posix();assert relative in r['source_files'] and sha(p.read_bytes())==r['source_files'][relative]

def one_case(r,name,owner):
 """Host retains Job handle for negative-case observation, not sole-owner proof."""
 entered=time.monotonic()
 import msvcrt,subprocess
 from experiments import process_limits as caps
 from experiments.digital_pilot74_output_capture_v2 import Capture
 k=kernel();root=Path(r['root']);pi=PI();job=None;attributes=None;initialized=False;fds=[];thread=None;sink=None;stream=None;command=None;original_birth=None;started=entered;usage=None;first=None;return_code=None;facts={};received=0;job_guard=threading.RLock()
 def stop_job():
  with job_guard:
   if job is not None and job.handle:job.terminate()
 def close_job():
  with job_guard:
   if job is not None:job.close()
 try:
  origin_tick=k.GetTickCount64();memory=1024*MIB if name=='wrong_root_limit_readback' else 2048*MIB
  job=caps.Job(caps.Limits(memory_bytes=memory,cpu_seconds=2400,processes=4,wall_seconds=5))
  br,bw=os.pipe();out_r,out_w=os.pipe();nul=os.open(os.devnull,os.O_RDONLY|os.O_BINARY);fds=[br,bw,out_r,out_w,nul]
  handles=[job.handle,msvcrt.get_osfhandle(br),msvcrt.get_osfhandle(out_w),msvcrt.get_osfhandle(nul)]
  for h in handles:checked(k.SetHandleInformation(h,1,1))
  n=ctypes.c_size_t();k.InitializeProcThreadAttributeList(None,2,0,ctypes.byref(n));assert n.value>0;attributes=ctypes.create_string_buffer(n.value);checked(k.InitializeProcThreadAttributeList(attributes,2,0,ctypes.byref(n)));initialized=True
  jobs=(wt.HANDLE*1)(job.handle);inherited=(wt.HANDLE*4)(*handles);checked(k.UpdateProcThreadAttribute(attributes,0,0x2000D,jobs,ctypes.sizeof(jobs),None,None));checked(k.UpdateProcThreadAttribute(attributes,0,0x20002,inherited,ctypes.sizeof(inherited),None,None))
  actual_start=origin_tick;fixture_start=actual_start
  if name=='expired_original_stop_window':assert actual_start>=3600000;fixture_start=actual_start-3600000
  request=r['registration_fixture'];command=[r['artifact']['path'],str(int(job.handle)),str(fixture_start),request['path'],str(request['extent']),'0'*64,str(handles[1])]
  grant=dict(version='PILOT74-NATIVE-CAPTURE-GRANT-v2',root=r['root'],source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],role=name,command_sha256=sha(enc(command)),operator_lock=owner,raw={key:r['slots']['raw/stdout/'+name+'.bin'][key] for key in ('path','limit','device','inode')},overflow={key:r['slots']['failure/native-first-output.bin'][key] for key in ('path','limit','device','inode')})
  write(r['slots']['raw/grants/'+name+'.json'],enc(grant));sink=Capture(grant,sha(enc(grant)),r['source_sha256'],r['configuration_sha256'],name,command)
  def drain():
   nonlocal received
   try:
    while True:
     block=stream.read(65536)
     if not block:sink.eof=True;break
     received+=len(block);sink.append(block)
     if received>MIB:stop_job()
   except BaseException as e:
    sink.errors.append(repr(e))
    try:stop_job()
    except BaseException as later:sink.errors.append(repr(later))
  si=STARTEX();si.startup.cb=ctypes.sizeof(si);si.startup.flags=0x100;si.startup.input=handles[3];si.startup.output=si.startup.error=handles[2];si.attributes=ctypes.cast(attributes,ctypes.c_void_p)
  line=ctypes.create_unicode_buffer(subprocess.list2cmdline(command));assert time.monotonic()-started<5,'Case setup consumed original5s deadline; do not create G';checked(k.CreateProcessW(r['artifact']['path'],line,None,None,True,0x80000|0x4|0x8000000,None,r['source_root'],ctypes.byref(si),ctypes.byref(pi)))
  original_birth=birth(k,pi.process);handed=original_birth+1 if name=='external_birth_mismatch' else original_birth;assert handed<2**64
  member=wt.BOOL();checked(k.IsProcessInJob(pi.process,job.handle,ctypes.byref(member)));assert member.value;actual=caps.ExtendedLimits();checked(caps.kernel().QueryInformationJobObject(job.handle,9,ctypes.byref(actual),ctypes.sizeof(actual),None));assert actual.job_memory==memory and actual.basic.job_cpu==2400*10_000_000 and actual.basic.active_processes==4 and actual.basic.flags&(0x4|0x8|0x200|0x2000)==(0x4|0x8|0x200|0x2000);facts.update(root_membership_observed=True,root_limit_readback=dict(memory_bytes=int(actual.job_memory),cpu_ticks=int(actual.basic.job_cpu),processes=int(actual.basic.active_processes),flags=int(actual.basic.flags)))
  facts.update(pid=pi.pid,creation_filetime_decimal=str(original_birth),handed_birth_decimal=str(handed),actual_case_start_tick=actual_start,fixture_original_tick=fixture_start,root_limits=vars(job.limits) if hasattr(job,'limits') else dict(memory_bytes=memory,cpu_seconds=2400,processes=4),root_job_membership_from_creation_requested=True,command=command)
  write(r['slots']['raw/native/'+name+'.start.json'],enc(facts))
  assert os.write(bw,struct.pack('<Q',handed))==8;os.close(bw);fds.remove(bw)
  stream=os.fdopen(out_r,'rb',buffering=0);fds.remove(out_r);thread=threading.Thread(target=drain,daemon=True);thread.start();assert time.monotonic()-started<5,'Case setup consumed original5s deadline; do not resume G';facts['setup_elapsed_seconds']=time.monotonic()-started;assert k.ResumeThread(pi.thread)==1
  os.close(out_w);fds.remove(out_w)
  while k.WaitForSingleObject(pi.process,10)==258:
   if time.monotonic()-started>=5:raise TimeoutError('NEW boundary case exceeded5s; closure authority incomplete until exact handles observed')
  assert k.WaitForSingleObject(pi.process,0)==0 and birth(k,pi.process)==original_birth;code=wt.DWORD();checked(k.GetExitCodeProcess(pi.process,ctypes.byref(code)));return_code=code.value
  thread.join(2);assert not thread.is_alive();capture=sink.finish();usage=job.usage()
  assert return_code==125 and capture['capture_complete'] and capture['eof'] and not capture['errors'] and received==0
  assert usage['started_processes']==1 and usage['active_before_close']==0,'Unexpected worker/descendant; no valid worker or World is permitted'
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
  if thread:thread.join(2)
  facts.update(case=name,command=command,pid=pi.pid or None,creation_filetime_decimal=None if original_birth is None else str(original_birth),exception=repr(e),traceback=''.join(traceback.format_exception(e)),closure_unknown=True,passed=False,available_capture_errors=[] if sink is None else sink.errors,raw_EOF_known=False if sink is None else sink.eof)
  try:write(r['slots']['failure/first-exception.json'],enc(facts))
  except BaseException as later:e.add_note('First exception write incomplete:'+repr(later))
  raise
 finally:
  # If a capture thread cannot join, its files/EOF are UNKNOWN. No final
  # archive acceptance is allowed while such a writer is active.
  errors=[]
  def cleanup(action):
   try:action()
   except BaseException as error:errors.append(repr(error))
  if job:cleanup(close_job)
  if thread and thread.is_alive():thread.join(2)
  if sink and not(thread and thread.is_alive()):cleanup(sink.close)
  if stream and not(thread and thread.is_alive()):cleanup(stream.close)
  for fd in fds:cleanup(lambda fd=fd:os.close(fd))
  if pi.thread:cleanup(lambda:checked(k.CloseHandle(pi.thread)))
  if pi.process:cleanup(lambda:checked(k.CloseHandle(pi.process)))
  if initialized:cleanup(lambda:k.DeleteProcThreadAttributeList(attributes))
  if thread and thread.is_alive():errors.append('Capture writer still active; no archive authority')
  if errors:
   if first is not None:first.add_note('Native cleanup incomplete:'+repr(errors))
   else:raise RuntimeError('Native cleanup incomplete:'+repr(errors))
 write(r['slots']['raw/native/'+name+'.json'],enc(facts));return facts

def worker(registration,registration_sha256,review,review_sha256):
 r=admission(registration,registration_sha256,review,review_sha256)
 from experiments import process_limits as caps
 limits=caps.ExtendedLimits();k=caps.kernel();caps.checked(k.QueryInformationJobObject(None,9,ctypes.byref(limits),ctypes.sizeof(limits),None));assert limits.job_memory==2048*MIB and limits.basic.job_cpu==60*10_000_000 and limits.basic.active_processes==4
 origins(r,True);owner=r['operator_lock'];read(owner,16384);assert kernel().GetTickCount64()>=3600000,'Expired-window fixture unavailable: abort before ALL case launches';results=[]
 for name in CASES:results.append(one_case(r,name,owner))
 origins(r,True)
 summary=dict(schema='PILOT74-NEW-NATIVE-BOUNDARY-SUMMARY-v1',cases=[dict(case=x['case'],exit_code=x['exit_code']) for x in results],worlds=0,vm_steps=0,positive_custody_qualified=False,recovery_qualified=False,finite_admission=False)
 write(r['slots']['raw/summary.json'],enc(summary));sys.stdout.buffer.write(enc(summary)+b'\n');sys.stdout.buffer.flush()

def archive_available(r,complete):
 root=Path(r['root']);rows=[]
 for name,slot in sorted(r['slots'].items()):
  path=Path(slot['path']);i=plain(path);assert (i.st_dev,i.st_ino)==(slot['device'],slot['inode']) and i.st_size<=slot['limit'];rows.append(dict(name=name,**spec(path,slot['limit'])))
 assert sum(x['extent'] for x in rows)<=64*MIB
 target=Path(r['archive_slot']['path']);assert plain(target).st_size==0
 with target.open('r+b') as output:
  with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED,allowZip64=False) as archive:
   for row in rows:
    assert len(row['name'])<=240 and row['name'].isascii() and '..' not in Path(row['name']).parts
    archive.writestr(row['name'],read(row,64*MIB))
  output.flush();os.fsync(output.fileno())
 assert target.stat().st_size<=r['archive_limit'];restored=0
 with zipfile.ZipFile(target) as archive:
  assert archive.namelist()==[x['name'] for x in rows]
  for row in rows:
   data=archive.read(row['name']);assert len(data)==row['extent'] and sha(data)==row['sha256'];write(r['restore_slots'][row['name']],data);restored+=len(data)
 assert restored<=r['restore_limit']
 for row in rows:assert sha(read(row,64*MIB))==row['sha256'] and spec(Path(r['restore_slots'][row['name']]['path']),64*MIB)['sha256']==row['sha256']
 return dict(available_files_exactly_restored=True,evidence_complete=complete,archive=spec(target,64*MIB))

def execute_registered(registration,registration_sha256,review,review_sha256):
 """Trusted host caller holds original operator lock; no self-issued review."""
 r=admission(registration,registration_sha256,review,review_sha256)
 from experiments import digital_pilot74_native_observed_v2 as native
 from experiments.digital_pilot74_output_capture_v2 import ParentCapture
 from experiments.process_limits import Limits
 origins(r);owner=r['operator_lock'];read(owner,16384)
 command=[sys.executable,'-B','-m','experiments.digital_pilot74_guardian_boundary_qualifier_v1','--worker',json.dumps(registration),registration_sha256,json.dumps(review),review_sha256]
 # Separate parent capture prevents concurrent parent/case writers sharing
 # the one first-case overflow slot. Its2MiB overflow stays in control8MiB.
 grant=dict(version='PILOT74-PARENT-CAPTURE-GRANT-v2',root=str(Path(r['root'])/'control'),source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],role='parent',command_sha256=sha(enc(command)),operator_lock=owner,raw={key:r['slots']['control/raw/stdout/parent.bin'][key] for key in ('path','limit','device','inode')},overflow={key:r['slots']['control/failure/native-first-output.bin'][key] for key in ('path','limit','device','inode')})
 write(r['slots']['control/grant.json'],enc(grant));write(r['slots']['raw/attempt.claimed'],b'ONE NEW BOUNDARY GROUP; NO RETRY\n')
 sink=ParentCapture(grant,sha(enc(grant)),r['source_sha256'],r['configuration_sha256'],'parent',command);first=None;result=None;proof=None
 try:
  result=native._run(command,Limits(**r['parent_limits']),r['source_root'],sink);write(r['slots']['control/native.json'],enc(result))
  assert result['exit_code']==0 and result['post_close_processes_exited'] and not result['timed_out'] and not result['supervisor_cpu_stop'] and not result['output_truncated'] and not result['stdout_limit_exceeded']
 except BaseException as error:
  first=error
  try:write(r['slots']['control/first-exception.json'],enc(dict(error=repr(error),traceback=''.join(traceback.format_exception(error)),native_result_missing=result is None,closure_unknown=result is None)))
  except BaseException as later:error.add_note('Outer exception custody incomplete:'+repr(later))
 finally:
  try:sink.close()
  except BaseException as error:
   if first is None:first=error
   else:first.add_note('Parent capture close incomplete:'+repr(error))
 # Only after the parent job and all capture writers have stopped. If the
 # native helper throws before a structured closure, never infer a complete
 # archive/restore from partial files; preserve available raw in place.
 if result is not None and result['post_close_processes_exited']:
  try:proof=archive_available(r,first is None)
  except BaseException as later:
   if first is None:first=later
 output=dict(schema='PILOT74-NEW-NATIVE-BOUNDARY-OUTER-v1',passed=first is None and proof is not None,first_exception=None if first is None else repr(first),native=result,archive=proof,full_native_or_recovery_qualified=False,worlds=0,vm_steps=0,finite_admission=False)
 write(r['terminal_slot'],enc(output));return output

if __name__=='__main__':
 assert len(sys.argv)==6 and sys.argv[1]=='--worker'
 worker(json.loads(sys.argv[2]),sys.argv[3],json.loads(sys.argv[4]),sys.argv[5])
