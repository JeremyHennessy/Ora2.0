"""Read-only preparation of existing PILOT74 admission; never a launcher.

No World imports, native execution, lock acquisition, grant issuance or automatic
admission. Trusted reviewer/registrar ancestry remains an external obligation.
This inspects the existing five gate receipts without replacing their authority.
"""
import hashlib,json,os
from pathlib import Path
GATES=('interface','custody','union_failure','source_fit','whole_source_ci')
CONFIG=dict(version='DIGITAL-PILOT74-NATIVE-qualification-v1',seeds=[3],cuts=[8192,9216,10240],horizon=10240,mode='faithful',inheritance_mode='parent_copy',fuel_mode='renewed',dose=8,software_only=True)
def encode(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def pinned(spec,cap):
    p=Path(spec['path'])
    if p.is_symlink() or not p.is_file() or p.stat().st_nlink!=1 or getattr(p.stat(),'st_file_attributes',0)&0x400:raise ValueError('Plain unshared input required')
    if type(spec['extent']) is not int or not 0<spec['extent']<=cap:raise ValueError('Bounded exact input required')
    with p.open('rb') as f:raw=f.read(cap+1)
    if len(raw)!=spec['extent'] or digest(raw)!=spec['sha256']:raise ValueError('Pinned input changed')
    return raw
def inspect(packet):
    if packet['configuration']!=CONFIG:raise ValueError('Unchanged finite configuration required')
    if not packet['preserve_closed_results'] or packet['world_launches']!=0:raise ValueError('Preparation only;preserve closed results')
    pins=packet['source_files'];source_sha=digest(encode({n:s['sha256'] for n,s in pins.items()}));config_sha=digest(encode(CONFIG))
    if packet['source_sha256']!=source_sha:raise ValueError('Source manifest differs')
    for name,spec in pins.items():
        if not name.startswith('experiments/') or '..' in name or '\\' in name:raise ValueError('Invalid source member')
        pinned(spec,1024**2)
    missing=[];present=[]
    for kind in GATES:
        spec=packet['reviews'].get(kind)
        if not spec:missing.append(kind);continue
        r=json.loads(pinned(spec,1024**2))
        if not (r['schema']=='PILOT74-EXTERNAL-GATE-REVIEW-v2' and r['kind']==kind and r['revision']==packet['revision'] and r['source_sha256']==source_sha and r['configuration_sha256']==config_sha and r['scope']=='new_pilot74_whole_source_only' and r['verdict']=='PASS'):
            raise ValueError('Wrong gate scope/source/configuration')
        if kind=='whole_source_ci':
            if r['head_sha']!=packet['revision'] or r['conclusion']!='success' or r['old_suites_rerun'] is not False:raise ValueError('Exact scoped CI required')
        else:
            if not r['native_records'] or r['archive_restore_exact'] is not True:raise ValueError('Native/archive evidence required')
            for n in r['native_records']:
                value=json.loads(pinned(n,1024**2))
                if value['exit_code']!=0 or value['timed_out'] or value['output_truncated'] or not value['post_close_processes_exited'] or value['usage']['active_before_close']!=0:raise ValueError('Failed native evidence')
        present.append(kind)
    return dict(preparation_checked=True,source_members=len(pins),source_bytes=sum(s['extent'] for s in pins.values()),gate_receipts_present=present,gate_receipts_missing=missing,
        qualification_request_ready=not missing,execution_authorized=False,worlds_launched=0,
        mandatory_external_steps=['Independent reviewer ancestry for exact pinned gate receipts','Actual original-owner registration and expiring grant in existing custody path','Whole finite recovery qualification before supervised continuation attachment'],
        limitation='Receipt shape and hashes cannot authenticate reviewer execution ancestry;this is not an admission or replacement launcher.')
