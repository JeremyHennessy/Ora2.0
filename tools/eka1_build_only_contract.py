"""Approved BUILD_ONLY source contract. No compiler, command runner or native grant.

Retained-file debits are preparation evidence, not an OS mediation boundary.
Opaque nested attempts are UNKNOWN only in this separate build scope. All
native entry remains held; process_limits.run's USER-only result is insufficient.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import threading
from tools.eka1_native_owner_candidate import canonical,current_birth,NativeQualificationRequired
from tools.eka1_cpu_grant_transport import plain,hexhash,read_exact,save,tick
from tools import eka1_external_settlement as settlement
from tools.eka1_runtime_capsule import release_header,CapsuleReadHandle

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'runs/eka1-build-only-registry-v1'
CONTRACT='EKA-BUILD-ONLY-METERED-RELEASE-v1'
CONTRACT_SHA='a24c1a888d286a5cf5919c0725bb1330e21ab1d4e207ef6efa1512f4b3254952'
STAGED_CONTRACT='EKA-BUILD-ONLY-SINGLE-ATTEMPT-DERIVED-HEADER-v1'
STAGED_SCHEMA='EKA-BUILD-ONLY-STAGED-MANIFEST-v1'
AMENDMENT_FILE='data/eka1-single-attempt-staged-release-amendment-20261101.json'
AMENDMENT_SHA='e0858730a375f44629eb60d0d163880fc71dc4fa3e8f9a28d896cafbbbcced0c'
DERIVED_OUTPUTS=('eka1_probe_pins.h','stage-b-manifest.json')
ROOT_OBSERVATION_FILES=('root-observation-pending.json','root-observation-initial.json',
                        'root-observation-stage-a.json','root-observation-final.json')
CATALOGUE=('compile_watchdog','link_watchdog','compile_guardian','link_guardian')
BUILD_OUTPUTS=('eka1_probe_guardian.exe','eka1_owner_watchdog.dll','guardian.obj','watchdog.obj','watchdog.lib','watchdog.exp')
# Explicit candidate thresholds from the retained build scope, NOT authority
# inherited from that failed/unqualified historical setup. Manifest must state
# every value; independent qualification/operator approval remain separate.
LIMITS=dict(USER_ticks=300000000,memory_bytes=536870912,active_processes=4,
            wall_ms=30000,output_bytes=1048576,archive_files=128,archive_bytes=67108864)
SOURCES=('tools/eka1_build_only_contract.py','tools/eka1_cpu_grant_transport.py',
         'tools/eka1_native_owner_candidate.py','tools/eka1_external_settlement.py',
         'experiments/native/eka1_probe_guardian.c','experiments/native/eka1_probe_owner_watchdog.c',
         'experiments/native/eka1_runtime_capsule.h','tools/eka1_runtime_capsule.py')
EXTERNAL=('owner','observer','cleanup','archive','restore','hash','completion','watchdog',
          'verifier_final_write','registry','unattributed_system_costs')

def recipe(m):return digest(canonical({k:v for k,v in m.items() if k!='external_settlement_plan'}))

def staged(m):return m.get('schema')==STAGED_SCHEMA
def source_names(m):return SOURCES+('tools/eka1_probe_child.py',) if staged(m) else SOURCES

def release_inputs(m,out):
    """Fixed precommitted arguments; only the future DLL hash is derived."""
    return dict(python=m['interpreter']['path'],python_sha=m['interpreter']['sha256'],
                program=str(ROOT/'tools/eka1_probe_child.py'),program_sha=m['source']['tools/eka1_probe_child.py'],
                watchdog=str(out/'eka1_owner_watchdog.dll'))

def root_binding(m):
    value=m['root_binding'];rid=hexhash(value['root_identity'])
    expected=dict(root_identity=rid,USER_ticks=0,KERNEL_ticks=0,period_USER_ticks=0,period_KERNEL_ticks=0,
                  active=0,total_processes=0,root_handle_retained=True)
    if canonical(value)!=canonical(expected):raise ValueError('Fresh retained root and exact zero epoch required')
    return rid

def ledger_rows(path):return [json.loads(x) for x in path.read_bytes().splitlines()]

def stage_binding(m,msha,physical,claim_tick,rows,out):
    """Revalidate retained derived DATA, never OS custody or execution authority."""
    if len(rows)<7:raise ValueError('Missing one-time StageB binding')
    attempt=rows[5]['event'];event=rows[6]['event']
    if set(attempt)!={'kind','input_recipe_sha256','stage_a_sample'} or attempt['kind']!='derive_attempt' or attempt['input_recipe_sha256']!=recipe(m):
        raise ValueError('Derivation was not consumed before effects')
    if set(event)!={'kind','manifest_sha256'} or event['kind']!='derived_stage_b':
        raise ValueError('Missing exact derived-manifest event')
    d,raw=read_exact(out/DERIVED_OUTPUTS[1],event['manifest_sha256'])
    prior=digest(canonical(rows[5])+b'\n')
    keys={'schema','assignment_sha256','input_recipe_sha256','owner_birth','ledger_identity','deadline_tick',
          'prior_ledger_tip','derived_tick','stage_a_sample','watchdog','header','release_pins','invocations'}
    if (set(d)!=keys or d['schema']!='EKA-BUILD-ONLY-DERIVED-STAGE-B-v1' or
        d['assignment_sha256']!=msha or d['input_recipe_sha256']!=recipe(m) or
        d['owner_birth']!=m['owner_birth'] or d['ledger_identity']!=list(physical) or
        d['deadline_tick']!=m['deadline_tick'] or d['prior_ledger_tip']!=prior or
        d['invocations']!=m['invocations'][2:] or d['stage_a_sample']!=attempt['stage_a_sample']):raise ValueError('Derived StageB binding changed')
    created=[birth(rows[i]['event']['result']['birth']) for i in (2,4)]
    s=d['stage_a_sample'];validate_sample(s,m,msha,physical,created,claim_tick);validate_limits(s,m)
    if not s['measured_tick']<=number(d['derived_tick'])<m['deadline_tick']:raise ValueError('Derived observation ordering differs')
    if s.get('root_handle_retained') is not True:raise ValueError('Same root handle must remain retained')
    pins=dict(release_inputs(m,out),watchdog_sha=d['watchdog']['sha256'])
    if d['release_pins']!=pins:raise ValueError('Caller substituted release pins')
    for key,path in [('watchdog',out/'eka1_owner_watchdog.dll'),('header',out/DERIVED_OUTPUTS[0])]:
        item=d[key];plain(path);info=path.stat()
        if (set(item)!={'path','sha256','file_identity'} or item['path']!=str(path) or
            item['file_identity']!=[info.st_dev,info.st_ino] or digest(path.read_bytes())!=hexhash(item['sha256'])):
            raise ValueError('Derived artifact bytes or physical custody changed')
    if (out/DERIVED_OUTPUTS[0]).read_bytes()!=release_header(pins):raise ValueError('Header differs from pinned derivation rule')
    return d

def cumulative_stage_sample(final,initial):
    """One root, lifetime and epoch; StageA is an observation, not a debit."""
    if (final.get('root_handle_retained') is not True or final['root_identity']!=initial['root_identity'] or
        final['started_tick']!=initial['started_tick'] or final['closed_tick']<initial['measured_tick'] or
        not set(map(birth,initial['members']))<=set(map(birth,final['members']))):
        raise ValueError('Original root, start, closure order or StageA members changed')
    for name in ('USER_ticks','KERNEL_ticks','elapsed_ms','peak_memory_bytes','output_bytes','job_total_processes'):
        if final[name]<initial[name]:raise ValueError('Cumulative root counter decreased: '+name)

def invocations(m,out):
    """Fixed source-level catalogue, DATA only; never passed to an OS API here."""
    includes=sorted({str(Path(p).parent) for p in m['includes']}|{str(Path(m['header']['path']).parent)})
    libraries=sorted({str(Path(p).parent) for p in m['libraries']})
    rows=[]
    for name in ('watchdog','guardian'):
        source=ROOT/('experiments/native/eka1_probe_owner_watchdog.c' if name=='watchdog' else 'experiments/native/eka1_probe_guardian.c')
        obj=out/(name+'.obj');target=out/('eka1_owner_watchdog.dll' if name=='watchdog' else 'eka1_probe_guardian.exe')
        rows.append(dict(role='compile_'+name,image=m['toolchain']['compiler']['path'],argv=['/nologo','/c','/TC','/O1','/MT','/Z7',
                         *['/I'+p for p in includes],'/Fo'+str(obj),str(source)]))
        rows.append(dict(role='link_'+name,image=m['toolchain']['linker']['path'],argv=['/NOLOGO','/INCREMENTAL:NO','/OUT:'+str(target),
                         *(['/DLL','/IMPLIB:'+str(out/'watchdog.lib')] if name=='watchdog' else []),
                         *['/LIBPATH:'+p for p in libraries],str(obj),'kernel32.lib','bcrypt.lib']))
    return rows

def digest(raw):return hashlib.sha256(raw).hexdigest()
def number(v):
    if type(v) is not int or not 0<=v<2**63:raise ValueError('Exact nonnegative raw counter required')
    return v
def birth(v):return settlement.birth(v)

def validate_sample(s,m,manifest_sha256,physical,created,claim_tick):
    """One raw counter/closure contract shared by owner and external verifier."""
    if type(s) is not dict:raise ValueError('Missing raw root counters/custody')
    u=number(s.get('USER_ticks'));k=number(s.get('KERNEL_ticks'));hexhash(s['root_identity'])
    members=[birth(x) for x in s['members']]
    if (s.get('scope')!='BUILD_ONLY' or s.get('assignment_sha256')!=manifest_sha256 or
        s.get('ledger_identity')!=list(physical) or birth(m['owner_birth']) in members or len(set(members))!=len(members) or
        len(set(created))!=len(created) or not set(created)<=set(members) or
        len(s['signaled_births'])!=len(members) or set(members)!=set(birth(x) for x in s['signaled_births']) or
        s.get('active')!=0 or type(s.get('active')) is not int or s.get('EOF') is not True or
        s.get('termination_succeeded') is not True or s.get('nested_CPU_added') is not False or
        s.get('initial_USER_ticks')!=0 or type(s.get('initial_USER_ticks')) is not int or
        s.get('initial_KERNEL_ticks')!=0 or type(s.get('initial_KERNEL_ticks')) is not int or
        s.get('period_USER_ticks')!=u or s.get('period_KERNEL_ticks')!=k):
        raise ValueError('Incomplete/duplicate/corrupt root scope, epochs or custody')
    if staged(m) and (s['root_identity']!=m['root_binding']['root_identity'] or s.get('root_handle_retained') is not True):
        raise ValueError('Frozen source-only root binding changed')
    number(s['period_USER_ticks']);number(s['period_KERNEL_ticks'])
    if number(s['job_total_processes'])!=len(members):raise ValueError('Unexplained associated-process count; complete identity set missing')
    start=number(s['started_tick']);end=number(s['closed_tick']);measured=number(s['measured_tick'])
    number(s['elapsed_ms']);number(s['peak_memory_bytes']);number(s['output_bytes'])
    if not claim_tick<=start<=end<=measured or end-start!=s['elapsed_ms']:
        raise ValueError('Raw measurement ordering differs')
    return u,k,members

def validate_limits(s,m):
    """Resource failure never refunds an otherwise consistent measured debit."""
    for name,limit in [('USER_ticks',LIMITS['USER_ticks']),('peak_memory_bytes',LIMITS['memory_bytes']),
                       ('elapsed_ms',LIMITS['wall_ms']),('output_bytes',LIMITS['output_bytes'])]:
        if s[name]>limit:raise ValueError('Terminal resource overrun: '+name)
    if s['measured_tick']>m['deadline_tick']:raise TimeoutError('Original absolute deadline exceeded')

class BuildOnly:
    """One original process, fixed manifest/catalogue and physical ledger.

    No restoration constructor, callback, generic launcher or retry/refund API.
    A poisoned instance may retain final costs once, never reserve more work.
    """
    def __init__(self,manifest,preparation,*,manifest_sha256,preparation_sha256):
        self._mutex=threading.RLock();self._fd=None;self._closed=False;self._failed=None
        self._storage_failed=False;self._finalized=False;self._seq=0;self._bytes=0;self._tip='0'*64;self._cleanup_errors=[]
        self._pending=None;self._outcomes=[];self._attempts=0;self._files={};self._debits=[]
        self._derive_consumed=False;self._derived=None;self._pins=[];self._pin_cleanup_recorded=False
        self._root_observation_consumed=False;self._root_job=None;self._root_api=None;self._root_duplicate=None
        self._root_close_attempted=False;self._root_cleanup_recorded=False;self._root_phases=set();self._root_compare=None
        self._root_initial=None;self._root_last=None;self._root_context=None
        self._start=tick();self._birth=current_birth();self._end=self._start+LIMITS['wall_ms']
        self._manifest_path=Path(manifest);self._preparation_path=Path(preparation)
        self._manifest_sha=hexhash(manifest_sha256);self._preparation_sha=hexhash(preparation_sha256)
        self.out=None
        REGISTRY.mkdir(parents=True,exist_ok=True);plain(REGISTRY)
        self._marker=REGISTRY/(self._manifest_sha+'.consumed.json')
        save(self._marker,dict(scope='BUILD_ONLY',manifest_sha256=self._manifest_sha,
                              preparation_sha256=self._preparation_sha,owner=list(self._birth),claim_tick=self._start))
        # A replacement assignment/hash cannot mint another lifetime in the
        # same original producer. A later authorized build needs a fresh owner.
        self._owner_marker=REGISTRY/('owner-'+digest(canonical(list(self._birth)))+'.consumed.json')
        save(self._owner_marker,dict(owner=list(self._birth),manifest_sha256=self._manifest_sha,claim_tick=self._start))
        try:
            self._manifest,self._raw=read_exact(self._manifest_path,self._manifest_sha);m=self._manifest
            aid=m.get('assignment_id')
            if type(aid) is not str or re.fullmatch('[A-Za-z0-9_-]{1,96}',aid) is None:raise ValueError('Fixed assignment ID required')
            self._assignment_marker=REGISTRY/('assignment-'+digest(aid.encode('ascii'))+'.consumed.json')
            save(self._assignment_marker,dict(assignment_id=aid,manifest_sha256=self._manifest_sha,owner=list(self._birth)))
            prep,self._prep_raw=read_exact(self._preparation_path,self._preparation_sha)
            if canonical(prep)!=canonical(dict(schema='EKA-BUILD-ONLY-PREPARATION-v1',assignment_id=aid,manifest_sha256=self._manifest_sha,
                          scope='BUILD_ONLY',authority='SOURCE_ONLY',attempts=1)):
                raise ValueError('Preparation binding required; never a native/scientific grant')
            keys={'schema','scope','contract','assignment_id','owner_birth','deadline_tick','limits','output_relative',
                  'source','header','interpreter','toolchain','sdk','includes','libraries','dependencies',
                  'environment','invocations','outputs','external_cost_categories','external_settlement_plan'}
            if staged(m):keys.update(('release_pins','root_binding'))
            if (set(m)!=keys or m['schema'] not in ('EKA-BUILD-ONLY-MANIFEST-v1',STAGED_SCHEMA) or m['scope']!='BUILD_ONLY' or
                m['contract']!=(STAGED_CONTRACT if staged(m) else CONTRACT) or birth(m['owner_birth'])!=self._birth or
                canonical(m['limits'])!=canonical(LIMITS) or m['external_cost_categories']!=list(EXTERNAL)):
                raise ValueError('Strictly separate build scope, original owner and explicit unchanged limits required')
            self._end=number(m['deadline_tick'])
            if not self._start<self._end<=self._start+LIMITS['wall_ms']:raise ValueError('Original absolute build deadline required')
            if type(m['output_relative']) is not str or re.fullmatch('runs/eka1-build-only-[A-Za-z0-9_-]{1,96}',m['output_relative']) is None:
                raise ValueError('Fresh fixed build output required')
            self.out=ROOT/m['output_relative']
            if self.out.exists():raise FileExistsError('No output replacement')
            if set(m['source'])!=set(source_names(m)):raise ValueError('Exact reviewed build source closure required')
            if Path(m['interpreter']['path'])!=Path(sys.executable).resolve():raise ValueError('Exact interpreter required')
            if set(m['toolchain'])!={'compiler','linker'}:raise ValueError('Fixed toolchain only')
            if staged(m):
                binding=m['root_binding'];rid=root_binding(m)
                self._root_marker=REGISTRY/('root-'+rid+'.consumed.json')
                save(self._root_marker,dict(root_binding=binding,assignment_sha256=self._manifest_sha,owner=list(self._birth)))
            if staged(m) and (m['header']!=dict(path=str(self.out/DERIVED_OUTPUTS[0])) or
                              m['release_pins']!=release_inputs(m,self.out)):
                raise ValueError('Exact future header path and fixed release derivation required')
            self._inputs()
            inv=m['invocations']
            if type(inv) is not list or len(inv)!=4:raise ValueError('Exact four supervised build slots required')
            for role,item in zip(CATALOGUE,inv):
                tool=m['toolchain']['compiler' if role.startswith('compile') else 'linker']['path']
                if (set(item)!={'role','image','argv'} or item['role']!=role or item['image']!=tool or
                    type(item['argv']) is not list or not 1<=len(item['argv'])<=64 or
                    any(type(a) is not str or not a or len(a)>2048 or any(c in a for c in '\0\r\n') for a in item['argv'])):
                    raise ValueError('Exact pinned supervised invocation DATA required')
            if inv!=invocations(m,self.out):raise ValueError('Only fixed release compile/link arguments; no arbitrary command or scientific source')
            if (type(m['environment']) is not dict or not m['environment'] or
                any(k not in ('SystemRoot','TEMP','TMP') or type(v) is not str or not v or any(c in v for c in '\0\r\n') for k,v in m['environment'].items())):
                raise ValueError('Explicit minimal environment; no ambient tool options/discovery')
            names=m['outputs']
            if (type(names) is not list or not 2<=len(names)<=128 or any(type(n) is not str for n in names) or len(set(n.casefold() for n in names))!=len(names) or
                any(settlement.safe_name(n)!=n for n in names) or
                not set(BUILD_OUTPUTS+(DERIVED_OUTPUTS if staged(m) else ()))<=set(names)):
                raise ValueError('Fixed exact retained output inventory required')
            for p in (self._manifest_path,self._preparation_path,self._marker,self._assignment_marker,self._owner_marker):
                self._files[p]=(p.read_bytes(),(p.stat().st_dev,p.stat().st_ino))
            if staged(m):self._files[self._root_marker]=(self._root_marker.read_bytes(),(self._root_marker.stat().st_dev,self._root_marker.stat().st_ino))
            self.out.mkdir();plain(self.out);self._path=self.out/'build-ledger.jsonl'
            self._fd=os.open(self._path,os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_BINARY,0o600)
            s=os.fstat(self._fd);self._physical=(s.st_dev,s.st_ino)
            self._append(dict(kind='bind',assignment=self._manifest_sha,owner=list(self._birth),deadline=self._end,
                              ledger_identity=list(self._physical),claim_tick=self._start))
            self._check()
        except BaseException as exc:
            self._fail(exc)
            try:self.close()
            except BaseException as cleanup:exc.add_note('Constructor ledger closure incomplete: '+repr(cleanup))
            raise

    def _inputs(self):
        m=self._manifest
        if digest((ROOT/'data/eka1-native-build-decision-20261030.json').read_bytes())!=CONTRACT_SHA:raise ValueError('Approved contract bytes changed')
        if staged(m) and digest((ROOT/AMENDMENT_FILE).read_bytes())!=AMENDMENT_SHA:raise ValueError('Approved staging amendment bytes changed')
        pins={str(ROOT/n):h for n,h in m['source'].items()}
        for name in (*(() if staged(m) else ('header',)),'interpreter',*m['toolchain']):
            item=m['toolchain'][name] if name in m['toolchain'] else m[name]
            if set(item)!={'path','sha256'}:raise ValueError('Exact file identity fields required')
            if item['path'] in pins and pins[item['path']]!=item['sha256']:raise ValueError('Conflicting file pin')
            pins[item['path']]=item['sha256']
        for name in ('sdk','includes','libraries','dependencies'):
            if type(m[name]) is not dict or not m[name]:raise ValueError('Explicit dependency inventories required')
            for path,h in m[name].items():
                if path in pins and pins[path]!=h:raise ValueError('Inconsistent dependency pin')
                pins[path]=h
        for path,h in pins.items():
            p=Path(path)
            if not p.is_absolute():raise ValueError('Absolute frozen input required')
            plain(p)
            if digest(p.read_bytes())!=hexhash(h):raise ValueError('Source/header/toolchain/SDK/dependency bytes changed')
        plan=m['external_settlement_plan']
        if set(plan)!={'path','sha256'}:raise ValueError('Frozen external settlement plan required')
        value,raw=read_exact(Path(plan['path']),plan['sha256'])
        if (value.get('schema')!='EKA-EXTERNAL-SETTLEMENT-PLAN-v1' or
            value.get('assignment_sha256')!=digest(m['assignment_id'].encode('ascii')) or
            value.get('immutable_build_package_sha256')!=recipe(m) or
            birth(value.get('owner_birth'))!=self._birth):raise ValueError('External settlement must bind this logical assignment, input recipe and original owner')

    def _physical_check(self):
        if self._fd is None or self._closed:raise RuntimeError('Ledger closed/incomplete')
        plain(self._path);fd=os.fstat(self._fd);named=self._path.stat()
        if (not stat.S_ISREG(fd.st_mode) or fd.st_nlink!=1 or (fd.st_dev,fd.st_ino)!=self._physical or
            (named.st_dev,named.st_ino)!=self._physical or fd.st_size!=self._bytes or
            os.lseek(self._fd,0,os.SEEK_CUR)!=self._bytes or digest(self._path.read_bytes())!=getattr(self,'_ledger_sha',digest(b''))):
            raise OSError('Physical ledger identity, contents, extent or cursor changed')

    def _append(self,event):
        self._physical_check()
        if self._storage_failed:raise RuntimeError('Incomplete ledger; no append retry')
        raw=canonical(dict(sequence=self._seq,previous=self._tip,event=event))+b'\n'
        try:
            if self._bytes+len(raw)>1048576 or os.write(self._fd,raw)!=len(raw):raise OSError('Partial/oversize ledger retained')
            os.fsync(self._fd)
        except BaseException:self._storage_failed=True;raise
        self._seq+=1;self._bytes+=len(raw);self._tip=digest(raw);self._ledger_sha=digest(self._path.read_bytes())

    def _check(self,final=False):
        if not final and 'final' in self._root_phases:raise RuntimeError('Final root observation consumed; work authority closed')
        if self._failed is not None and not final:raise RuntimeError('Original failure; no reusable preparation')
        if current_birth()!=self._birth:raise ValueError('Original process birth changed')
        if not final and tick()>=self._end:raise TimeoutError('Original deadline expired; no extension')
        if canonical(self._manifest)!=self._raw:raise ValueError('In-memory assignment changed')
        for p,(raw,identity) in self._files.items():
            plain(p);s=p.stat()
            if p.read_bytes()!=raw or (s.st_dev,s.st_ino)!=identity:raise ValueError('Immutable binding replaced')
        self._physical_check();self._inputs()
        if staged(self._manifest) and self._derived is not None:
            if any(p.handle is None for p in self._pins):raise ValueError('Retained derived input handle closed early')
            if stage_binding(self._manifest,self._manifest_sha,self._physical,self._start,ledger_rows(self._path),self.out)!=self._derived:
                raise ValueError('In-memory StageB evidence changed')

    def _fail(self,exc):
        if self._failed is None:self._failed=type(exc).__name__+': '+str(exc)
        if self.out is not None and self.out.exists() and not (self.out/'failure.json').exists():
            try:save(self.out/'failure.json',dict(first_failure=self._failed,scope='BUILD_ONLY',
                     opaque_nested_attempts='UNKNOWN',debits=self._debits,unresolved_costs=['root_native_measurement_qualification',*EXTERNAL],native_entry_enabled=False))
            except BaseException as write:exc.add_note('Failure evidence write incomplete: '+repr(write))

    def precharge(self,role):
        with self._mutex:
            try:
                self._check()
                if self._finalized or self._pending is not None or self._attempts>=4 or role!=CATALOGUE[self._attempts]:
                    raise ValueError('Uncharged, repeated or out-of-order supervised attempt')
                if staged(self._manifest) and self._attempts>=2 and self._derived is None:
                    raise ValueError('StageB requires once-frozen derived header and manifest')
                self._append(dict(kind='supervised_attempt',role=role,index=self._attempts,request_sha256=digest(canonical(self._manifest['invocations'][self._attempts]))))
                self._pending=(role,self._attempts);self._attempts+=1
                return dict(role=role,index=self._attempts-1,ledger_identity=list(self._physical),ledger_tip=self._tip,
                            scope='SOURCE_ONLY_DEBIT_NOT_EXECUTION_AUTHORITY')
            except BaseException as exc:self._fail(exc);raise

    def derive_stage_b(self,sample):
        """Freeze fixed derived DATA once; creates no process or native authority."""
        with self._mutex:
            try:
                self._check()
                if (not staged(self._manifest) or self._finalized or self._derive_consumed or
                    self._attempts!=2 or len(self._outcomes)!=2 or self._pending is not None):
                    raise ValueError('Exactly one successful StageA before derivation required')
                self._derive_consumed=True
                raw=canonical(sample)
                if len(raw)>65536:raise ValueError('Bounded StageA sample required')
                sample=json.loads(raw)
                self._append(dict(kind='derive_attempt',input_recipe_sha256=recipe(self._manifest),stage_a_sample=sample))
                created=[birth(x[2]['birth']) for x in self._outcomes]
                validate_sample(sample,self._manifest,self._manifest_sha,self._physical,created,self._start)
                validate_limits(sample,self._manifest)
                derived_tick=tick()
                if sample['measured_tick']>derived_tick:raise ValueError('StageA sample cannot be from the future')
                if sample.get('root_handle_retained') is not True:raise ValueError('StageA root must remain retained')
                dll=self.out/'eka1_owner_watchdog.dll';plain(dll);h,n=settlement.file_digest(dll)
                pin=CapsuleReadHandle(dll,h);self._pins.append(pin)
                info=dll.stat();watchdog=dict(path=str(dll),sha256=h,file_identity=[info.st_dev,info.st_ino])
                pins=dict(self._manifest['release_pins'],watchdog_sha=h)
                header=self.out/DERIVED_OUTPUTS[0];data=release_header(pins)
                with header.open('xb') as stream:
                    if stream.write(data)!=len(data):raise OSError('Short derived header write')
                    stream.flush();os.fsync(stream.fileno())
                self._pins.append(CapsuleReadHandle(header,digest(data)))
                info=header.stat()
                d=dict(schema='EKA-BUILD-ONLY-DERIVED-STAGE-B-v1',assignment_sha256=self._manifest_sha,
                       input_recipe_sha256=recipe(self._manifest),owner_birth=list(self._birth),ledger_identity=list(self._physical),
                       deadline_tick=self._end,prior_ledger_tip=self._tip,derived_tick=derived_tick,stage_a_sample=sample,watchdog=watchdog,
                       header=dict(path=str(header),sha256=digest(data),file_identity=[info.st_dev,info.st_ino]),
                       release_pins=pins,invocations=self._manifest['invocations'][2:])
                path=self.out/DERIVED_OUTPUTS[1];save(path,d);dsha=digest(path.read_bytes())
                self._pins.append(CapsuleReadHandle(path,dsha))
                for p in (dll,header,path):self._files[p]=(p.read_bytes(),(p.stat().st_dev,p.stat().st_ino))
                self._append(dict(kind='derived_stage_b',manifest_sha256=dsha))
                self._derived=json.loads(canonical(d));self._check()
                return dict(manifest_sha256=dsha,header_sha256=digest(data),decision='NO_GO',native_entry_enabled=False)
            except BaseException as exc:
                self._fail(exc)
                try:self._close_pins()
                except BaseException as cleanup:
                    exc.add_note('Derived input closure incomplete: '+repr(cleanup))
                    for note in getattr(cleanup,'__notes__',()):exc.add_note(note)
                raise

    def outcome(self,role,index,result):
        with self._mutex:
            try:
                self._check()
                if self._pending!=(role,index) or type(index) is not int:raise ValueError('No retained precharge for outcome')
                if type(result) is not dict or result.get('status') not in ('CREATED','CREATE_FAILED','REJECTED'):raise ValueError('Exact attempted-start outcome required')
                result=json.loads(canonical(result))  # Detach caller-owned nested lists BEFORE durable append.
                if result['status']=='CREATED':
                    birth(result['birth'])
                    if birth(result['parent_birth'])!=self._birth:raise ValueError('Original parent birth differs')
                    if result['image_sha256']!=self._manifest['toolchain']['compiler' if role.startswith('compile') else 'linker']['sha256']:
                        raise ValueError('Attempt image differs')
                elif not isinstance(result.get('error'),str) or not result['error']:raise ValueError('Failed creation error must be retained')
                self._append(dict(kind='outcome',role=role,index=index,result=result));self._outcomes.append((role,index,result.copy()));self._pending=None
                if (result['status']!='CREATED' or type(result.get('exit_code')) is not int or result['exit_code']!=0 or
                    any(result.get(n) is not True for n in ('signaled','root_member','EOF','termination_succeeded'))):
                    raise RuntimeError('Failed/rejected/incomplete start is terminal; reservation consumed')
            except BaseException as exc:self._fail(exc);raise

    def finalize(self,sample):
        with self._mutex:
            if self._finalized:raise RuntimeError('Final sample consumed exactly once; no replacement')
            self._finalized=True
            report=dict(scope='BUILD_ONLY',assignment_sha256=self._manifest_sha,opaque_nested_attempts='UNKNOWN',
                        USER_ticks=None,KERNEL_ticks=None,root_total_ticks=None,known_component_ticks_lower_bound=0,
                        native_entry_enabled=False,decision='NO_GO',actual_native_custody_independently_verified=False,
                        unresolved_costs=['root_native_measurement_qualification',*EXTERNAL],debits=self._debits)
            try:
                if not isinstance(sample,dict):raise ValueError('Missing raw root counters/custody')
                raw=canonical(sample)
                if len(raw)>65536:raise ValueError('Bounded raw root sample required')
                sample=json.loads(raw);report['raw_root_sample']=sample
                for name in ('USER_ticks','KERNEL_ticks'):
                    if sample.get(name) is not None:report[name]=number(sample[name]);report['known_component_ticks_lower_bound']+=sample[name]
                if report['USER_ticks'] is None or report['KERNEL_ticks'] is None:raise ValueError('Missing USER or KERNEL cost remains unresolved')
                report['root_total_ticks']=report['USER_ticks']+report['KERNEL_ticks']
                self._check(final=True)
                created=[birth(x[2]['birth']) for x in self._outcomes if x[2]['status']=='CREATED']
                u,k,members=validate_sample(sample,self._manifest,self._manifest_sha,self._physical,created,self._start)
                if staged(self._manifest) and self._derived is not None:
                    cumulative_stage_sample(sample,self._derived['stage_a_sample'])
                    if sample['closed_tick']<self._derived['derived_tick'] or sample['measured_tick']>tick():
                        raise ValueError('Final staged measurement ordering differs')
                self._debits.append(dict(root_identity=sample['root_identity'],USER_ticks=report['USER_ticks'],KERNEL_ticks=report['KERNEL_ticks'],nested_added=False))
                report['observed_births']=len(members);report['observed_job_total_processes']=number(sample['job_total_processes'])
                validate_limits(sample,self._manifest)
                if staged(self._manifest) and self._derived is None:raise ValueError('Incomplete staged build; no derived binding')
                if self._pending is not None or self._attempts!=4 or len(created)!=4 or self._failed is not None:raise ValueError('Incomplete/failed build attempt')
                inventory={};size=0
                for p in self.out.rglob('*'):
                    plain(p)
                    if not p.is_file():continue
                    name=p.relative_to(self.out).as_posix();h,n=settlement.file_digest(p);inventory[name]=h;size+=n
                if set(inventory)!=set(self._manifest['outputs'])|{'build-ledger.jsonl'}:raise ValueError('Missing/extra build output')
                if len(inventory)>LIMITS['archive_files'] or size>LIMITS['archive_bytes']:raise ValueError('Build retained extent exceeded')
                report['output_inventory']=inventory;report['retained_bytes_before_final_write']=size
                if tick()>self._end:raise TimeoutError('Original absolute deadline exceeded')
                report['status']='PROVISIONAL_BUILD_COSTS_EXTERNAL_SETTLEMENT_REQUIRED'
                report['input_recipe_sha256']=recipe(self._manifest)
                # This live owner CANNOT settle its own later signaled lifetime,
                # archive, final write or ledger close. Distinct phase below.
                save(self.out/'build-final.json',report);return report
            except BaseException as exc:
                report.update(status='TERMINAL_INCOMPLETE_UNRESOLVED',first_failure=self._failed or type(exc).__name__+': '+str(exc))
                self._fail(exc)
                try:save(self.out/'build-final.json',report)
                except BaseException as write:exc.add_note('Final cost evidence incomplete: '+repr(write))
                raise
            finally:
                primary=sys.exception()
                try:self.close()
                except BaseException as cleanup:
                    if primary is not None:
                        primary.add_note('Ledger closure incomplete: '+repr(cleanup))
                        for note in getattr(cleanup,'__notes__',()):primary.add_note(note)
                    else:raise

    def preflight(self):
        try:self._check()
        except BaseException as exc:self._fail(exc);raise
        return dict(decision='NO_GO',scope='BUILD_ONLY',native_entry_enabled=False,operator_authorization=False,
                    opaque_nested_attempts='UNKNOWN',physical_ledger_identity=list(self._physical),
                    original_owner=list(self._birth),original_deadline=self._end,
                    unqualified=['OS_containment_and_birth_image_custody','complete_executed_dependency_provenance',
                                 'root_USER_KERNEL_measurement_and_external_settlement','independent_exact_single_build_manifest','separate_human_execution_authorization'])

    def _root_observation_context(self):
        """Source binding only; kernel-object comparison is recorded separately."""
        self._check(final=True)
        expected=(self._birth,self._manifest_sha,self._physical,self._end,root_binding(self._manifest),str(self.out))
        if self._root_context is not None and expected!=self._root_context:
            raise ValueError('Original root-observation owner/manifest/ledger/deadline changed')
        for name in ('tools/eka1_cpu_accounting.py','experiments/process_limits.py'):
            path=ROOT/name
            if self._manifest['dependencies'].get(str(path))!=digest(path.read_bytes()):
                raise ValueError('Root observation dependency not pinned: '+name)
        kernelbase=Path(self._manifest['environment']['SystemRoot'])/'System32/KernelBase.dll'
        if self._manifest['dependencies'].get(str(kernelbase))!=digest(kernelbase.read_bytes()):
            raise ValueError('Exact KernelBase observation dependency not pinned')
        return expected

    def _root_observation_record(self,phase):
        context=self._root_context or (self._birth,self._manifest_sha,self._physical,self._end,None,str(self.out))
        return dict(schema='EKA-BUILD-ONLY-RAW-ROOT-OBSERVATION-v1',phase=phase,
                    scope='RAW_ROOT_COUNTERS_ONLY_NOT_A_FULL_BUILD_SAMPLE',decision='NO_GO',
                    assignment_sha256=context[1],owner_birth=list(context[0]),
                    ledger_identity=list(context[2]),logical_root_identity=context[4],
                    deadline_tick=context[3],raw=None,available_USER_ticks=None,available_KERNEL_ticks=None,
                    known_component_ticks_lower_bound=0,custody_errors=[],debit_performed=False,
                    native_entry_enabled=False,actual_native_custody_independently_qualified=False)

    @staticmethod
    def _validate_root_observation(raw,initial=False,previous=None):
        for name in ('user_ticks','kernel_ticks','period_user_ticks','period_kernel_ticks','active','total_processes',
                     'cpu_limit_ticks','memory_limit','process_limit','flags'):
            number(raw[name])
        if (raw['period_user_ticks']!=raw['user_ticks'] or raw['period_kernel_ticks']!=raw['kernel_ticks'] or
            raw['cpu_limit_ticks']!=LIMITS['USER_ticks'] or raw['memory_limit']!=LIMITS['memory_bytes'] or
            raw['process_limit']!=LIMITS['active_processes'] or raw['flags']!=0x220c or
            raw['active']>LIMITS['active_processes']):
            raise ValueError('Root observation epoch or unchanged limits differ')
        if initial and any(raw[n] for n in ('user_ticks','kernel_ticks','active','total_processes')):
            raise ValueError('Root observation must begin in fresh zero epoch')
        if previous is not None and any(raw[n]<previous[n] for n in ('user_ticks','kernel_ticks','total_processes')):
            raise ValueError('Root lifetime observation counter decreased')
        if not initial and raw['active']!=0:raise ValueError('Raw root remains active; closure unresolved')
        if raw['user_ticks']>LIMITS['USER_ticks']:raise ValueError('Terminal root USER resource overrun')

    def bind_root_observation(self,job):
        """Gated observation only. No process creation, continuation or grant."""
        native_admission()  # Must precede claims, imports and all kernel APIs.
        with self._mutex:
            record_write_attempted=False;duplicate_acquired=False
            try:
                self._check()
                if (not staged(self._manifest) or self._root_observation_consumed or self._attempts or
                    self._pending is not None or self._derived is not None):
                    raise ValueError('One root observation binding before any precharge required')
                self._root_observation_consumed=True
                self._root_context=self._root_observation_context()
                if not set(ROOT_OBSERVATION_FILES)<=set(self._manifest['outputs']):
                    raise ValueError('Root observation receipts must be reserved in output inventory')
                from experiments.process_limits import Job,checked
                from tools.eka1_cpu_accounting import root_snapshot
                from types import SimpleNamespace
                import ctypes
                from ctypes import wintypes as wt
                if type(job) is not Job or not job.handle:raise TypeError('Exact live existing Job required')
                record=self._root_observation_record('initial')
                save(self.out/ROOT_OBSERVATION_FILES[0],dict(record,status='PENDING_UNRESOLVED'))
                k=job.k;self._root_job=job;self._root_api=k
                definitions={'GetCurrentProcess':([],wt.HANDLE),
                    'GetModuleHandleW':([wt.LPCWSTR],wt.HMODULE),
                    'DuplicateHandle':([wt.HANDLE,wt.HANDLE,wt.HANDLE,ctypes.POINTER(wt.HANDLE),wt.DWORD,wt.BOOL,wt.DWORD],wt.BOOL),
                    }
                for name,(args,result) in definitions.items():
                    fn=getattr(k,name);fn.argtypes=args;fn.restype=result
                kernelbase=Path(self._manifest['environment']['SystemRoot'])/'System32/KernelBase.dll'
                module=k.GetModuleHandleW(str(kernelbase));checked(module)
                # Borrow an already loaded core module; no LoadLibrary reference or FreeLibrary ownership.
                # This does not qualify loaded-image identity or exclude concurrent module unloading.
                self._root_compare=ctypes.WinDLL(str(kernelbase),handle=module,use_last_error=True).CompareObjectHandles
                self._root_compare.argtypes=[wt.HANDLE,wt.HANDLE];self._root_compare.restype=wt.BOOL
                process=k.GetCurrentProcess();held=wt.HANDLE()
                checked(k.DuplicateHandle(process,job.handle,process,ctypes.byref(held),0,False,2))
                if not held.value:raise OSError('Root duplicate unavailable')
                self._root_duplicate=held.value
                duplicate_acquired=True
                if not self._root_compare(job.handle,self._root_duplicate):
                    raise OSError('Root duplicate kernel-object identity differs')
                record['same_kernel_object']=True
                record['raw']=root_snapshot(SimpleNamespace(k=k,handle=self._root_duplicate))
                self._root_observation_values(record)
                self._validate_root_observation(record['raw'],initial=True)
                self._root_initial=json.loads(canonical(record['raw']));self._root_last=self._root_initial
                self._root_observation_context()
                record.update(status='INITIAL_ZERO_OBSERVED_UNQUALIFIED',observed_tick=tick())
                if record['observed_tick']>=self._end:raise TimeoutError('Original observation deadline exceeded')
                record_write_attempted=True
                save(self.out/ROOT_OBSERVATION_FILES[1],record)
                return record
            except BaseException as exc:
                self._fail(exc)
                if 'record' in locals():
                    if record['raw'] is None and hasattr(exc,'raw_root_partial'):
                        record['raw']=exc.raw_root_partial.copy();self._root_observation_values(record)
                    record.update(status='FAILED_UNRESOLVED',failure=repr(exc))
                    self._retain_root_observation_failure(exc,self.out/ROOT_OBSERVATION_FILES[1],record,persist=not record_write_attempted)
                if duplicate_acquired:
                    try:self._close_root_observation()
                    except BaseException as cleanup:
                        exc.add_note('Root duplicate closure incomplete: '+repr(cleanup))
                        for note in getattr(cleanup,'__notes__',()):exc.add_note(note)
                raise

    @staticmethod
    def _root_observation_values(record):
        raw=record['raw']
        if isinstance(raw,dict):
            for name,key in (('USER','user_ticks'),('KERNEL','kernel_ticks')):
                value=raw.get(key)
                if type(value) is int and 0<=value<2**63:
                    record['available_'+name+'_ticks']=value
                    record['known_component_ticks_lower_bound']+=value

    @staticmethod
    def _retain_root_observation_failure(exc,path,record,*,persist=True):
        exc.root_observation=json.loads(canonical(record))
        if not persist:
            exc.add_note('Raw observation write already attempted; pending evidence unresolved, no retry')
            return
        try:save(path,record)
        except BaseException as write:exc.add_note('Raw observation write incomplete; no retry: '+repr(write))

    def snapshot_root(self,phase):
        """One StageA observation and one final raw read; neither is a debit."""
        native_admission()
        with self._mutex:
            if phase not in ('stage_a','final'):
                exc=ValueError('Fixed root observation phase required');self._fail(exc);raise exc
            if phase in self._root_phases:
                exc=RuntimeError('Root observation phase consumed; no retry');self._fail(exc);raise exc
            self._root_phases.add(phase)  # Read and persistence failures consume the phase too.
            record=self._root_observation_record(phase);errors=[];record_write_attempted=False
            path=Path(self._root_context[5] if self._root_context is not None else self.out)/ROOT_OBSERVATION_FILES[2 if phase=='stage_a' else 3]
            try:
                if phase=='stage_a' and 'final' in self._root_phases:raise RuntimeError('StageA observation cannot follow final capture')
                if self._root_duplicate is None or self._root_close_attempted or self._root_initial is None:
                    raise RuntimeError('Retained initialized root observation unavailable')
                try:
                    self._root_observation_context()
                    if phase=='stage_a' and (self._failed is not None or self._attempts!=2 or self._pending is not None or self._derived is not None):
                        raise ValueError('StageA observation requires its exact completed two slots')
                    if self._failed is not None:raise RuntimeError('Original failure remains terminal')
                    if not self._root_job.handle or not self._root_compare(self._root_job.handle,self._root_duplicate):
                        raise OSError('Original root handle lost or kernel object replaced')
                    record['same_kernel_object']=True
                except BaseException as binding:
                    errors.append(repr(binding))
                    if phase!='final':raise
                from tools.eka1_cpu_accounting import root_snapshot
                from types import SimpleNamespace
                record['raw']=root_snapshot(SimpleNamespace(k=self._root_api,handle=self._root_duplicate))
                self._root_observation_values(record)
                try:self._validate_root_observation(record['raw'],previous=self._root_last)
                except BaseException as invalid:errors.append(repr(invalid))
                record['observed_tick']=tick()
                if record['observed_tick']>self._end:errors.append('Original absolute deadline exceeded')
                record['custody_errors']=errors
                if errors:raise ValueError('Raw root observation terminal unresolved: '+repr(errors))
                self._root_last=json.loads(canonical(record['raw']))
                record['status']='RAW_ROOT_OBSERVED_UNQUALIFIED_NOT_BILLED'
                record_write_attempted=True
                save(path,record)
                return record
            except BaseException as exc:
                if record['raw'] is None and hasattr(exc,'raw_root_partial'):
                    record['raw']=exc.raw_root_partial.copy();self._root_observation_values(record)
                self._fail(exc);record.update(status='FAILED_UNRESOLVED',failure=repr(exc),custody_errors=errors)
                self._retain_root_observation_failure(exc,path,record,persist=not record_write_attempted)
                raise

    def _close_root_observation(self):
        if self._root_duplicate is None:return
        if self._root_close_attempted:raise OSError('Prior root duplicate closure incomplete; no retry')
        self._root_close_attempted=True
        try:
            from experiments.process_limits import checked
            checked(self._root_api.CloseHandle(self._root_duplicate))
            self._root_duplicate=None
        except BaseException as exc:
            self._cleanup_errors.append(repr(exc));self._fail(exc)
            if not self._root_cleanup_recorded:
                self._root_cleanup_recorded=True
                try:save(self.out/'root-observation-cleanup-failure.json',dict(first_failure=self._failed,
                         cleanup_errors=[repr(exc)[:2048]],unresolved_root_duplicate=True,retry=False,native_entry_enabled=False))
                except BaseException as write:exc.add_note('Root cleanup tail incomplete; no retry: '+repr(write))
            raise

    def _close_pins(self):
        errors=[]
        for pin in reversed(self._pins):
            try:
                if not pin.close_attempted:pin.close()
                elif pin.handle is not None:raise OSError('Prior retained handle closure incomplete; no retry')
            except BaseException as exc:errors.append(exc);self._cleanup_errors.append(repr(exc));self._fail(exc)
        if errors:
            first=errors[0]
            details=[repr(error)[:2048] for error in errors]
            first.add_note('All retained DATA handle closure errors: '+repr(details))
            if not self._pin_cleanup_recorded:
                self._pin_cleanup_recorded=True  # Failed writes are consumed too; never retry.
                try:save(self.out/'derived-cleanup-failure.json',dict(first_failure=self._failed,
                         cleanup_errors=details,unresolved_handles=sum(p.handle is not None for p in self._pins),
                         native_entry_enabled=False,retry=False))
                except BaseException as write:first.add_note('Cleanup tail write incomplete; no retry: '+repr(write))
            raise first

    def close(self):
        if not self._closed:
            self._closed=True
            pin_error=None
            try:self._close_pins()
            except BaseException as exc:pin_error=exc
            try:self._close_root_observation()
            except BaseException as root_error:
                if pin_error is None:pin_error=root_error
                else:
                    pin_error.add_note('Root duplicate closure incomplete: '+repr(root_error))
                    for note in getattr(root_error,'__notes__',()):pin_error.add_note(note)
            if self._fd is not None:
                fd=self._fd
                try:os.close(fd)
                except BaseException as exc:
                    self._cleanup_errors.append(repr(exc));self._fail(exc)
                    if pin_error is not None:
                        exc.add_note('Retained input/root closure incomplete: '+repr(pin_error))
                        for note in getattr(pin_error,'__notes__',()):exc.add_note(note)
                    raise
                else:self._fd=None
            if pin_error is not None:raise pin_error

def native_admission(*unused,**ignored):
    raise NativeQualificationRequired('NO_GO: source-only build contract; no compilation/execution authority')

def settle_build(manifest_path,manifest_sha256,receipt_path,receipt_sha256,*,external_receipt_sha256):
    """Distinct external DATA phase after original-owner closure. Never authority.

    Burn the logical build settlement before trusting replacement receipts.
    Exact payload binds this build; existing settlement validates owner death,
    disjoint external CPU/archive/restoration. Native custody remains unknown.
    """
    m,mraw=read_exact(Path(manifest_path),manifest_sha256)
    if m.get('scope')!='BUILD_ONLY' or m.get('contract')!=(STAGED_CONTRACT if staged(m) else CONTRACT):raise ValueError('Separate build scope required')
    aid=m['assignment_id'];key=digest(aid.encode('ascii'));REGISTRY.mkdir(parents=True,exist_ok=True);plain(REGISTRY)
    claim=REGISTRY/('settlement-'+key+'.consumed.json')
    save(claim,dict(assignment_id=aid,manifest_sha256=manifest_sha256,receipt_sha256=receipt_sha256,status='CONSUMED_PENDING_UNRESOLVED'))
    report=dict(scope='BUILD_ONLY',decision='NO_GO',native_entry_enabled=False,opaque_nested_attempts='UNKNOWN',
                unresolved_costs=list(EXTERNAL),actual_native_custody_independently_verified=False)
    try:
        if current_birth()==birth(m['owner_birth']):raise ValueError('Live original owner cannot settle its own closure')
        out=ROOT/m['output_relative'];receipt_path=Path(receipt_path)
        if (m.get('schema') not in ('EKA-BUILD-ONLY-MANIFEST-v1',STAGED_SCHEMA) or canonical(m.get('limits'))!=canonical(LIMITS) or
            set(m.get('source',{}))!=set(source_names(m)) or m.get('external_cost_categories')!=list(EXTERNAL) or
            m.get('invocations')!=invocations(m,out)):raise ValueError('Frozen build contract changed')
        if staged(m):
            rid=root_binding(m);plain(REGISTRY/('root-'+rid+'.consumed.json'))
            if (REGISTRY/('root-'+rid+'.consumed.json')).read_bytes()!=canonical(dict(root_binding=m['root_binding'],assignment_sha256=manifest_sha256,owner=m['owner_birth'])):
                raise ValueError('Retained once-only root claim differs')
            if (digest((ROOT/AMENDMENT_FILE).read_bytes())!=AMENDMENT_SHA or
                m['release_pins']!=release_inputs(m,out) or m['header']!=dict(path=str(out/DERIVED_OUTPUTS[0]))):
                raise ValueError('Frozen staged derivation changed')
        if receipt_path!=out/'build-final.json':raise ValueError('Fixed build receipt path required')
        r,rraw=read_exact(receipt_path,receipt_sha256)
        if (r.get('scope')!='BUILD_ONLY' or r.get('assignment_sha256')!=manifest_sha256 or r.get('input_recipe_sha256')!=recipe(m) or
            r.get('status')!='PROVISIONAL_BUILD_COSTS_EXTERNAL_SETTLEMENT_REQUIRED' or r.get('opaque_nested_attempts')!='UNKNOWN'):
            raise ValueError('Exact provisional build required; terminal failures cannot be promoted')
        u=number(r['USER_ticks']);k=number(r['KERNEL_ticks']);sample=r['raw_root_sample']
        if (r['root_total_ticks']!=u+k or len(r['debits'])!=1 or r['debits'][0]!=dict(root_identity=sample['root_identity'],USER_ticks=u,KERNEL_ticks=k,nested_added=False)):
            raise ValueError('Inconsistent or duplicated root cost')
        report.update(root_total_ticks=u+k,root_debit=r['debits'][0])
        ledger=out/'build-ledger.jsonl';lraw=ledger.read_bytes();rows=[json.loads(x) for x in lraw.splitlines()]
        if digest(lraw)!=r['output_inventory'].get('build-ledger.jsonl') or len(rows)!=(11 if staged(m) else 9):raise ValueError('Exact retained ledger required')
        tip='0'*64
        for i,row in enumerate(rows):
            if row['sequence']!=i or type(row['sequence']) is not int or row['previous']!=tip:raise ValueError('Ledger sequence/hash chain differs')
            tip=digest(canonical(row)+b'\n')
        plain(ledger);info=ledger.stat();physical=(info.st_dev,info.st_ino)
        claim_tick=number(rows[0]['event']['claim_tick'])
        if (not claim_tick<m['deadline_tick']<=claim_tick+LIMITS['wall_ms'] or
            rows[0]['event']!=dict(kind='bind',assignment=manifest_sha256,owner=m['owner_birth'],deadline=m['deadline_tick'],
                                  ledger_identity=list(physical),claim_tick=claim_tick)):raise ValueError('Ledger binding changed')
        created=[]
        for i,role in enumerate(CATALOGUE):
            offset=2 if staged(m) and i>=2 else 0
            a=rows[1+i*2+offset]['event'];o=rows[2+i*2+offset]['event']
            if a!=dict(kind='supervised_attempt',role=role,index=i,request_sha256=digest(canonical(m['invocations'][i]))) or o['kind']!='outcome' or o['role']!=role or o['index']!=i:
                raise ValueError('Supervised attempt not durably precharged before outcome')
            v=o['result'];created.append(birth(v['birth']))
            if (v['status']!='CREATED' or birth(v['parent_birth'])!=birth(m['owner_birth']) or
                v['image_sha256']!=m['toolchain']['compiler' if role.startswith('compile') else 'linker']['sha256'] or
                type(v.get('exit_code')) is not int or v['exit_code']!=0 or
                any(v.get(n) is not True for n in ('signaled','root_member','EOF','termination_succeeded'))):raise ValueError('Incomplete attempted-start evidence')
        raw_u,raw_k,members=validate_sample(sample,m,manifest_sha256,physical,created,claim_tick)
        derived=None
        if staged(m):
            derived=stage_binding(m,manifest_sha256,physical,claim_tick,rows,out)
            cumulative_stage_sample(sample,derived['stage_a_sample'])
            if sample['closed_tick']<derived['derived_tick']:raise ValueError('Final closure precedes derivation')
        if len(set(created))!=4 or (raw_u,raw_k)!=(u,k):raise ValueError('Changed raw root cost/custody')
        validate_limits(sample,m)
        retained={}
        for path in out.rglob('*'):
            plain(path)
            if path.is_file():retained[path.relative_to(out).as_posix()]=settlement.file_digest(path)[0]
        expected_retained=dict(r['output_inventory'],**{'build-final.json':receipt_sha256})
        if retained!=expected_retained:raise ValueError('Retained build output or failure tail changed')
        plan=m['external_settlement_plan'];p,praw=read_exact(Path(plan['path']),plan['sha256'])
        if p.get('assignment_sha256')!=key or p.get('owner_birth')!=m['owner_birth'] or p.get('immutable_build_package_sha256')!=recipe(m):
            raise ValueError('External settlement changed build recipe/owner/assignment')
        if any(s['root_identity']==sample['root_identity'] or set(birth(x) for x in s['members']).intersection(members) for s in p['scopes']):
            raise ValueError('External settlement double bills build root/member')
        evidence=Path(plan['path']).parent
        if evidence==out or out in evidence.parents or evidence in out.parents:raise ValueError('Disjoint evidence roots required')
        expected={'build/manifest.json':manifest_sha256,'build/receipt.json':receipt_sha256,
                  'build/header.h':derived['header']['sha256'] if derived is not None else m['header']['sha256']}
        expected.update({'build/source/'+n:h for n,h in m['source'].items()})
        expected.update({'build/output/'+n:h for n,h in r['output_inventory'].items()})
        actual={x.relative_to(evidence/'payload').as_posix():settlement.file_digest(x)[0] for x in (evidence/'payload').rglob('*') if x.is_file()}
        if actual!=expected:raise ValueError('Archive must contain this exact manifest/header/source/output/ledger/receipt package')
        report['external']=settlement.settle(Path(plan['path']),plan['sha256'],evidence/'settlement-input.json',external_receipt_sha256)
        if report['external'].get('covered_measurement_fields_complete') is not True:
            raise ValueError('Missing covered external CPU remains terminal unresolved debt')
        archive=report['external']['archive']
        buildfiles=[x for x in out.rglob('*') if x.is_file()]
        if len(buildfiles)+archive['total_retained_files']>LIMITS['archive_files'] or sum(x.stat().st_size for x in buildfiles)+archive['total_retained_bytes']>LIMITS['archive_bytes']:
            raise ValueError('Combined build/archive/restore retained cap exceeded')
        report.update(status='SOURCE_CONSISTENT_EXACT_BUILD_ARCHIVE_NATIVE_UNQUALIFIED',manifest_sha256=manifest_sha256,receipt_sha256=receipt_sha256)
        save(claim.with_suffix('.result.json'),report);return report
    except BaseException as exc:
        report.update(status='TERMINAL_UNRESOLVED',first_failure=type(exc).__name__+': '+str(exc))
        try:save(claim.with_suffix('.failure.json'),report)
        except BaseException as write:exc.add_note('External build failure write incomplete: '+repr(write))
        raise
