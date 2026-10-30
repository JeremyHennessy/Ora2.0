"""Once-consumed CPU assignment transport. Source-only: NEVER a native grant.

An externally pinned human approval record is necessary, not sufficient. The
opaque compiler/helper and external settlement gaps remain hard NO_GO reasons.
No process, compiler, World, refund, marker removal or resume API exists here.
"""
import hashlib
import json
import os
from pathlib import Path
import re
from tools import eka1_native_owner_candidate as owners

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'runs/eka1-cpu-grant-registry-v1'
LIMITS={'private_USER_ticks':10000000,'root_USER_ticks':80000000,
        'process_memory_bytes':67108864,'private_job_memory_bytes':134217728,
        'root_job_memory_bytes':268435456,'private_active_processes':1,
        'root_active_processes':4,'role_wall_ms':5000,'closure_ms':3000,
        'global_wall_ms':120000,'raw_bytes':65536,'archive_files':128,
        'archive_bytes':67108864}
UNQUALIFIED=('compiler_helper_pre_effect_attempt_custody',
             'complete_executed_SDK_dependency_closure',
             'external_owner_observer_archive_final_settlement',
             'native_grant_guardian_transport_qualification')

def digest(raw):return hashlib.sha256(raw).hexdigest()
def hexhash(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}',value) is None:
        raise ValueError('Externally pinned exact SHA256 required')
    return value
def plain(path):
    for p in (Path(path),*Path(path).parents):
        s=p.lstat()
        if p.is_symlink() or getattr(s,'st_file_attributes',0)&0x400:
            raise ValueError('Plain non-reparse ancestry required')
    if path.is_file() and path.stat().st_nlink!=1:raise ValueError('Shared artifact refused')
def read_exact(path,expected):
    path=Path(path);plain(path)
    if not path.is_file() or path.stat().st_size>1024**2:raise ValueError('Bounded artifact required')
    raw=path.read_bytes()
    if digest(raw)!=hexhash(expected):raise ValueError('Pinned artifact changed')
    value=json.loads(raw)
    if owners.canonical(value)!=raw:raise ValueError('Canonical unique-key JSON required')
    return value,raw
def file_identity(path):
    plain(path);s=path.stat()
    return (s.st_dev,s.st_ino)
def save(path,value):
    raw=owners.canonical(value)
    with path.open('xb') as stream:
        if stream.write(raw)!=len(raw):raise OSError('Short immutable evidence write; consumed')
        stream.flush();os.fsync(stream.fileno())
def tick():
    import ctypes
    from ctypes import wintypes
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetTickCount64.restype=ctypes.c_ulonglong;k.GetTickCount64.argtypes=[]
    return k.GetTickCount64()

class CpuGrantTransport:
    """One producer and one fixed registry claim, including failed validation.

    The expected grant hash must come from separate operator authorization.
    Supplying matching JSON/hash here cannot open the native execution gate.
    """
    def __init__(self,manifest,grant,*,manifest_sha256,operator_grant_sha256):
        self.manifest_path=Path(manifest);self.grant_path=Path(grant)
        self.manifest_sha=hexhash(manifest_sha256);self.grant_sha=hexhash(operator_grant_sha256)
        self.claim_tick=tick();self.original_end=self.claim_tick+LIMITS['global_wall_ms']
        self.birth=owners.current_birth();self.failed=True;self.bound=False;self.binding=None;self.owner=None
        REGISTRY.mkdir(parents=True,exist_ok=True);plain(REGISTRY)
        self.marker=REGISTRY/(self.manifest_sha+'.consumed.json')
        # Burn in a fixed registry BEFORE parsing or trusting caller artifacts.
        save(self.marker,{'status':'CONSUMED_UNRESOLVED','manifest_sha256':self.manifest_sha,
                          'grant_sha256':self.grant_sha,'producer_birth':list(self.birth),
                          'claim_tick':self.claim_tick,'original_end_tick':self.original_end,
                          'scope':'SOURCE_ONLY_NO_EXECUTION_AUTHORITY','no_retry':True})
        self.marker_raw=self.marker.read_bytes()
        try:
            self.manifest,self.manifest_raw=read_exact(self.manifest_path,self.manifest_sha)
            m=self.manifest
            assignment=m.get('assignment_id') if type(m) is dict else None
            if type(assignment) is not str or re.fullmatch('[A-Za-z0-9_-]{1,96}',assignment) is None:
                raise ValueError('Immutable assignment identity required')
            self.assignment_marker=REGISTRY/('assignment-id-'+digest(assignment.encode('ascii'))+'.consumed.json')
            save(self.assignment_marker,{'assignment_id':assignment,'manifest_sha256':self.manifest_sha,
                                        'producer_birth':list(self.birth),'original_end_tick':self.original_end})
            self.assignment_marker_raw=self.assignment_marker.read_bytes()
            self.grant,self.grant_raw=read_exact(self.grant_path,self.grant_sha)
            g=self.grant
            if (set(m)!={'schema','assignment_id','purpose','mode','output_relative','source',
                         'interpreter','toolchain','limits'} or
                m['schema']!='EKA-CPU-PROSPECTIVE-ASSIGNMENT-v1' or m['purpose']!='ONE_CPU_STRESS_ONLY' or
                type(m['mode']) is not int or m['mode']!=3 or
                type(m['assignment_id']) is not str or re.fullmatch('[A-Za-z0-9_-]{1,96}',m['assignment_id']) is None or
                owners.canonical(m['limits'])!=owners.canonical(LIMITS)):
                raise ValueError('Exact one-purpose CPU assignment and unchanged limits required')
            relative=m['output_relative']
            if (type(relative) is not str or re.fullmatch('runs/eka1-cpu-[A-Za-z0-9_-]{1,96}',relative) is None):
                raise ValueError('Fixed fresh diagnostic output required')
            self.out=ROOT/relative
            if self.out.exists():raise ValueError('Assignment output already exists; no replacement')
            if (set(g)!={'schema','manifest_sha256','assignment_id','authorization',
                         'acknowledge_nondeterministic_CPU_overshoot','attempts'} or
                g['schema']!='EKA-CPU-OPERATOR-APPROVAL-v1' or g['manifest_sha256']!=self.manifest_sha or
                g['assignment_id']!=m['assignment_id'] or g['authorization']!='EXPLICIT_HUMAN_OPERATOR' or
                g['acknowledge_nondeterministic_CPU_overshoot'] is not True or
                type(g['attempts']) is not int or g['attempts']!=1):
                raise ValueError('Separate exact one-attempt operator acknowledgement required')
            self._sources()
            self.files={p:file_identity(p) for p in (self.manifest_path,self.grant_path,self.marker,self.assignment_marker)}
            self.failed=False
        except BaseException as exc:
            try:save(REGISTRY/(self.manifest_sha+'.failure.json'),{'status':'FAILED_CONSUMED',
                     'first_failure':repr(exc),'missing_costs':'UNKNOWN_UNRESOLVED','native_started':False})
            except BaseException:pass
            raise

    def _sources(self):
        from tools.eka1_native_probe import SOURCE_FILES,custody
        source=self.manifest['source']
        if type(source) is not dict or set(source)!=set(SOURCE_FILES):
            raise ValueError('Complete fixed runtime control source list required')
        for name,expected in source.items():
            p=ROOT/name;plain(p)
            if digest(p.read_bytes())!=hexhash(expected):raise ValueError('Runtime source changed')
        import sys
        interpreter=self.manifest['interpreter']
        if set(interpreter)!={'path','sha256','closure_sha256'} or Path(interpreter['path'])!=Path(sys.executable).resolve():
            raise ValueError('Exact executed interpreter required')
        plain(Path(interpreter['path']))
        if digest(Path(interpreter['path']).read_bytes())!=hexhash(interpreter['sha256']):
            raise ValueError('Interpreter changed')
        if digest(owners.canonical(custody()))!=hexhash(interpreter['closure_sha256']):
            raise ValueError('Observed interpreter/library/control closure changed')
        tools=self.manifest['toolchain']
        if type(tools) is not dict or not tools:raise ValueError('Frozen toolchain observations required')
        for name,expected in tools.items():
            p=Path(name)
            if not p.is_absolute():raise ValueError('Absolute toolchain path required')
            plain(p)
            if digest(p.read_bytes())!=hexhash(expected):raise ValueError('Toolchain input changed')

    def _poison(self,error):
        self.failed=True
        if self.owner is not None:
            try:self.owner._fail(error)
            except BaseException as cleanup:
                error.add_note('Original owner cleanup incomplete: '+repr(cleanup))

    def bind(self,owner,out,registration_sha256,global_end):
        if self.failed or self.bound:
            error=RuntimeError('Transport consumed/incomplete; no second bind')
            self._poison(error)
            raise error
        self.bound=True  # A failed binding is never reusable.
        try:
            from tools.eka1_native_probe import verify_reservations
            if type(owner) is not owners.NativeOwnerCandidate or tuple(owner._birth)!=self.birth or owners.current_birth()!=self.birth:
                raise ValueError('Only the original consuming producer may bind')
            self.owner=owner
            if Path(out).absolute()!=self.out:raise ValueError('Alternate output/assignment refused')
            self._sources()
            if any(file_identity(p)!=v for p,v in self.files.items()):raise ValueError('Transport physical artifact identity changed')
            read_exact(self.manifest_path,self.manifest_sha);read_exact(self.grant_path,self.grant_sha)
            if (self.marker.read_bytes()!=self.marker_raw or
                self.assignment_marker.read_bytes()!=self.assignment_marker_raw):raise ValueError('Consumed registry marker changed')
            registered=verify_reservations(owner,self.out,registration_sha256)
            if (registered.get('interpreter')!=self.manifest['interpreter']['path'] or
                digest(owners.canonical(registered.get('source')))!=self.manifest['interpreter']['closure_sha256']):
                raise ValueError('Registered source/interpreter closure differs from static approval')
            if (type(global_end) is not int or registered['global_end_tick']!=global_end or
                global_end!=self.original_end or tick()>=self.original_end):
                raise ValueError('Original absolute deadline required; no extension')
            if registered['execution_modes']!=[3]:raise ValueError('Only fixed CPU mode3')
            envelope={'status':'BOUND_SOURCE_ONLY_NO_NATIVE_AUTHORITY','static_manifest_sha256':self.manifest_sha,
                      'operator_grant_sha256':self.grant_sha,'producer_birth':list(self.birth),
                      'registration_sha256':registration_sha256,'physical_ledger':list(owner._physical),
                      'ledger_sha256':digest(owner._path.read_bytes()),'ledger_extent':owner._ledger._bytes,
                      'global_end_tick':global_end,'output':str(self.out),'mode':3,
                      'unqualified':list(UNQUALIFIED),'missing_costs':'UNKNOWN_UNRESOLVED'}
            self.binding=REGISTRY/(self.manifest_sha+'.binding.json')
            save(self.binding,envelope)
            self.binding_raw=self.binding.read_bytes();self.owner=owner;self.global_end=global_end
            self.files[self.binding]=file_identity(self.binding)
            self.registration_sha=registration_sha256
            return dict(envelope,binding_sha256=digest(self.binding_raw),native_entry_enabled=False)
        except BaseException as exc:
            self._poison(exc)
            raise

    def preflight(self):
        if self.failed or not self.bound or self.binding is None:raise RuntimeError('No complete once-bound transport')
        try:
            self.owner._check();self._sources()
            if any(file_identity(p)!=v for p,v in self.files.items()):raise ValueError('Transport physical artifact identity changed')
            read_exact(self.manifest_path,self.manifest_sha);read_exact(self.grant_path,self.grant_sha)
            bound=json.loads(self.binding_raw)
            fd=os.fstat(self.owner._fd);named=self.owner._path.stat()
            if ((fd.st_dev,fd.st_ino)!=tuple(bound['physical_ledger']) or
                (named.st_dev,named.st_ino)!=(fd.st_dev,fd.st_ino) or
                fd.st_size!=bound['ledger_extent'] or named.st_size!=fd.st_size or
                self.owner._assignment!=self.registration_sha or
                digest((self.out/'registration.json').read_bytes())!=self.registration_sha):
                raise ValueError('Original physical ledger/registration binding changed')
            if (owners.current_birth()!=self.birth or self.marker.read_bytes()!=self.marker_raw or
                self.assignment_marker.read_bytes()!=self.assignment_marker_raw or
                self.binding.read_bytes()!=self.binding_raw or tick()>=self.global_end or
                digest(self.owner._path.read_bytes())!=json.loads(self.binding_raw)['ledger_sha256']):
                raise ValueError('Owner/ledger/grant/binding/deadline custody changed')
            return {'decision':'NO_GO','native_entry_enabled':False,'binding_sha256':digest(self.binding_raw),
                    'unqualified':list(UNQUALIFIED),'operator_approval_alone_sufficient':False}
        except BaseException as exc:
            self._poison(exc)
            raise
