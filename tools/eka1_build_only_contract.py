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

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'runs/eka1-build-only-registry-v1'
CONTRACT='EKA-BUILD-ONLY-METERED-RELEASE-v1'
CONTRACT_SHA='a24c1a888d286a5cf5919c0725bb1330e21ab1d4e207ef6efa1512f4b3254952'
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
            if (set(m)!=keys or m['schema']!='EKA-BUILD-ONLY-MANIFEST-v1' or m['scope']!='BUILD_ONLY' or
                m['contract']!=CONTRACT or birth(m['owner_birth'])!=self._birth or
                canonical(m['limits'])!=canonical(LIMITS) or m['external_cost_categories']!=list(EXTERNAL)):
                raise ValueError('Strictly separate build scope, original owner and explicit unchanged limits required')
            self._end=number(m['deadline_tick'])
            if not self._start<self._end<=self._start+LIMITS['wall_ms']:raise ValueError('Original absolute build deadline required')
            if type(m['output_relative']) is not str or re.fullmatch('runs/eka1-build-only-[A-Za-z0-9_-]{1,96}',m['output_relative']) is None:
                raise ValueError('Fresh fixed build output required')
            self.out=ROOT/m['output_relative']
            if self.out.exists():raise FileExistsError('No output replacement')
            if set(m['source'])!=set(SOURCES):raise ValueError('Exact reviewed build source closure required')
            if Path(m['interpreter']['path'])!=Path(sys.executable).resolve():raise ValueError('Exact interpreter required')
            if set(m['toolchain'])!={'compiler','linker'}:raise ValueError('Fixed toolchain only')
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
                not set(BUILD_OUTPUTS)<=set(names)):
                raise ValueError('Fixed exact retained output inventory required')
            for p in (self._manifest_path,self._preparation_path,self._marker,self._assignment_marker,self._owner_marker):
                self._files[p]=(p.read_bytes(),(p.stat().st_dev,p.stat().st_ino))
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
        pins={str(ROOT/n):h for n,h in m['source'].items()}
        for name in ('header','interpreter',*m['toolchain']):
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
        if self._failed is not None and not final:raise RuntimeError('Original failure; no reusable preparation')
        if current_birth()!=self._birth:raise ValueError('Original process birth changed')
        if not final and tick()>=self._end:raise TimeoutError('Original deadline expired; no extension')
        if canonical(self._manifest)!=self._raw:raise ValueError('In-memory assignment changed')
        for p,(raw,identity) in self._files.items():
            plain(p);s=p.stat()
            if p.read_bytes()!=raw or (s.st_dev,s.st_ino)!=identity:raise ValueError('Immutable binding replaced')
        self._physical_check();self._inputs()

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
                self._append(dict(kind='supervised_attempt',role=role,index=self._attempts,request_sha256=digest(canonical(self._manifest['invocations'][self._attempts]))))
                self._pending=(role,self._attempts);self._attempts+=1
                return dict(role=role,index=self._attempts-1,ledger_identity=list(self._physical),ledger_tip=self._tip,
                            scope='SOURCE_ONLY_DEBIT_NOT_EXECUTION_AUTHORITY')
            except BaseException as exc:self._fail(exc);raise

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
                self._debits.append(dict(root_identity=sample['root_identity'],USER_ticks=report['USER_ticks'],KERNEL_ticks=report['KERNEL_ticks'],nested_added=False))
                report['observed_births']=len(members);report['observed_job_total_processes']=number(sample['job_total_processes'])
                validate_limits(sample,self._manifest)
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
                    if primary is not None:primary.add_note('Ledger closure incomplete: '+repr(cleanup))
                    else:raise

    def preflight(self):
        try:self._check()
        except BaseException as exc:self._fail(exc);raise
        return dict(decision='NO_GO',scope='BUILD_ONLY',native_entry_enabled=False,operator_authorization=False,
                    opaque_nested_attempts='UNKNOWN',physical_ledger_identity=list(self._physical),
                    original_owner=list(self._birth),original_deadline=self._end,
                    unqualified=['OS_containment_and_birth_image_custody','complete_executed_dependency_provenance',
                                 'root_USER_KERNEL_measurement_and_external_settlement','independent_exact_single_build_manifest','separate_human_execution_authorization'])

    def close(self):
        if not self._closed:
            self._closed=True
            if self._fd is not None:
                fd=self._fd
                try:os.close(fd)
                except BaseException as exc:
                    self._cleanup_errors.append(repr(exc));self._fail(exc);raise
                else:self._fd=None

def native_admission(*unused,**ignored):
    raise NativeQualificationRequired('NO_GO: source-only build contract; no compilation/execution authority')

def settle_build(manifest_path,manifest_sha256,receipt_path,receipt_sha256,*,external_receipt_sha256):
    """Distinct external DATA phase after original-owner closure. Never authority.

    Burn the logical build settlement before trusting replacement receipts.
    Exact payload binds this build; existing settlement validates owner death,
    disjoint external CPU/archive/restoration. Native custody remains unknown.
    """
    m,mraw=read_exact(Path(manifest_path),manifest_sha256)
    if m.get('scope')!='BUILD_ONLY' or m.get('contract')!=CONTRACT:raise ValueError('Separate build scope required')
    aid=m['assignment_id'];key=digest(aid.encode('ascii'));REGISTRY.mkdir(parents=True,exist_ok=True);plain(REGISTRY)
    claim=REGISTRY/('settlement-'+key+'.consumed.json')
    save(claim,dict(assignment_id=aid,manifest_sha256=manifest_sha256,receipt_sha256=receipt_sha256,status='CONSUMED_PENDING_UNRESOLVED'))
    report=dict(scope='BUILD_ONLY',decision='NO_GO',native_entry_enabled=False,opaque_nested_attempts='UNKNOWN',
                unresolved_costs=list(EXTERNAL),actual_native_custody_independently_verified=False)
    try:
        if current_birth()==birth(m['owner_birth']):raise ValueError('Live original owner cannot settle its own closure')
        out=ROOT/m['output_relative'];receipt_path=Path(receipt_path)
        if (m.get('schema')!='EKA-BUILD-ONLY-MANIFEST-v1' or canonical(m.get('limits'))!=canonical(LIMITS) or
            set(m.get('source',{}))!=set(SOURCES) or m.get('external_cost_categories')!=list(EXTERNAL) or
            m.get('invocations')!=invocations(m,out)):raise ValueError('Frozen build contract changed')
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
        if digest(lraw)!=r['output_inventory'].get('build-ledger.jsonl') or len(rows)!=9:raise ValueError('Exact retained ledger required')
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
            a=rows[1+i*2]['event'];o=rows[2+i*2]['event']
            if a!=dict(kind='supervised_attempt',role=role,index=i,request_sha256=digest(canonical(m['invocations'][i]))) or o['kind']!='outcome' or o['role']!=role or o['index']!=i:
                raise ValueError('Supervised attempt not durably precharged before outcome')
            v=o['result'];created.append(birth(v['birth']))
            if (v['status']!='CREATED' or birth(v['parent_birth'])!=birth(m['owner_birth']) or
                v['image_sha256']!=m['toolchain']['compiler' if role.startswith('compile') else 'linker']['sha256'] or
                type(v.get('exit_code')) is not int or v['exit_code']!=0 or
                any(v.get(n) is not True for n in ('signaled','root_member','EOF','termination_succeeded'))):raise ValueError('Incomplete attempted-start evidence')
        raw_u,raw_k,members=validate_sample(sample,m,manifest_sha256,physical,created,claim_tick)
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
        expected={'build/manifest.json':manifest_sha256,'build/receipt.json':receipt_sha256,'build/header.h':m['header']['sha256']}
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
