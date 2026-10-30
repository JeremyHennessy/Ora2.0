"""Offline external-settlement protocol. Never a launcher or native authority.

Validate disjoint closed-scope claims and exact archive bytes. A receipt writer
cannot certify its own final CPU or final write. Its tail always remains a
separate unresolved debt here, even when a future settlement scope is reserved.
Hash/metadata consistency is not independently observed native custody.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import zipfile
from tools.eka1_cpu_grant_transport import read_exact,plain,hexhash,save
from tools.eka1_native_owner_candidate import current_birth

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'runs/eka1-external-settlement-registry-v1'
MAX_FILES=128
MAX_BYTES=64*1024**2
PHASES=('archive_create','restore','hash','completion','watchdog_shutdown','process_closure')
TAILS={'archive-verification.json','completion.json','watchdog-stop.json','final-closure.json'}

class SettlementFailure(RuntimeError):
    def __init__(self,message,observation):
        super().__init__(message);self.observation=observation

def digest(raw):return hashlib.sha256(raw).hexdigest()
def integer(value):
    if type(value) is not int or not 0<=value<2**63:raise ValueError('Exact nonnegative integer required')
    return value
def birth(value):
    if (type(value) is not list or len(value)!=2 or any(type(x) is not int or x<=0 for x in value) or
        value[0]>=2**32 or value[1]>=2**64):
        raise ValueError('Exact process PID/creation identity required')
    return tuple(value)
def safe_name(value):
    if (type(value) is not str or re.fullmatch(r'[A-Za-z0-9_./-]+',value) is None or
        value.startswith('/') or any(x in ('','.','..') or x.endswith('.') for x in value.split('/'))):
        raise ValueError('Canonical relative evidence name required')
    return value
def file_digest(path):
    plain(path)
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno());h=hashlib.sha256();count=0
        if before.st_size>MAX_BYTES:raise ValueError('Evidence extent exceeded')
        for block in iter(lambda:stream.read(65536),b''):
            count+=len(block)
            if count>MAX_BYTES:raise ValueError('Evidence grew beyond bound')
            h.update(block)
        after=os.fstat(stream.fileno());named=path.stat();plain(path)
        if ((before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino) or
            (after.st_dev,after.st_ino)!=(named.st_dev,named.st_ino) or
            before.st_size!=count or after.st_size!=count or before.st_mtime_ns!=after.st_mtime_ns):
            raise ValueError('Evidence physical custody changed')
    return h.hexdigest(),count

def archive_observation(root,files,receipt_name,caps):
    if (type(caps) is not dict or set(caps)!={'payload_files','payload_bytes','stored_bytes','retained_files','retained_bytes'} or
        any(type(caps[k]) is not int or not 0<caps[k]<= (MAX_FILES if k.endswith('files') else MAX_BYTES) for k in caps)):
        raise ValueError('Explicit bounded payload AND total-retained caps required')
    if type(files) is not dict:raise ValueError('Exact retained inventory required')
    if receipt_name in files:raise ValueError('Receipt cannot hash or certify its own final write')
    observed={};extent=0;all_names=[]
    for path in sorted(root.rglob('*')):
        plain(path)
        if not path.is_file():continue
        name=safe_name(path.relative_to(root).as_posix());all_names.append(name)
        extent+=path.stat().st_size
        if len(all_names)>caps['retained_files'] or extent>caps['retained_bytes']:
            raise ValueError('Total retained extent includes ZIP, restored copies, tails and inputs')
        if name!=receipt_name:observed[name]=file_digest(path)[0]
    if observed!=files:raise ValueError('Retained inventory differs or omits a post-archive tail')
    if not {('tails/'+n) for n in TAILS}<=set(observed):raise ValueError('Completion/watchdog/closure/archive-verification tails required')
    payload={n[len('payload/'):]:h for n,h in observed.items() if n.startswith('payload/')}
    restored={n[len('restored/'):]:h for n,h in observed.items() if n.startswith('restored/')}
    if not payload or payload!=restored:raise ValueError('Exact DATA restoration required; no restored code execution')
    if len(payload)>caps['payload_files'] or sum((root/'payload'/n).stat().st_size for n in payload)>caps['payload_bytes']:
        raise ValueError('Payload cap exceeded')
    target=root/'evidence.zip'
    if target.stat().st_size>caps['stored_bytes']:raise ValueError('Stored ZIP cap exceeded')
    with zipfile.ZipFile(target) as archive:
        entries=archive.infolist();names=[safe_name(x.filename) for x in entries]
        if len(names)!=len(set(x.casefold() for x in names)) or set(names)!=set(payload):
            raise ValueError('ZIP duplicate/extra/missing entry')
        if sum(x.file_size for x in entries)>caps['payload_bytes']:raise ValueError('Expanded ZIP cap exceeded')
        for item in entries:
            if stat.S_IFMT(item.external_attr>>16) not in (0,stat.S_IFREG):raise ValueError('ZIP must contain regular DATA files only')
            count=0;h=hashlib.sha256()
            with archive.open(item) as stream:
                for block in iter(lambda:stream.read(65536),b''):
                    count+=len(block)
                    if count>item.file_size or count>caps['payload_bytes']:raise ValueError('Expanded data exceeded declaration')
                    h.update(block)
            if count!=item.file_size or h.hexdigest()!=payload[item.filename]:raise ValueError('ZIP payload bytes differ')
    return {'payload_files':len(payload),'payload_bytes':sum((root/'payload'/n).stat().st_size for n in payload),
            'stored_bytes':target.stat().st_size,'total_retained_files':len(all_names),'total_retained_bytes':extent,
            'retained_extent_scope':'COVERED_EVIDENCE_DIRECTORY_ONLY_EXCLUDES_LIVE_VERIFIER_REGISTRY_TAIL',
            'settlement_input_excluded_from_self_hash_but_counted':receipt_name,'restored_code_executed':False}

def settle(plan_path,plan_sha256,receipt_path,receipt_sha256):
    """One assignment claim. Failures retain partial observations, never refund."""
    plan_path=Path(plan_path);receipt_path=Path(receipt_path)
    plan,plan_raw=read_exact(plan_path,plan_sha256)
    if (plan_path.name!='settlement-plan.json' or receipt_path!=plan_path.parent/'settlement-input.json' or
        type(plan) is not dict or plan.get('schema')!='EKA-EXTERNAL-SETTLEMENT-PLAN-v1'):
        raise ValueError('Fixed settlement DATA plan/input locations required')
    assignment=hexhash(plan['assignment_sha256']);verifier=birth(list(current_birth()))
    for path in REGISTRY.parents:
        if path.exists():plain(path)
    REGISTRY.mkdir(parents=True,exist_ok=True);plain(REGISTRY)
    prefix=REGISTRY/assignment
    report={'schema':'EKA-EXTERNAL-SETTLEMENT-OBSERVATION-v1','assignment_sha256':assignment,
            'plan_sha256':plan_sha256,'receipt_sha256':receipt_sha256,'verifier_birth':list(verifier),
            'decision':'NO_GO','native_entry_enabled':False,'scope':'SOURCE_CONSISTENCY_ONLY_NOT_NATIVE_CUSTODY',
            'debits':[],'recorded_complete_covered_ticks':None,'known_component_ticks_lower_bound':0,
            'verifier_writer_tail':'UNSETTLED','unresolved_costs':['live_verifier_final_write_and_lifetime'],
            'verifier_registry_extent':'UNSETTLED_OUTSIDE_COVERED_ARCHIVE_TOTAL',
            'no_retry':True,'no_refund':True,'historical_debt_forgiven':False}
    save(prefix.with_suffix('.consumed.json'),dict(report,status='CONSUMED_PENDING_UNRESOLVED'))
    try:
        receipt,raw=read_exact(receipt_path,receipt_sha256)
        if (type(receipt) is not dict or receipt.get('schema')!='EKA-EXTERNAL-SETTLEMENT-INPUT-v1' or
            receipt.get('assignment_sha256')!=assignment or receipt.get('plan_sha256')!=plan_sha256):
            raise ValueError('Exact prospective assignment/plan binding required')
        owner=birth(plan['owner_birth']);hexhash(plan['immutable_build_package_sha256'])
        scopes=plan['scopes'];samples=receipt['samples'];phases=plan['phases'];events=receipt['events']
        if not isinstance(scopes,list) or not 1<=len(scopes)<=16 or not isinstance(samples,list) or len(samples)!=len(scopes):
            raise ValueError('Exact bounded scope/sample set required')
        members=set();identities=set();scope_map={}
        for scope in scopes:
            sid=hexhash(scope['scope_id']);identity=hexhash(scope['root_identity'])
            group=[birth(x) for x in scope['members']]
            if (sid in scope_map or identity in identities or not group or len(set(group))!=len(group) or
                members.intersection(group) or verifier in group or
                scope['kind'] not in ('PROCESS_LIFETIME','JOB_LIFETIME') or
                (scope['kind']=='PROCESS_LIFETIME' and len(group)!=1)):
                raise ValueError('Duplicate/nested/self-measured root scope refused')
            members.update(group);identities.add(identity);scope_map[sid]=(scope,set(group))
        if owner not in members:raise ValueError('Original owner lifetime missing')
        owner_scope=next(sid for sid,unused in scope_map.items() if owner in scope_map[sid][1])
        if not isinstance(phases,list) or [x['phase'] for x in phases]!=list(PHASES):
            raise ValueError('Exact archive/restore/hash/completion/watchdog/closure dependency order required')
        if phases[-1]['phase']!='process_closure' or birth(phases[-1]['actor_birth'])==owner:
            raise ValueError('External process closure must be the final covered phase')
        if phases[-1].get('closed_scope_id')!=owner_scope or birth(phases[-1].get('closed_birth'))!=owner:
            raise ValueError('Final closure must bind the original owner scope/birth')
        if not isinstance(events,list) or len(events)!=len(phases):raise ValueError('Exact phase event chain required')
        previous='0'*64;phase_end={};last_tick=0
        for index,(declared,event) in enumerate(zip(phases,events)):
            sid=declared['scope_id'];actor=birth(declared['actor_birth']);ended=integer(event['ended_tick'])
            if (sid not in scope_map or actor not in scope_map[sid][1] or
                event.get('sequence')!=index or type(event.get('sequence')) is not int or
                event.get('previous_sha256')!=previous or event.get('phase')!=declared['phase'] or
                event.get('actor_birth')!=declared['actor_birth'] or event.get('scope_id')!=sid or ended<last_tick):
                raise ValueError('Changed phase actor/order/hash/cutoff')
            if declared['phase']=='process_closure' and (event.get('closed_scope_id')!=owner_scope or
                birth(event.get('closed_birth'))!=owner):
                raise ValueError('Final closure event changed original owner scope/birth')
            previous=digest(json.dumps(event,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
            phase_end[sid]=max(phase_end.get(sid,0),ended);last_tick=ended
        if receipt.get('event_tip_sha256')!=previous:raise ValueError('Final evidence chain differs')
        seen=set();complete=True;total=0;sample_map={}
        for sample in samples:
            sid=sample['scope_id']
            if sid in seen or sid not in scope_map:raise ValueError('Duplicate or alternate debit')
            seen.add(sid);scope,group=scope_map[sid]
            measurer=birth(sample['measurer_birth'])
            if measurer not in members and measurer!=verifier:
                raise ValueError('Undeclared measuring actor costs cannot disappear')
            closed=[birth(x) for x in sample['closed_births']]
            if (sample.get('root_identity')!=scope['root_identity'] or sample.get('kind')!=scope['kind'] or
                measurer in group or sample.get('signaled') is not True or
                type(sample.get('active')) is not int or sample['active']!=0 or
                len(closed)!=len(group) or set(closed)!=group or sample.get('EOF') is not True or
                integer(sample['signaled_tick'])<phase_end.get(sid,0) or
                integer(sample['measured_tick'])<sample['signaled_tick']):
                raise ValueError('External final closed-scope custody/cutoff missing')
            sample_map[sid]=sample
            u=sample.get('USER_ticks');k=sample.get('KERNEL_ticks')
            if u is not None:integer(u);report['known_component_ticks_lower_bound']+=u
            if k is not None:integer(k);report['known_component_ticks_lower_bound']+=k
            value=None if u is None or k is None else u+k
            if scope['kind']=='JOB_LIFETIME':
                for name in ('period_USER_ticks','period_KERNEL_ticks'):
                    if sample.get(name) is not None:integer(sample[name])
                if (sample.get('initial_USER_ticks')!=0 or type(sample.get('initial_USER_ticks')) is not int or
                    sample.get('initial_KERNEL_ticks')!=0 or type(sample.get('initial_KERNEL_ticks')) is not int or
                    sample.get('period_USER_ticks')!=u or sample.get('period_KERNEL_ticks')!=k):
                    raise ValueError('Job epoch/reset or initial CPU inconsistent')
            report['debits'].append({'scope_id':sid,'recorded_USER_ticks':u,'recorded_KERNEL_ticks':k,
                                    'recorded_total_ticks':value,'private_subset_added_again':False})
            if value is None:complete=False;report['unresolved_costs'].append(sid)
            else:total+=value
        # A covered measurer must still have been alive at its observation. A
        # cycle would require each process to outlive its own already-signaled
        # closure, so reject it rather than self-certifying a final writer.
        for sample in sample_map.values():
            measurer=birth(sample['measurer_birth'])
            for sid,unused in scope_map.items():
                if measurer in scope_map[sid][1] and sample_map[sid]['signaled_tick']<=sample['measured_tick']:
                    raise ValueError('Circular or posthumous final measurement')
        if events[-1]['ended_tick']<sample_map[owner_scope]['signaled_tick']:
            raise ValueError('Final closure cutoff precedes original owner signaled observation')
        report['recorded_complete_covered_ticks']=total if complete else None
        report['archive']=archive_observation(plan_path.parent,receipt['files'],receipt_path.name,plan['archive_caps'])
        tail=plan.get('verifier_tail_scope')
        if tail is not None:
            hexhash(tail)
            if tail in scope_map:raise ValueError('Current writer tail cannot already be a closed scope')
            report['verifier_writer_tail']='PENDING_SEPARATE_EXTERNAL_SCOPE'
            report['reserved_verifier_tail_scope']=tail
        report['covered_measurement_fields_complete']=complete
        report['status']=('SOURCE_CONSISTENT_COVERED_SCOPES_FINAL_WRITER_UNSETTLED' if complete else
                          'SOURCE_CONSISTENT_PARTIAL_DEBT_FINAL_WRITER_UNSETTLED')
        report['actual_native_measurements_independently_verified']=False
        report['immutable_build_package_sha256']=plan['immutable_build_package_sha256']
        save(prefix.with_suffix('.settlement.json'),report)
        return report
    except BaseException as exc:
        report.update(status='INCOMPLETE_UNRESOLVED_DEBT',first_failure=type(exc).__name__+': '+str(exc))
        try:save(prefix.with_suffix('.failure.json'),report)
        except BaseException as write_error:exc.add_note('Settlement failure evidence incomplete: '+repr(write_error))
        raise SettlementFailure(str(exc),report) from exc
