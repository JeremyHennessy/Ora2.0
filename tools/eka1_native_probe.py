"""New finite, source-sealed SYNTHETIC OS qualification. No scientific imports.

The real registered original and World path are deliberately not admitted.
One process, one physical ledger, one immutable nine-case catalog. Historical
birth precharges remain preserved. Inline compilation is now retired because
its opaque helper attempts cannot satisfy pre-effect attempted-birth custody.
The native binary is bound to that ledger identity/hash, owner birth and case
markers. This is not a sandbox against the Windows account administrator.
"""
import ctypes
from ctypes import wintypes as wt
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import eka1_native_owner_candidate as owner_source
from experiments.process_limits import Job, Limits
from tools.eka1_cpu_accounting import RootCpuAttempt, CpuAccountingFailure

CASES = ('ok', 'failed-create', 'wall', 'cpu', 'memory', 'output', 'tree', 'guardian-stall', 'python-owner-stall')
SOURCE_FILES = ('tools/eka1_native_probe.py', 'tools/eka1_probe_child.py',
                'tools/eka1_native_owner_candidate.py', 'tools/eka1_cumulative_reservations.py',
                'experiments/process_limits.py', 'experiments/native/eka1_probe_guardian.c',
                'experiments/native/eka1_probe_owner_watchdog.c', 'tools/eka1_cpu_accounting.py',
                'tools/eka1_cpu_grant_transport.py', 'tools/eka1_prebuilt_cpu_artifact.py',
                'tools/eka1_runtime_capsule.py','experiments/native/eka1_runtime_capsule.h',
                'tools/eka1_external_settlement.py')
_used_cases=set()
_case_lock=threading.RLock()
_owner_watchdog=None
_owner_watchdog_started=False
_evidence_directory=None
_execution_consumed=False


def native_admission(transport=None):
    if transport is not None:
        from tools.eka1_cpu_grant_transport import CpuGrantTransport
        if type(transport) is not CpuGrantTransport:raise TypeError('Exact once-bound transport required')
        preflight=transport.preflight()
        raise owner_source.NativeQualificationRequired('NOT_READY: '+','.join(preflight['unqualified']))
    raise owner_source.NativeQualificationRequired('NOT_READY: source-only candidate; fresh immutable native assignment grant not supplied')


def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(path, value):
    raw = owner_source.canonical(value)
    if len(raw)>1024**2:raise ValueError('Evidence record exceeds reserved1MiB')
    with Path(path).open('xb') as f:
        if f.write(raw) != len(raw): raise OSError('Short evidence write')
        f.flush(); os.fsync(f.fileno())


def plain(path):
    for p in (Path(path), *Path(path).parents):
        info = p.lstat()
        if p.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Reparse ancestry refused')


def custody():
    paths = [ROOT / p for p in SOURCE_FILES]
    paths += [ROOT / ('tests/'+name) for name in (
        'test_eka1_cpu_accounting.py','test_eka1_cpu_grant_transport.py',
        'test_eka1_native_probe_contract.py','test_eka1_first_failure_custody.py',
        'test_eka1_native_owner_candidate.py','test_eka1_reservation_source_integrity.py',
        'test_eka1_prebuilt_cpu_artifact.py','test_eka1_runtime_capsule.py',
        'test_eka1_external_settlement.py')]
    python = Path(sys.executable).resolve()
    paths += [python, *python.parent.glob('python*.dll')]
    # Observe the isolated interpreter's standard-library and extension source
    # closure. Hashes are custody observations, not proof against privileged
    # replacement or proof every possible Windows dependency was enumerated.
    for sub in ('Lib', 'DLLs'):
        paths += [p for p in (python.parent/sub).rglob('*') if p.is_file() and
                  p.suffix in ('.py', '.pyd', '.dll', '.zip') and
                  'site-packages' not in p.parts and '__pycache__' not in p.parts]
    result = {}
    for p in paths:
        plain(p); result[str(p)] = sha(p.read_bytes())
    return result


class START(ctypes.Structure):
    _fields_ = [('cb',wt.DWORD),('reserved',wt.LPWSTR),('desktop',wt.LPWSTR),('title',wt.LPWSTR),
        ('x',wt.DWORD),('y',wt.DWORD),('xs',wt.DWORD),('ys',wt.DWORD),('xc',wt.DWORD),('yc',wt.DWORD),
        ('fill',wt.DWORD),('flags',wt.DWORD),('show',wt.WORD),('reserved_n',wt.WORD),
        ('reserved_ptr',ctypes.c_void_p),('input',wt.HANDLE),('output',wt.HANDLE),('error',wt.HANDLE)]
class STARTEX(ctypes.Structure): _fields_ = [('startup',START),('attributes',ctypes.c_void_p)]
class PI(ctypes.Structure): _fields_ = [('process',wt.HANDLE),('thread',wt.HANDLE),('pid',wt.DWORD),('tid',wt.DWORD)]
class FILEID(ctypes.Structure): _fields_ = [('volume',ctypes.c_ulonglong),('identifier',ctypes.c_ubyte*16)]


def kernel():
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    definitions = {
        'CreateProcessW':([wt.LPCWSTR,wt.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,wt.BOOL,wt.DWORD,ctypes.c_void_p,wt.LPCWSTR,ctypes.c_void_p,ctypes.POINTER(PI)],wt.BOOL),
        'InitializeProcThreadAttributeList':([ctypes.c_void_p,wt.DWORD,wt.DWORD,ctypes.POINTER(ctypes.c_size_t)],wt.BOOL),
        'UpdateProcThreadAttribute':([ctypes.c_void_p,wt.DWORD,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p],wt.BOOL),
        'DeleteProcThreadAttributeList':([ctypes.c_void_p],None),
        'GetTickCount64':([],ctypes.c_ulonglong),
        'CloseHandle':([wt.HANDLE],wt.BOOL),
        'OpenProcess':([wt.DWORD,wt.BOOL,wt.DWORD],wt.HANDLE),
        'GetFileInformationByHandleEx':([wt.HANDLE,ctypes.c_int,ctypes.c_void_p,wt.DWORD],wt.BOOL),
        'GetProcessTimes':([wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p],wt.BOOL),
        'GetProcessId':([wt.HANDLE],wt.DWORD),
        'IsProcessInJob':([wt.HANDLE,wt.HANDLE,ctypes.POINTER(wt.BOOL)],wt.BOOL),
        'ResumeThread':([wt.HANDLE],wt.DWORD),
        'WaitForSingleObject':([wt.HANDLE,wt.DWORD],wt.DWORD),
        'GetExitCodeProcess':([wt.HANDLE,ctypes.POINTER(wt.DWORD)],wt.BOOL)}
    for name,(args,result) in definitions.items():
        getattr(k,name).argtypes=args; getattr(k,name).restype=result
    return k


def checked(ok):
    if not ok: raise ctypes.WinError(ctypes.get_last_error())


def compiler_command(out,phase,setup,line,link_line):
    """Retained historical formatter fixture only; no execution path uses it."""
    # cmd.exe does not use the C argv escaping applied by subprocess to lists.
    # Keep quotes inside a retained fixed script, never an argv argument.
    batch=out/('build-'+phase+'.cmd')
    if any(c.isspace() or c in '&|<>^%!"' for c in str(batch)):
        raise ValueError('Fixed build script path must be plain and contain no whitespace')
    raw=('@echo off\r\nset "VSCMD_SKIP_SENDTELEMETRY=1"\r\ncall "'+str(setup)+'" >nul\r\nif errorlevel 1 exit /b %errorlevel%\r\n'+line+'\r\nif errorlevel 1 exit /b %errorlevel%\r\n'+link_line+'\r\nexit /b %errorlevel%\r\n').encode('ascii')
    with batch.open('xb') as f:
        if f.write(raw)!=len(raw):raise OSError('Short compiler script write')
        f.flush();os.fsync(f.fileno())
    command=[os.environ['COMSPEC'],'/d','/c',str(batch)]
    save(out/('compiler-script-'+phase+'.json'),{'script_sha256':sha(raw),'command':command,'setup_error_checked_before_compiler':True,'compiler_exits_before_linker':True,'compile_command':line,'link_command':link_line})
    return command


def registration_for(source,global_end):
    return {'schema':'EKA-SYNTHETIC-REGISTRATION-v1','cases':list(CASES),'execution_modes':[3],'accounting_contract':'EKA-CPU-METERED-ATTEMPT-v1','role_slots':9,'births_per_slot':4,'births_reserved':36,'global_wall_seconds':120,'global_end_tick':global_end,'native_role_wall_seconds':5,'closure_seconds':3,'raw_bytes_per_case':65536,'process_memory_bytes':64*1024**2,'child_job_memory_bytes':128*1024**2,'root_job_memory_bytes':256*1024**2,'child_user_cpu_seconds':1,'root_user_cpu_seconds':8,'source':source,'interpreter':sys.executable,'owner_birth':list(owner_source.current_birth()),'scientific_admission':False}


def verify_reservations(owner,out,seal):
    if type(owner) is not owner_source.NativeOwnerCandidate:raise TypeError('Exact owner required')
    ledger=owner.ledger
    if getattr(ledger,'_births',None)!=36:raise ValueError('Entire36-birth synthetic catalog must be reserved')
    slots=[(1,i) for i in range(7)]+[(8,0),(8,1)]
    catalog={(d,r):sha(owner_source.canonical({'schema':'EKA-SYNTHETIC-ONLY-v1','dose':d,'role':r})) for d in (1,8) for r in owner_source.ROLES}
    if owner._requests!=tuple(sorted(catalog.items())):raise ValueError('Exact synthetic request catalog required')
    if ledger._roles!=set(slots) or ledger._genesis!={1:{},8:{}}:raise ValueError('Wrong role/genesis reservations')
    previous='0'*64;expected=[];birth=0
    for dose,index in slots:
        expected.append(dict(kind='role',dose=dose,index=index))
        for unused in range(4):expected.append(dict(kind='process_birth',dose=dose,role=index,index=birth));birth+=1
    raw=owner._path.read_bytes();lines=raw.splitlines(keepends=True)
    if len(lines)!=len(expected):raise ValueError('Wrong physical ledger row count')
    for sequence,(line,reservation) in enumerate(zip(lines,expected)):
        row=json.loads(line)
        if row!=dict(sequence=sequence,previous_sha256=previous,reservation=reservation,execution_authenticated=False):raise ValueError('Physical reservation chain/catalog differs')
        previous=sha(line)
    registration=(out/'registration.json').read_bytes()
    if sha(registration)!=seal or owner._assignment!=seal:raise ValueError('Assignment differs')
    registered=json.loads(registration)
    if registered!=registration_for(registered['source'],registered['global_end_tick']):
        raise ValueError('Wrong registered synthetic catalog')
    return registered


def launch(exe, out, mode, owner, seal, global_end,transport=None):
    with _case_lock:
        if type(owner) is not owner_source.NativeOwnerCandidate:raise TypeError('Exact owner required')
        try:
            if owner._closed or owner._failed is not None:raise RuntimeError('Owner closed/incomplete; no retry')
            owner.ledger
            if type(mode) is not int or mode not in range(9):raise ValueError('Fixed synthetic case required')
            registered=verify_reservations(owner,out,seal)
            if mode not in registered['execution_modes']:raise ValueError('Only single-purpose CPU role admitted prospectively')
            if global_end!=registered['global_end_tick']:raise ValueError('Original enclosing deadline differs')
            if (owner,mode) in _used_cases:raise ValueError('Native slot already consumed; no retry')
            native_admission(transport) if transport is not None else native_admission()
            _used_cases.add((owner,mode))
            result=_launch(exe,out,mode,owner,seal,global_end,transport) if transport is not None else _launch(exe,out,mode,owner,seal,global_end)
            accept_case(result,out,mode)
            cpu=json.loads((out/(str(mode)+'.cpu-final.json')).read_text())
            if cpu!=result.get('cpu_accounting') or cpu['assignment']!=seal:
                raise CpuAccountingFailure('Durable CPU debit/assignment differs')
            if custody()!=registered['source']:raise ValueError('Post-case source/dependency closure differs')
            return result
        except BaseException as exc:
            owner._fail(exc)
            raise


def _launch(exe, out, mode, owner, seal, global_end,transport=None):
    """No arbitrary command API. Caller precharged the entire fixed catalog."""
    if type(owner) is not owner_source.NativeOwnerCandidate:raise TypeError('Exact owner required')
    owner.ledger
    if type(mode) is not int or mode not in range(9):raise ValueError('Fixed synthetic case required')
    registered=verify_reservations(owner,out,seal)
    if mode not in registered['execution_modes']:raise ValueError('Only single-purpose CPU role admitted prospectively')
    if registered['source']!=custody():raise ValueError('Source/dependency/interpreter changed')
    registration=(out/'registration.json').read_bytes()
    if seal!=sha(registration) or seal!=owner._assignment:raise ValueError('Assignment differs')
    plain(exe);plain(out)
    if Path(exe)!=out/'eka1_probe_guardian.exe' or sha(exe.read_bytes())!=json.loads((out/'binary-custody.json').read_text())['artifact_sha256']:
        raise ValueError('Exact compiled guardian required')
    native_admission(transport) if transport is not None else native_admission()
    if transport is None or transport.owner is not owner or transport.original_end!=global_end:
        raise owner_source.NativeQualificationRequired('NOT_READY: exact reusable runtime binding required')
    k=kernel(); began=k.GetTickCount64(); end=min(global_end,began+8000)
    if end-began < 4000: raise TimeoutError('No room for role and closure')
    job=Job(Limits(memory_bytes=256*1024**2,cpu_seconds=8,processes=4,wall_seconds=8))
    attrs=None; initialized=False; pi=PI(); fds=[]; handles=[]; inherited=[]
    meter=None;result=None;private=None;expected_birth=None;capsule=None
    try:
        meter=RootCpuAttempt(job,out,mode,owner,save)
        from tools.eka1_runtime_capsule import prepare
        capsule=prepare(transport,owner,exe,sha(exe.read_bytes()),end)
        raw=os.open(out/(str(mode)+'.raw'),os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_BINARY,0o600);fds.append(raw)
        rec=os.open(out/(str(mode)+'.inner.json'),os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_BINARY,0o600);fds.append(rec)
        nul=os.open(os.devnull,os.O_RDONLY|os.O_BINARY);fds.append(nul)
        oh=k.OpenProcess(0x1000|0x100000,True,os.getpid());checked(oh);handles.append(oh)
        lh=msvcrt.get_osfhandle(owner._fd)
        inherited=[msvcrt.get_osfhandle(f) for f in (raw,rec,nul)]+[lh,oh,int(job.handle),int(capsule['handle'].handle)]
        for h in inherited:os.set_handle_inheritable(h,True)
        size=ctypes.c_size_t();k.InitializeProcThreadAttributeList(None,2,0,ctypes.byref(size))
        attrs=ctypes.create_string_buffer(size.value);checked(k.InitializeProcThreadAttributeList(attrs,2,0,ctypes.byref(size)));initialized=True
        jobs=(wt.HANDLE*1)(job.handle);hs=(wt.HANDLE*len(inherited))(*inherited)
        checked(k.UpdateProcThreadAttribute(attrs,0,0x2000D,jobs,ctypes.sizeof(jobs),None,None))
        checked(k.UpdateProcThreadAttribute(attrs,0,0x20002,hs,ctypes.sizeof(hs),None,None))
        start=STARTEX();start.startup.cb=ctypes.sizeof(start);start.attributes=ctypes.cast(attrs,ctypes.c_void_p)
        start.startup.flags=0x100;start.startup.input=start.startup.output=start.startup.error=msvcrt.get_osfhandle(nul)
        command=[str(exe),str(mode),str(msvcrt.get_osfhandle(raw)),str(msvcrt.get_osfhandle(rec)),str(end),'EKA-SYNTHETIC-ONLY-v1',str(lh),str(oh),seal,str(int(job.handle)),str(int(capsule['handle'].handle)),capsule['sha256']]
        checked(k.CreateProcessW(str(exe),ctypes.create_unicode_buffer(subprocess.list2cmdline(command)),None,None,True,0x80000|4|8,None,str(ROOT),ctypes.byref(start),ctypes.byref(pi)))
        times=[ctypes.c_ulonglong() for _ in range(4)];checked(k.GetProcessTimes(pi.process,*[ctypes.byref(t) for t in times]))
        expected_birth=str(times[0].value)
        save(out/(str(mode)+'.start.json'),{'pid':pi.pid,'birth':str(times[0].value),'suspended':True,'root_limits':job.usage(),'end_tick':end,'mode':mode})
        if k.GetTickCount64()>=end-3000:raise TimeoutError('Pre-resume deadline')
        if k.ResumeThread(pi.thread)!=1:raise OSError('Cannot resume guardian')
        while True:
            wait=k.WaitForSingleObject(pi.process,20)
            if wait==0:break
            if wait!=258:raise OSError('Native guardian wait failed')
            if k.GetTickCount64()>=end:
                raise TimeoutError('Outer absolute guardian deadline')
        code=wt.DWORD();checked(k.GetExitCodeProcess(pi.process,ctypes.byref(code)))
        usage=job.usage()
        if usage['active_before_close']:raise RuntimeError('Outer Job closure UNKNOWN')
        if k.WaitForSingleObject(pi.process,0)!=0:raise RuntimeError('Guardian birth not signaled')
        raw_bytes=(out/(str(mode)+'.raw')).read_bytes();inner_bytes=(out/(str(mode)+'.inner.json')).read_bytes()
        records=[json.loads(row) for row in inner_bytes.splitlines()]
        result={'mode':mode,'guardian_exit':code.value,'guardian_birth':str(times[0].value),'guardian_pid':pi.pid,'elapsed_ms':k.GetTickCount64()-began,'usage':usage,'root_empty':True,'raw_sha256':sha(raw_bytes),'raw_bytes':len(raw_bytes),'inner_sha256':sha(inner_bytes),'inner':records[-1] if records and records[-1]['schema']=='EKA-SYNTHETIC-NATIVE-v1' else None,'child_start':records[0] if records and records[0]['schema']=='EKA-NATIVE-CHILD-START-v1' else None,'source_binary_sha256':sha(exe.read_bytes())}
        result['descendant_records']=[r for r in records if r['schema'] in ('EKA-DESCENDANT-BOUND-v1','EKA-DESCENDANT-GATE-v1')]
        private_records=[r for r in records if r['schema']=='EKA-PRIVATE-CPU-FINAL-v1']
        if len(private_records)==1:
            private=private_records[0]
            start=result['child_start']
            if not start or private['pid']!=start['pid'] or private['birth']!=start['birth']:
                private=None
                raise CpuAccountingFailure('Private retained birth/start receipt differs')
    finally:
        # Kill-on-close owns the whole root, including a crashed guardian's tree.
        primary=sys.exc_info()[1];failures=[];final_error=None
        # Retain the root and guardian birth handles through final counters.
        try:
            accounting=settle_root(job,meter,k,pi,expected_birth,private,end)
            if result is not None:result['cpu_accounting']=accounting
        except BaseException as exc:
            final_error=exc
            failures.append('CPU finalization: '+repr(exc))
        actions=[]
        actions += [lambda h=h:os.set_handle_inheritable(h,False) for h in inherited]
        actions += [job.close]
        if capsule is not None:actions += [capsule['handle'].close,capsule['image_handle'].close]
        if pi.thread:actions.append(lambda:checked(k.CloseHandle(pi.thread)))
        if pi.process:actions.append(lambda:checked(k.CloseHandle(pi.process)))
        if initialized:actions.append(lambda:k.DeleteProcThreadAttributeList(attrs))
        actions += [lambda h=h:checked(k.CloseHandle(h)) for h in handles]
        actions += [lambda fd=fd:os.close(fd) for fd in fds]
        for action in actions:
            try:action()
            except BaseException as exc:failures.append(type(exc).__name__+': '+str(exc))
        if failures:
            try:save(out/(str(mode)+'.cleanup-failure.json'),{'primary':repr(primary),'cleanup':failures,'physical_closure':'UNKNOWN','retry':False})
            except BaseException:pass
            if primary is None:
                if final_error is not None:raise final_error
                raise RuntimeError('Native cleanup incomplete: '+repr(failures))
    save(out/(str(mode)+'.outer.json'),result)
    return result


def settle_root(job,meter,k,pi,expected_birth,private,end):
    """One termination attempt; observe final counters even on custody failure."""
    failures=[];guardian=None
    try:job.terminate()
    except BaseException as exc:failures.append('terminate: '+repr(exc))
    try:
        while job.usage()['active_before_close'] and k.GetTickCount64()<end:time.sleep(.005)
        if pi.process:
            t=[ctypes.c_ulonglong() for unused in range(4)];member=wt.BOOL()
            if k.WaitForSingleObject(pi.process,0)!=0:raise CpuAccountingFailure('Guardian not signaled')
            checked(k.GetProcessTimes(pi.process,*[ctypes.byref(x) for x in t]))
            checked(k.IsProcessInJob(pi.process,job.handle,ctypes.byref(member)))
            guardian={'pid':k.GetProcessId(pi.process),'birth':str(t[0].value),'signaled':True,
                      'root_member':bool(member.value),'user_ticks':t[3].value,'kernel_ticks':t[2].value}
            if guardian['pid']!=pi.pid or guardian['birth']!=expected_birth:
                raise CpuAccountingFailure('Guardian retained birth changed')
    except BaseException as exc:failures.append('birth/closure: '+repr(exc))
    if meter is None:raise CpuAccountingFailure('CPU pending/initial receipt unavailable')
    return meter.finish(guardian,private,failures)


def build(out, owner, source, seal, global_end):
    if type(owner) is not owner_source.NativeOwnerCandidate:raise TypeError('Exact owner required')
    try:
        if owner._closed or owner._failed is not None:raise RuntimeError('Owner closed/incomplete; no retry')
        native_admission()
        verify_reservations(owner,out,seal)
        return _build(out,owner,source,seal,global_end)
    except BaseException as exc:
        owner._fail(exc)
        raise


def _build(out, owner, source, seal, global_end):
    """Retired: opaque helper attempts cannot be precharged by this owner.

    This inner entry refuses independently of the human/native admission gate.
    A matching old binary or source hash is not a compatible fresh assignment.
    No setup script, bootstrap, compiler or linker is invoked here.
    """
    raise owner_source.NativeQualificationRequired(
        'INLINE_BUILD_RETIRED: separately measured immutable prebuilt artifacts '
        'and independently reviewed fresh-owner binding protocol required')


def archive_evidence(out):
    """Exact DATA restoration only; never imports or executes restored code."""
    import zipfile
    paths=[p for p in out.rglob('*') if p.is_file()]
    if len(paths)>128 or sum(p.stat().st_size for p in paths)>64*1024**2:
        raise ValueError('Synthetic archive file/expanded reservation exceeded')
    pins={str(p.relative_to(out)).replace('\\','/'):sha(p.read_bytes()) for p in paths}
    target=out/'evidence.zip'
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in paths:plain(p);z.write(p,str(p.relative_to(out)))
    if target.stat().st_size>64*1024**2:raise ValueError('Synthetic stored archive cap')
    restore=out/'restored';restore.mkdir()
    with zipfile.ZipFile(target) as z:
        if len(z.infolist())!=len(pins):raise ValueError('Archive entry count differs')
        for item in z.infolist():
            name=item.filename
            if name not in pins or Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Unexpected archive entry')
            raw=z.read(item)
            if sha(raw)!=pins[name]:raise ValueError('Archive bytes differ')
            dest=restore/name;dest.parent.mkdir(exist_ok=True,parents=True)
            with dest.open('xb') as f:f.write(raw)
    if any(sha((restore/p).read_bytes())!=h for p,h in pins.items()):raise ValueError('Restored bytes differ')
    save(out/'archive-verification.json',{'status':'PASS_EXACT_DATA_RESTORE','file_count':len(pins),'stored_bytes':target.stat().st_size,'expanded_bytes':sum(p.stat().st_size for p in paths),'zip_sha256':sha(target.read_bytes()),'files':pins,'restored_code_executed':False,'full_scientific_archive_qualified':False})


def accept_case(result,out,mode):
    """Only the declared negative outcomes may leave later fixture slots usable."""
    inner=result['inner']
    if mode==7:
        if result['guardian_exit']!=124 or inner is not None or result['child_start'] is None or not result['root_empty']:raise ValueError('Watchdog fixture did not terminate blocked guardian')
    elif mode==1:
        if result['guardian_exit']!=125 or inner is None or inner['error']!=10 or inner['pid']!=0 or inner['cleanup_count'] or inner['active'] or not result['root_empty']:raise ValueError('Create failure not retained')
    else:
        if result['guardian_exit'] or inner is None or inner['error'] or not inner['eof'] or inner['active'] or not result['root_empty']:
            raise ValueError('Native closure/capture incomplete')
        raw=(out/(str(mode)+'.raw')).read_bytes()
        if mode==0 and b'EKA_SYNTHETIC_OK' not in raw:raise ValueError('Missing normal output')
        if mode==2 and inner['reason']!=1:raise ValueError('Wall limit not observed')
        if mode==3 and (inner['exit_code']==0 or inner['user_cpu_ticks']<10000000):raise ValueError('CPU termination not observed')
        if mode==3 and result.get('cpu_accounting',{}).get('status')!='MEASURED_WITHIN_USER_CEILINGS_NOT_NATIVE_QUALIFICATION':raise CpuAccountingFailure('Final CPU debit missing/incomplete/over budget')
        if mode==4 and b'EKA_MEMORY_LIMIT' not in raw:raise ValueError('Memory limit not observed')
        if mode==5 and (not inner['overflow'] or result['raw_bytes']!=65536):raise ValueError('Output limit not observed')
        if mode==6:
            # Windows may count an active-limit-rejected creation in cumulative
            # TotalProcesses. It must never become a second successful child.
            identity=str(inner['desc_pid'])+' '+str(inner['desc_birth'])
            lines=raw.splitlines();records=result.get('descendant_records',[])
            if (lines.count(('EKA_DESCENDANT_CREATED '+identity).encode())!=1 or
                lines.count(('EKA_DESCENDANT_SELF '+identity).encode())!=1 or
                lines.count(b'EKA_PROCESS_CAP_REFUSED 1816')!=1 or
                inner['process_cap']!=2 or inner['started_processes'] not in (2,3) or
                result['usage']['started_processes']>4 or not inner['desc_signaled'] or
                not inner['desc_pid'] or int(inner['desc_birth'])<=0 or
                [r['schema'] for r in records]!=['EKA-DESCENDANT-BOUND-v1','EKA-DESCENDANT-GATE-v1']):raise ValueError('Process containment not observed')
            bound,released=records
            if (any(r.get('pid')!=inner['desc_pid'] or r.get('birth')!=inner['desc_birth'] for r in records) or
                any(bound.get(flag) is not True for flag in ('live','private_job','root_job','self_ready')) or
                not isinstance(bound.get('tick'),int) or not isinstance(released.get('tick'),int) or
                bound['tick']>released['tick']):raise ValueError('Process containment identity/order not observed')
        if mode==8 and (inner['exit_code']!=124 or not 1000<=inner['elapsed_ms']<4000 or b'EKA_PYTHON_OWNER_WATCHDOG_STARTED' not in raw):raise ValueError('Blocked Python owner deadline not observed')


def qualify(out):
    global _owner_watchdog,_owner_watchdog_started,_evidence_directory
    out=Path(out).absolute();plain(out.parent);out.mkdir(exist_ok=False)
    _evidence_directory=out
    save(out/'attempt-costs-pending.json',{'status':'UNRESOLVED_ATTEMPT_COSTS','root_cpu':'PENDING','build_owner_observer_archive_cpu':'UNSETTLED_SEPARATE_SCOPES','historical_costs':'UNRESOLVED_PRESERVED','no_retry':True,'strict_prepaid_bound':False,'scientific_ready':False})
    global_end=kernel().GetTickCount64()+120000;started=time.monotonic();source=custody()
    catalog={(d,r):sha(owner_source.canonical({'schema':'EKA-SYNTHETIC-ONLY-v1','dose':d,'role':r})) for d in (1,8) for r in owner_source.ROLES}
    registration=registration_for(source,global_end)
    save(out/'registration.json',registration);seal=sha((out/'registration.json').read_bytes())
    owner=owner_source.NativeOwnerCandidate(out/'reservations.jsonl',owner_birth=owner_source.current_birth(),assignment_id=seal,request_hashes=catalog)
    results=[]
    try:
        ledger=owner.ledger
        for dose,index in [(1,i) for i in range(7)]+[(8,0),(8,1)]:
            ledger.role(dose,index)
            for unused in range(4):ledger.process_birth(dose,index)
        assert ledger._births==36
        exe=build(out,owner,source,seal,global_end)
        dll=out/'eka1_owner_watchdog.dll';_owner_watchdog=ctypes.WinDLL(str(dll),use_last_error=True)
        _owner_watchdog.EkaStartWatchdog.argtypes=[wt.DWORD,ctypes.c_ulonglong,ctypes.c_ulonglong];_owner_watchdog.EkaStartWatchdog.restype=wt.BOOL
        _owner_watchdog.EkaStopWatchdog.argtypes=[];_owner_watchdog.EkaStopWatchdog.restype=wt.BOOL
        birth=owner_source.current_birth();checked(_owner_watchdog.EkaStartWatchdog(birth[0],birth[1],global_end))
        _owner_watchdog_started=True
        save(out/'owner-watchdog-start.json',{'owner_birth':birth,'absolute_end_tick':global_end,'native_thread':True,'prebuild_phase':'Separately bounded compiler Jobs; earlier Python metadata IO interruption unqualified'})
        if custody()!=source:raise ValueError('Source/dependency/interpreter closure changed')
        for mode in registration['execution_modes']:
            owner.ledger  # canonical birth, physical identity/extent and deadline
            result=launch(exe,out,mode,owner,seal,global_end);results.append(result)
        report={'status':'MEASURED_SINGLE_CPU_ROLE_SCOPED_ONLY','results':results,'reserved_births':ledger._births,'no_refunds':True,'elapsed_seconds':time.monotonic()-started,'scientific_admission':False,'finite_scientific_qualification_ready':False,'strict_cpu_ceiling_qualified':False,'remaining':'External build/owner/observer/archive costs remain separate/unsettled; strict prepaid CPU bound and scientific qualification remain NOT_READY'}
        save(out/'qualification.json',report);return report
    except BaseException as exc:
        owner._fail(exc)
        try:save(out/'first-failure.json',{'type':type(exc).__name__,'message':str(exc),'owner_first_failure':owner._failed,'cpu_observation':getattr(exc,'cpu_observation',None),'cleanup':owner._cleanup_errors,'completed_cases':len(results),'reserved_births':owner._ledger._births if owner._ledger else None,'status':'INCOMPLETE_NO_RETRY'})
        except BaseException as evidence_error:
            owner._cleanup_errors.append('first-failure evidence: '+repr(evidence_error))
            try:save(out/'evidence-write-failure.json',{'primary':repr(exc),'evidence_error':repr(evidence_error),'status':'INCOMPLETE'})
            except BaseException:pass
        raise
    finally:owner.close()


def execute(out):
    """Archive only this attempt; every cleanup runs and retains the first cause."""
    global _execution_consumed
    native_admission()
    if _execution_consumed:raise ValueError('Synthetic owner attempt consumed; no retry')
    _execution_consumed=True
    began=time.monotonic();out=Path(out).absolute()
    try:
        report=qualify(out)
    finally:
        primary=sys.exc_info()[1];cleanup_error=None
        if _evidence_directory==out:
            try:archive_evidence(out)
            except BaseException as exc:
                cleanup_error=exc
                try:save(out/'archive-failure.json',{'primary':repr(primary),'archive_error':repr(exc),'status':'INCOMPLETE','archive_cost':'UNKNOWN_UNRESOLVED','root_debits_not_refunded':True})
                except BaseException:pass
        if _owner_watchdog_started:
            try:checked(_owner_watchdog.EkaStopWatchdog())
            except BaseException as exc:
                if cleanup_error is None:cleanup_error=exc
                try:save(out/'watchdog-stop-failure.json',{'primary':repr(primary),'cleanup':repr(exc),'status':'INCOMPLETE'})
                except BaseException:pass
        if primary is None and cleanup_error is not None:raise cleanup_error
    save(out/'completion.json',{'status':report['status'],'elapsed_including_archive_seconds':time.monotonic()-began,'elapsed_before_archive_seconds':report['elapsed_seconds'],'owner_watchdog_stopped':True,'prebuild_metadata_interruption_qualified':False})
    return report


if __name__=='__main__':
    raise SystemExit('NOT_READY: source-only metered candidate; separate immutable native assignment authorization required')
