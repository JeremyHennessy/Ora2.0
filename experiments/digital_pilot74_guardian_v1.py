"""Source-only native guardian transport. NO automatic launch or qualification.

The callable host launcher requires separate pinned qualification/CI/finite
registration. It never creates registrations, replays roles or runs old checks.
"""
import copy,ctypes,hashlib,json,os,struct,sys
from pathlib import Path
from ctypes import wintypes as wt
from experiments import digital_pilot74_publication_reader_v2 as physical
MIB=1024**2
FRAME=65536
ARTIFACTS={'experiments/native/pilot74_guardian_v1.c','experiments/native/pilot74_guardian_v1.exe'}
_client=None

def artifact_name(name):
    return type(name) is str and name.isascii() and '..' not in name and '\\' not in name and ':' not in name and ((name.startswith('experiments/') and name.endswith('.py')) or name in ARTIFACTS)
def enc(v):return physical.encode(v)
def digest(b):return physical.digest(b)
def _kernel():
    assert os.name=='nt'
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    signatures={'CreateFileW':([wt.LPCWSTR,wt.DWORD,wt.DWORD,ctypes.c_void_p,wt.DWORD,wt.DWORD,wt.HANDLE],wt.HANDLE),'CloseHandle':([wt.HANDLE],wt.BOOL),'GetFileInformationByHandleEx':([wt.HANDLE,ctypes.c_int,ctypes.c_void_p,wt.DWORD],wt.BOOL),'SetHandleInformation':([wt.HANDLE,wt.DWORD,wt.DWORD],wt.BOOL),'GetTickCount64':([],ctypes.c_ulonglong),'GetProcessTimes':([wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p],wt.BOOL),'WaitForSingleObject':([wt.HANDLE,wt.DWORD],wt.DWORD),'GetExitCodeProcess':([wt.HANDLE,ctypes.POINTER(wt.DWORD)],wt.BOOL),'OpenProcess':([wt.DWORD,wt.BOOL,wt.DWORD],wt.HANDLE),'QueryFullProcessImageNameW':([wt.HANDLE,wt.DWORD,wt.LPWSTR,ctypes.POINTER(wt.DWORD)],wt.BOOL),'GetProcessId':([wt.HANDLE],wt.DWORD),'ResumeThread':([wt.HANDLE],wt.DWORD),'TerminateProcess':([wt.HANDLE,wt.UINT],wt.BOOL),'InitializeProcThreadAttributeList':([ctypes.c_void_p,wt.DWORD,wt.DWORD,ctypes.POINTER(ctypes.c_size_t)],wt.BOOL),'UpdateProcThreadAttribute':([ctypes.c_void_p,wt.DWORD,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p],wt.BOOL),'DeleteProcThreadAttributeList':([ctypes.c_void_p],None)}
    for name,(args,result) in signatures.items():getattr(k,name).argtypes=args;getattr(k,name).restype=result
    return k
def checked(ok):
    if not ok:raise ctypes.WinError(ctypes.get_last_error())
class ID(ctypes.Structure):_fields_=[('volume',ctypes.c_ulonglong),('identifier',ctypes.c_ubyte*16)]
def win32_id(path):
    p=Path(path);physical.plain(p)
    for parent in p.parents:physical.plain(parent,True)
    k=_kernel();handle=k.CreateFileW(str(p),0x80000000,0,None,3,0x00200000,None)
    if handle in (None,ctypes.c_void_p(-1).value):raise ctypes.WinError(ctypes.get_last_error())
    try:
        value=ID();checked(k.GetFileInformationByHandleEx(handle,18,ctypes.byref(value),ctypes.sizeof(value)))
        return format(value.volume,'016x')+':'+bytes(value.identifier).hex()
    finally:checked(k.CloseHandle(handle))
def _birth(k,handle):
    vals=[ctypes.c_ulonglong() for unused in range(4)]
    checked(k.GetProcessTimes(handle,*[ctypes.byref(v) for v in vals]));return vals[0].value
def _bind_peer(r,hello):
    assert hello['schema']=='PILOT74-GUARDIAN-HELLO-v1'
    k=_kernel();pid=hello['pid'];assert type(pid) is int and 0<pid<2**32
    handle=k.OpenProcess(0x1000|0x100000,False,pid);checked(handle)
    try:
        assert str(_birth(k,handle))==hello['creation_filetime_decimal'] and k.WaitForSingleObject(handle,0)==258
        name=ctypes.create_unicode_buffer(32768);n=wt.DWORD(len(name));checked(k.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(n)))
        assert Path(name.value).resolve()==Path(r['guardian']['artifact']['path']).resolve()
        physical.external(r['guardian']['artifact'],512*1024)
    finally:checked(k.CloseHandle(handle))

def normalize_native(wire):
    """Convert exact integer native wire ticks to host metrics, never VM floats."""
    assert type(wire) is dict and set(wire)=={'command','configuration_sha256','elapsed_ms','exit_code','pid','creation_filetime_decimal','schema','source_sha256','role','start','stdout_capture','user_cpu_ticks','peak_job_memory_bytes','active_before_close','started_processes','post_close_processes_exited','timed_out'}
    assert wire['schema']=='PILOT74-GUARDIAN-NATIVE-v1'
    assert type(wire['timed_out']) is bool and type(wire['post_close_processes_exited']) is bool
    assert 0<wire['pid']<2**32 and wire['exit_code']<2**32
    assert type(wire['command']) is list and all(type(v) is str and v for v in wire['command'])
    for key in ('source_sha256','configuration_sha256'):physical.checksum(wire[key])
    for key in ('pid','user_cpu_ticks','elapsed_ms','exit_code','active_before_close','started_processes','peak_job_memory_bytes'):assert type(wire[key]) is int and wire[key]>=0
    creation=wire['creation_filetime_decimal'];assert type(creation) is str and creation.isdecimal() and str(int(creation))==creation and 0<int(creation)<2**64
    capture=wire['stdout_capture'];assert type(capture) is dict and set(capture)=={'capture_complete','eof','errors','grant_sha256','overflow','raw','received_bytes','retained_bytes','schema','stdout_limit_exceeded'}
    assert capture['schema']=='PILOT74-NATIVE-CAPTURE-v2'
    for key in ('capture_complete','eof','stdout_limit_exceeded'):assert type(capture[key]) is bool
    for key in ('received_bytes','retained_bytes'):assert type(capture[key]) is int and capture[key]>=0
    assert capture['retained_bytes']<=capture['received_bytes']
    assert type(capture['errors']) is list and all(type(e) is str for e in capture['errors'])
    if capture['capture_complete']:assert capture['eof'] is True and capture['errors']==[] and capture['retained_bytes']==capture['received_bytes']
    for key,cap in (('raw',MIB),('overflow',24*MIB)):
        spec=capture[key];assert type(spec) is dict and set(spec)=={'path','extent','sha256'} and type(spec['extent']) is int and 0<=spec['extent']<=cap
        physical.checksum(spec['sha256'])
    physical.checksum(capture['grant_sha256'])
    return dict(schema='resource01-result-v1',platform='Windows',command=wire['command'],limits=dict(memory_bytes=1024*MIB,cpu_seconds=180,wall_seconds=300,processes=3),exit_code=wire['exit_code'],timed_out=wire['timed_out'],supervisor_cpu_stop=False,owned_pids_before_close=[wire['pid']],observed_job_processes=[dict(pid=wire['pid'],creation_filetime_decimal=creation)],post_close_processes_exited=wire['post_close_processes_exited'],usage=dict(user_cpu_seconds=wire['user_cpu_ticks']/10_000_000,windows_reported_peak_job_memory_bytes=wire['peak_job_memory_bytes'],active_before_close=wire['active_before_close'],started_processes=wire['started_processes'],configured_memory_bytes=1024*MIB,configured_cpu_ticks=180*10_000_000,configured_processes=3),elapsed_seconds=wire['elapsed_ms']/1000,stdout_capture=capture,stdout_limit_exceeded=capture['stdout_limit_exceeded'],output_bytes=capture['received_bytes'],retained_bytes=capture['retained_bytes'],output_extent_known=capture['eof'],output_truncated=not capture['capture_complete'],inline_output_complete=capture['received_bytes']<=MIB,guardian_start=wire['start'],guardian_wire=True,isolation_verified=False)

class Client:
    def __init__(self,r):
        assert os.name=='nt' and _client is None
        import msvcrt
        self.r=r;self.ordinal=0;self.is_ready=False;self.archiving=False;self.finished=False;self.results={}
        self.reader=os.fdopen(msvcrt.open_osfhandle(int(os.environ.pop('PILOT74_GUARDIAN_READ')),os.O_RDONLY|os.O_BINARY),'rb',buffering=0)
        self.writer=os.fdopen(msvcrt.open_osfhandle(int(os.environ.pop('PILOT74_GUARDIAN_WRITE')),os.O_WRONLY|os.O_BINARY),'wb',buffering=0)
        _bind_peer(r,self.exchange('HELLO'))
    def _read(self,n):
        chunks=[];left=n
        while left:
            part=self.reader.read(left)
            if not part:raise OSError('Guardian pipe EOF; available prefix retained, closure unknown')
            chunks.append(part);left-=len(part)
        return b''.join(chunks)
    def exchange(self,kind,**fields):
        value=dict(type=kind,source_sha256=self.r['source_sha256'],configuration_sha256=self.r['configuration_sha256'],**fields);raw=enc(value);assert len(raw)<=FRAME
        packet=struct.pack('<I',len(raw))+raw
        if self.writer.write(packet)!=len(packet):raise OSError('Partial guardian frame; never retry')
        size=self._read(4)
        if len(size)!=4:raise OSError('Missing guardian frame header; closure unknown')
        n=struct.unpack('<I',size)[0];assert 0<n<=FRAME
        raw=self._read(n)
        if len(raw)!=n:raise OSError('Partial guardian frame; closure unknown')
        result=physical.parse(raw,FRAME)
        if result.get('schema')=='PILOT74-GUARDIAN-FIRST-FAILURE-v1':raise RuntimeError('Guardian refused; available native failure evidence retained: '+repr(result))
        return result
    def ready(self,controller):
        assert not self.is_ready and not self.archiving
        preflight=preflight_all(controller)
        slots=[]
        for row in controller.plan['roles']:
            name=row['name']
            for leaf in ('native/'+name+'.start.json','native/'+name+'.json','stdout/'+name+'.bin'):
                slot=controller.slots['raw/'+leaf];slots.append(dict(path=slot['path'],limit=slot['limit'],win32_id=win32_id(slot['path'])))
        for leaf in ('failure/native-first-output.bin','failure/native-first-failure.json'):
            slot=controller.slots[leaf];slots.append(dict(path=slot['path'],limit=slot['limit'],win32_id=win32_id(slot['path'])))
        preflight['native_slots']=slots
        controller.save('metadata/guardian-preflight.json',enc(preflight))
        result=self.exchange('READY',slots=slots,preflight=controller.spec('metadata/guardian-preflight.json',FRAME));assert result['schema']=='PILOT74-GUARDIAN-READY-v1';self.is_ready=True
    def run(self,command,limits,cwd,*,capture_grant,capture_seal,source_sha256,configuration_sha256,role,request):
        assert self.is_ready and not self.archiving and self.ordinal<26
        assert vars(limits)==dict(memory_bytes=1024*MIB,cpu_seconds=180,processes=3,wall_seconds=300)
        assert (source_sha256,configuration_sha256)==(self.r['source_sha256'],self.r['configuration_sha256'])
        result=self.exchange('ROLE_REQUEST',ordinal=self.ordinal,role=role,command=command,cwd=str(cwd),request=request,capture_grant=capture_grant,capture_seal=capture_seal)
        assert result['schema']=='PILOT74-GUARDIAN-ROLE-RESULT-v1' and result['ordinal']==self.ordinal and result['role']==role
        self.ordinal+=1;raw=physical.external(result['native'],MIB);wire=physical.parse(raw,MIB)
        assert wire['source_sha256']==source_sha256 and wire['configuration_sha256']==configuration_sha256 and wire['role']==role and wire['command']==command
        n=normalize_native(wire);n['native_spec']=result['native']
        capture=n['stdout_capture'];assert capture['grant_sha256']==capture_seal
        n['output']=physical.external(capture['raw'],MIB).decode('utf8',errors='replace')
        self.results[role]=n;return n
    def barrier(self,complete):
        if self.archiving:return
        kind='ARCHIVE_BARRIER' if complete else 'STOP'
        assert not complete or self.ordinal==26
        value=self.exchange(kind);assert value['schema']=='PILOT74-GUARDIAN-BARRIER-v1';self.archiving=True
    def finish(self,result=None):
        if self.finished:return
        if not self.archiving:self.barrier(False)
        value=self.exchange('FINISH',archive=result,complete=False if result is None else result['evidence_complete']);assert value['schema']=='PILOT74-GUARDIAN-FINISH-v1';self.finished=True

def connect(r):
    global _client
    _client=Client(r);return _client
def current():
    assert _client is not None,'No native guardian connection; old outer/bootstrap path REFUSED'
    return _client
def verify_native(slots,name,n):
    slot=slots['raw/native/'+name+'.json'];spec=n['native_spec'];assert spec['path']==slot['path'] and spec['extent']<=slot['limit']
    raw,identity=physical.read_exact(spec['path'],{k:spec[k] for k in ('extent','sha256')},slot['limit']);assert identity[:2]==(slot['device'],slot['inode'])
    assert normalize_native(physical.parse(raw,slot['limit']))['command']==n['command']
    assert n['stdout_capture']['capture_complete'] is True and n['output_truncated'] is False and n['stdout_limit_exceeded'] is False
    assert n['usage']['started_processes']==1 and n['usage']['active_before_close']==0 and n['post_close_processes_exited'] is True
    return spec

def preflight_all(c):
    """Actual source/path/slot templates before any valid role, no VM calls."""
    from experiments import digital_pilot74_finite_requests_v2 as requests
    from experiments import digital_pilot74_parent_ledger_v2 as ledger
    class Shadow(requests.Requests):
        def spec(self,name,cap):
            slot=self.slots['raw/'+name];assert slot['limit']<=cap
            return dict(path=slot['path'],extent=slot['limit'],sha256='f'*64)
    s=Shadow(c.root,c.slots,c.r['revision'],c.r['source_files'],c.rows,c.r['operator_lock'])
    def wide(v):
        if type(v) is dict:return {k:(2**128-1 if k in ('device','inode') else wide(x)) for k,x in v.items()}
        if type(v) is list:return [wide(x) for x in v]
        return v
    results=[]
    for row in c.plan['roles']:
        name=row['name'];export='restored' if name.startswith('restored/') else 'original';extra=[]
        if name.endswith('/prepared'):module='digital_pilot74_source_ready_v2';request=s.readiness(export)
        elif name.startswith(('original/','restored/')):
            suffix=name.split('/')[1];kind=next(k for k in ('generate','audit','resume') if suffix.startswith(k));cut=None if kind=='generate' else int(suffix[len(kind):]);module='digital_pilot74_child';request=s.task(export,kind,cut)
        elif name=='closed-projection-publication-audit':module='digital_pilot74_closed_audit_child_v2';request=s.closed(s.spec('metadata/publication/registration-3.json',32768))
        else:
            kind,fault=('sequence','normal') if name=='normal-sequence' else name.split('/');module='digital_pilot74_journal_observed_child_v2';initial=dict(path=c.slots['raw/metadata/initial-commit/'+name+'.json']['path'],extent=16384,sha256='f'*64);request,seal=s.journal(kind,fault,initial);extra=[seal]
        encoded=enc(wide(request));assert len(encoded)<=c.slots['raw/requests/'+name+'.json']['limit']
        spec=dict(path=c.slots['raw/requests/'+name+'.json']['path'],extent=len(encoded),sha256='f'*64)
        command=[c.r['python']['path'],'-B',str(Path(c.exported['roots'][export])/'experiments/digital_pilot74_entrypoint_v2.py'),module,spec['path'],str(spec['extent']),spec['sha256']]+extra
        capture=ledger.capture_grant(c.slots,c.root,c.r['source_sha256'],c.r['configuration_sha256'],name,command,c.r['operator_lock'])
        grant=enc(wide(dict(request=spec,command=command,capture=capture)));frame=enc(wide(dict(type='ROLE_REQUEST',source_sha256=c.r['source_sha256'],configuration_sha256=c.r['configuration_sha256'],ordinal=25,role=name,command=command,cwd=c.exported['roots'][export],request=spec,capture_grant=capture['grant'],capture_seal=capture['seal'])))
        assert len(grant)<=c.slots['raw/metadata/grants/'+name+'.json']['limit'] and len(frame)<=FRAME and len(enc(command))<=12000
        native_bound=len(enc(command))+12*2048+16384
        assert native_bound<=960*1024
        results.append(dict(role=name,request_bound=len(encoded),grant_bound=len(grant),frame_bound=len(frame),native_record_bound=native_bound))
    assert len(results)==26 and len(enc(results))<=FRAME
    return dict(schema='PILOT74-GUARDIAN-PREFLIGHT-v1',source_sha256=c.r['source_sha256'],configuration_sha256=c.r['configuration_sha256'],roles=results,source_rows=c.rows,archive_bound=c.plan['archive_and_restore_bound'],execution_authority=False,peak_fit_qualified=False)

def validate_host_registration(spec,expected):
    """External pins are prerequisites; this creates no authority or registration."""
    assert spec['sha256']==expected and os.name=='nt'
    raw=physical.external(spec,FRAME);r=physical.parse(raw,FRAME)
    assert r['schema']=='PILOT74-FINITE-REGISTRATION-v2' and r['mode']=='finite_qualification'
    from experiments import digital_pressure71_scientific_child as boundary
    assert boundary.verify_source(r['source_root'],r['source_files'])==r['source_sha256']
    assert ARTIFACTS<=set(r['source_files']) and r['source_files']['experiments/native/pilot74_guardian_v1.exe']==r['guardian']['artifact']['sha256']
    assert r['guardian']['version']=='PILOT74-NATIVE-GUARDIAN-CONFIG-v1'
    assert Path(r['guardian']['artifact']['path'])==Path(r['source_root'])/'experiments/native/pilot74_guardian_v1.exe'
    physical.external(r['guardian']['artifact'],512*1024)
    build=physical.parse(physical.external(r['guardian']['build_review'],FRAME),FRAME)
    assert build['schema']=='PILOT74-GUARDIAN-BUILD-REVIEW-v1' and build['verdict']=='PASS' and build['revision']==r['revision'] and build['artifact_sha256']==r['guardian']['artifact']['sha256'] and build['old_checks_rerun'] is False
    assert set(r['reviews'])=={'interface','custody','union_failure','source_fit','whole_source_ci'}
    for kind,value in r['reviews'].items():
        v=physical.parse(physical.external(value,128*1024),128*1024)
        assert v['schema']=='PILOT74-EXTERNAL-GATE-REVIEW-v2' and v['kind']==kind and v['verdict']=='PASS' and v['revision']==r['revision'] and v['source_sha256']==r['source_sha256'] and v['configuration_sha256']==r['configuration_sha256']
        if kind=='whole_source_ci':assert v['head_sha']==r['revision'] and v['conclusion']=='success' and v['old_suites_rerun'] is False
        else:
            assert v['archive_restore_exact'] is True and v['native_records']
            for n in v['native_records']:
                native=physical.parse_native(physical.external(n,MIB),MIB);assert native['exit_code']==0 and native['post_close_processes_exited'] is True and native['output_truncated'] is False and native['timed_out'] is False
    lock=r['operator_lock'];_,identity=physical.read_exact(lock['path'],{k:lock[k] for k in ('extent','sha256')},16384);assert identity[:2]==(lock['device'],lock['inode'])
    assert win32_id(lock['path'])==r['guardian']['lock_win32_id']
    assert Path(r['python']['path']).resolve()==Path(sys.executable).resolve()==Path('D:/OraLab/tools/Python312/python.exe').resolve();physical.external(r['python'],16*MIB)
    return r

def launch_guardian(spec,expected):
    """Trusted host boundary only. No task-file writes outside the root Job.

    No CLI invokes this; actual source/native review and separate registration
    remain required. Caller must retain returned native birth/exit transport.
    """
    r=validate_host_registration(spec,expected)
    from experiments import process_limits as caps
    import msvcrt,subprocess
    k=_kernel();limits=caps.Limits(memory_bytes=2048*MIB,cpu_seconds=2400,processes=4,wall_seconds=3600)
    job=None;birth_read=birth_write=None
    class START(ctypes.Structure):_fields_=[('cb',wt.DWORD),('reserved',wt.LPWSTR),('desktop',wt.LPWSTR),('title',wt.LPWSTR),('x',wt.DWORD),('y',wt.DWORD),('xs',wt.DWORD),('ys',wt.DWORD),('xc',wt.DWORD),('yc',wt.DWORD),('fill',wt.DWORD),('flags',wt.DWORD),('show',wt.WORD),('reserved_n',wt.WORD),('reserved_ptr',ctypes.c_void_p),('input',wt.HANDLE),('output',wt.HANDLE),('error',wt.HANDLE)]
    class STARTEX(ctypes.Structure):_fields_=[('startup',START),('attributes',ctypes.c_void_p)]
    class PI(ctypes.Structure):_fields_=[('process',wt.HANDLE),('thread',wt.HANDLE),('pid',wt.DWORD),('tid',wt.DWORD)]
    k.CreateProcessW.argtypes=[wt.LPCWSTR,wt.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,wt.BOOL,wt.DWORD,ctypes.c_void_p,wt.LPCWSTR,ctypes.c_void_p,ctypes.POINTER(PI)];k.CreateProcessW.restype=wt.BOOL
    size=ctypes.c_size_t();k.InitializeProcThreadAttributeList(None,2,0,ctypes.byref(size));attrs=ctypes.create_string_buffer(size.value);initialized=False;pi=PI();first_failure=None
    try:
        job=caps.Job(limits);birth_read,birth_write=os.pipe();read_handle=msvcrt.get_osfhandle(birth_read);os.set_handle_inheritable(read_handle,True);checked(k.SetHandleInformation(job.handle,1,1))
        checked(k.InitializeProcThreadAttributeList(attrs,2,0,ctypes.byref(size)));initialized=True
        jobs=(wt.HANDLE*1)(job.handle);handles=(wt.HANDLE*2)(job.handle,read_handle)
        checked(k.UpdateProcThreadAttribute(attrs,0,0x2000D,jobs,ctypes.sizeof(jobs),None,None));checked(k.UpdateProcThreadAttribute(attrs,0,0x20002,handles,ctypes.sizeof(handles),None,None))
        t0=k.GetTickCount64();command=[r['guardian']['artifact']['path'],str(int(job.handle)),str(t0),spec['path'],str(spec['extent']),spec['sha256'],str(read_handle)]
        line=ctypes.create_unicode_buffer(subprocess.list2cmdline(command));start=STARTEX();start.startup.cb=ctypes.sizeof(start);start.attributes=ctypes.cast(attrs,ctypes.c_void_p)
        checked(k.CreateProcessW(None,line,None,None,True,0x80000|0x4|0x8,None,r['source_root'],ctypes.byref(start),ctypes.byref(pi)))
        birth=_birth(k,pi.process);packet=struct.pack('<Q',birth)
        if os.write(birth_write,packet)!=len(packet):raise OSError('Partial external birth handoff; never retry')
        os.close(birth_write);birth_write=None
        assert k.ResumeThread(pi.thread)==1
        # Retain the external Job handle until actual whole-tree closure.
        # A guardian exit alone cannot establish descendant closure, and an
        # exception must still be able to terminate the entire owned tree.
        # Actual guardian native watchdog owns the absolute deadline. Host wait
        # has no task writer, bootstrap or extra experiment role.
        if k.WaitForSingleObject(pi.process,max(0,int(t0+3600000-k.GetTickCount64())))!=0:raise RuntimeError('Guardian closure UNKNOWN; do not claim complete evidence')
        code=wt.DWORD();checked(k.GetExitCodeProcess(pi.process,ctypes.byref(code)))
        usage=job.usage()
        if usage['active_before_close']!=0:raise RuntimeError('Guardian exited with active descendants; whole-tree closure UNKNOWN')
        return dict(schema='PILOT74-EXTERNAL-GUARDIAN-EXIT-v1',command=command,pid=pi.pid,creation_filetime_decimal=str(birth),exit_code=code.value,process_handle_signaled=True,usage=usage,post_close_processes_exited=True,registration_sha256=expected,external_native_provenance_required=True,publication_accepted=False,live_attachment=False)
    except BaseException as first:
        first_failure=first
        # Exact owned Job, not just G: W/C may still hold inherited handles.
        # The original failure remains authoritative if termination also fails.
        try:
            if job is not None:job.terminate()
        except BaseException as later:
            first.add_note('Whole Job termination failed; closure UNKNOWN: '+repr(later))
            if pi.process and k.WaitForSingleObject(pi.process,0)==258:
                try:checked(k.TerminateProcess(pi.process,125))
                except BaseException as fallback:first.add_note('Exact guardian fallback failed: '+repr(fallback))
        # No extended deadline, retry or asserted closure after an exception.
        raise
    finally:
        cleanup=[]
        if job is not None and job.handle:cleanup.append(('Job',job.close))
        if pi.thread:cleanup.append(('thread',lambda:checked(k.CloseHandle(pi.thread))))
        if pi.process:cleanup.append(('process',lambda:checked(k.CloseHandle(pi.process))))
        if initialized:cleanup.append(('attributes',lambda:k.DeleteProcThreadAttributeList(attrs)))
        if birth_read is not None:cleanup.append(('birth-read',lambda:os.close(birth_read)))
        if birth_write is not None:cleanup.append(('birth-write',lambda:os.close(birth_write)))
        errors=[]
        for name,close in cleanup:
            try:close()
            except BaseException as error:errors.append(name+': '+repr(error))
        if errors:
            if first_failure is not None:first_failure.add_note('Native cleanup incomplete; closure UNKNOWN: '+repr(errors))
            else:raise OSError('Native cleanup incomplete; closure UNKNOWN: '+repr(errors))
