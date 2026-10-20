"""Bounded notifications for a fresh owned Job, never identity from PID alone.
No native calls on import. Notifications may be lost; no complete census claim.
"""
import ctypes,json,threading,time
from ctypes import wintypes as w

def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
class PortAssociation(ctypes.Structure):
 _fields_=[('key',ctypes.c_void_p),('port',w.HANDLE)]
class JobEvents:
 def __init__(self,job,stop_job):
  from experiments.digital_pilot74_guardian_boundary_qualifier_v2 import kernel
  self.k=kernel();self.job=job;self.stop_job=stop_job;self.port=None;self.job_handle=None;self.thread=None;self.finished=False
  self.handles=[];self.rows=[];self.errors=[];self.stop=threading.Event();self.ready=threading.Event();self.complete=True
  k=self.k
  for name,args,result in [('GetCurrentProcess',[],w.HANDLE),('DuplicateHandle',[w.HANDLE,w.HANDLE,w.HANDLE,ctypes.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD],w.BOOL),('TerminateJobObject',[w.HANDLE,w.UINT],w.BOOL),('CreateIoCompletionPort',[w.HANDLE,w.HANDLE,ctypes.c_size_t,w.DWORD],w.HANDLE),('GetQueuedCompletionStatus',[w.HANDLE,ctypes.POINTER(w.DWORD),ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_void_p),w.DWORD],w.BOOL),('PostQueuedCompletionStatus',[w.HANDLE,w.DWORD,ctypes.c_size_t,ctypes.c_void_p],w.BOOL),('SetInformationJobObject',[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD],w.BOOL)]:
   f=getattr(k,name);f.argtypes=args;f.restype=result
 def checked(self,v):
  if not v:raise ctypes.WinError(ctypes.get_last_error())
  return v
 def fail(self,where,error):
  self.complete=False
  if len(self.errors)<32:self.errors.append(dict(where=where,error=repr(error)))
  else:self.stop.set()
 def start(self):
  assert self.port is None and not self.finished
  try:
   duplicate=w.HANDLE();current=self.k.GetCurrentProcess()
   self.checked(self.k.DuplicateHandle(current,self.job.handle,current,ctypes.byref(duplicate),0,False,2))
   self.job_handle=duplicate.value # immutable until the reader has joined
   self.stop_job=lambda:self.checked(self.k.TerminateJobObject(self.job_handle,125))
   self.port=self.checked(self.k.CreateIoCompletionPort(w.HANDLE(-1),None,0,1))
   association=PortAssociation(1,self.port)
   self.checked(self.k.SetInformationJobObject(self.job_handle,7,ctypes.byref(association),ctypes.sizeof(association)))
   self.thread=threading.Thread(target=self.collect,daemon=True);self.thread.start()
   assert self.ready.wait(.5),'Event reader readiness unavailable before CreateProcess'
  except BaseException as first:
   self.stop.set()
   if self.port:
    try:self.checked(self.k.PostQueuedCompletionStatus(self.port,0,2,None))
    except BaseException as later:first.add_note('Startup wake:'+repr(later))
   if self.thread and self.thread.ident is not None:self.thread.join(1)
   if self.port and not(self.thread and self.thread.is_alive()):
    try:self.checked(self.k.CloseHandle(self.port));self.port=None
    except BaseException as later:first.add_note('Startup port close:'+repr(later))
   if self.job_handle and not(self.thread and self.thread.is_alive()):
    try:self.checked(self.k.CloseHandle(self.job_handle));self.job_handle=None
    except BaseException as later:first.add_note('Startup duplicate Job close:'+repr(later))
   raise
 def live_member(self,pid):
  row=dict(notification_pid=pid,observed_monotonic_ns=time.monotonic_ns(),handle_opened=False,actual_pid=None,birth=None,image=None,membership=None,errors=[])
  # Keep every opened handle through finalization. No replacement or PID reuse
  # retry; this bounds lifetime query handles, not just simultaneous queries.
  if len(self.handles)>=4:raise RuntimeError('Lifetime query-handle bound4 exceeded')
  h=self.k.OpenProcess(0x1000|0x100000,False,pid)
  if not h:
   row['errors'].append(dict(field='OpenProcess',error=repr(ctypes.WinError(ctypes.get_last_error()))));self.complete=False;return row
  self.handles.append(h);row['handle_opened']=True
  def attempt(field,query):
   try:row[field]=query()
   except BaseException as e:row['errors'].append(dict(field=field,error=repr(e)));self.complete=False
  def actual_pid():
   actual=int(self.checked(self.k.GetProcessId(h)));assert actual==pid;return actual
  def membership():
   member=w.BOOL();self.checked(self.k.IsProcessInJob(h,self.job_handle,ctypes.byref(member)));assert member.value;return True
  def born():
   values=[ctypes.c_ulonglong() for _ in range(4)];self.checked(self.k.GetProcessTimes(h,*[ctypes.byref(x) for x in values]));return str(values[0].value)
  def image():
   text=ctypes.create_unicode_buffer(1024);n=w.DWORD(1024);self.checked(self.k.QueryFullProcessImageNameW(h,0,text,ctypes.byref(n)));assert 0<n.value<1024;return text[:n.value]
  for field,query in [('actual_pid',actual_pid),('membership',membership),('birth',born),('image',image)]:attempt(field,query)
  row['identity_scope']='Current opened handle independently checked; eventPID-to-handle correspondence not guaranteed by notification alone'
  return row
 def collect(self):
  self.ready.set()
  try:
   while True:
    code=w.DWORD();key=ctypes.c_size_t();value=ctypes.c_void_p()
    ok=self.k.GetQueuedCompletionStatus(self.port,ctypes.byref(code),ctypes.byref(key),ctypes.byref(value),20)
    if not ok:
     error=ctypes.get_last_error()
     if error==258:
      if self.stop.is_set():break
      continue
     raise ctypes.WinError(error)
    if key.value==2:break
    if key.value!=1:raise RuntimeError('Foreign completion key')
    if len(self.rows)>=32:raise RuntimeError('Event reservation32 exhausted')
    row=dict(message=int(code.value),notification_pid=int(value.value or 0),observed_monotonic_ns=time.monotonic_ns())
    self.rows.append(row)
    if code.value==6:row['current_member_handle']=self.live_member(row['notification_pid'])
    if len(enc(dict(events=self.rows,errors=self.errors)))>60000:raise RuntimeError('Full event encoding exceeds60000; stop without slicing')
  except BaseException as e:
   self.fail('collector',e)
   try:self.stop_job()
   except BaseException as later:self.fail('collector-stop',later)
 def finish(self):
  assert not self.finished;self.finished=True;self.stop.set()
  if self.port:
   try:self.checked(self.k.PostQueuedCompletionStatus(self.port,0,2,None))
   except BaseException as e:self.fail('wake',e)
  if self.thread and self.thread.ident is not None:self.thread.join(1)
  joined=not(self.thread and self.thread.is_alive())
  if not joined:self.fail('join',RuntimeError('Event reader still active; handles/port retained, evidence incomplete'))
  else:
   for h in self.handles:
    try:self.checked(self.k.CloseHandle(h))
    except BaseException as e:self.fail('close-query-handle',e)
   if self.port:
    try:self.checked(self.k.CloseHandle(self.port));self.port=None
    except BaseException as e:self.fail('close-port',e)
   if self.job_handle:
    try:self.checked(self.k.CloseHandle(self.job_handle));self.job_handle=None
    except BaseException as e:self.fail('close-duplicate-job',e)
  out=dict(schema='PILOT74-BOUNDED-JOB-EVENT-OBSERVATION-v1',monitor_complete=self.complete and joined,reader_joined=joined,events=self.rows,errors=self.errors,query_handles_opened=len(self.handles),max_query_handles=4,max_events=32,delivery_guaranteed=False,complete_process_census_claimed=False,pid_notification_is_identity=False)
  # Acceptance and custody are separate: always RETURN the full body, even
  # beyond the dedicated leaf ceiling. Caller retains it in its precharged
  # first-failure/final-case body (1MiB final hard ceiling), never slicing.
  out['dedicated_limit_bytes']=65536;out['dedicated_limit_exceeded']=False
  out['required_encoded_extent']=0
  while out['required_encoded_extent']!=len(enc(out)):
   out['required_encoded_extent']=len(enc(out))
  if out['required_encoded_extent']>65536:
   out['dedicated_limit_exceeded']=True;out['monitor_complete']=False
   while out['required_encoded_extent']!=len(enc(out)):
    out['required_encoded_extent']=len(enc(out))
  return out
