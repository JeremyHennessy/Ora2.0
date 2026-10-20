"""VM-free stand-in W for real native G protocol qualification only.

Mapped into a dedicated fixture source root. NEVER a production finite worker.
All 26 roles run scripted children; no model, VM, scientific sample or policy.
"""
import ctypes
from ctypes import wintypes as wt
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import shutil
import struct
import sys
import zipfile

MIB=1024**2
ROLES=['original/prepared','original/generate','original/audit8192','original/resume8192',
       'original/audit9216','original/resume9216','original/audit10240','original/resume10240',
       'restored/prepared','restored/generate','restored/audit8192','restored/resume8192',
       'restored/audit9216','restored/resume9216','restored/audit10240','restored/resume10240',
       'crash/partial','recover/partial','crash/orphan','recover/orphan','crash/committed',
       'recover/committed','crash/normal','recover/normal','normal-sequence','closed-projection-publication-audit']


def enc(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(v): return hashlib.sha256(v).hexdigest()
def pin(p):
    raw=p.read_bytes()
    return dict(path=p.as_posix(),extent=len(raw),sha256=sha(raw))
def read(spec):
    raw=Path(spec['path']).read_bytes()
    assert len(raw)==spec['extent'] and sha(raw)==spec['sha256']
    return raw
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f: f.write(enc(v))
    return pin(p)


def identity(p):
    class ID(ctypes.Structure):
        _fields_=[('volume',ctypes.c_ulonglong),('identifier',ctypes.c_ubyte*16)]
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetFileInformationByHandleEx.argtypes=[wt.HANDLE,ctypes.c_int,ctypes.c_void_p,wt.DWORD]
    with p.open('rb') as f:
        value=ID()
        if not k.GetFileInformationByHandleEx(msvcrt.get_osfhandle(f.fileno()),18,ctypes.byref(value),ctypes.sizeof(value)):
            raise ctypes.WinError(ctypes.get_last_error())
    return format(value.volume,'016x')+':'+bytes(value.identifier).hex()


def main():
    raw=read(dict(path=sys.argv[1],extent=int(sys.argv[2]),sha256=sys.argv[3]))
    r=json.loads(raw); root=Path(r['root']); root.mkdir(exist_ok=False)
    reader=os.fdopen(msvcrt.open_osfhandle(int(os.environ.pop('PILOT74_GUARDIAN_READ')),os.O_RDONLY|os.O_BINARY),'rb',buffering=0)
    writer=os.fdopen(msvcrt.open_osfhandle(int(os.environ.pop('PILOT74_GUARDIAN_WRITE')),os.O_WRONLY|os.O_BINARY),'wb',buffering=0)
    def exact(n):
        answer=b''
        while len(answer)<n:
            part=reader.read(n-len(answer))
            if not part: raise OSError('Native protocol EOF')
            answer+=part
        return answer
    def exchange(kind,**fields):
        body=enc(dict(type=kind,source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],**fields))
        assert len(body)<=65536
        packet=struct.pack('<I',len(body))+body
        assert writer.write(packet)==len(packet)
        n=struct.unpack('<I',exact(4))[0]; assert 0<n<=65536
        answer=json.loads(exact(n))
        if answer['schema']=='PILOT74-GUARDIAN-FIRST-FAILURE-v1': raise RuntimeError(answer)
        return answer
    assert exchange('HELLO')['schema']=='PILOT74-GUARDIAN-HELLO-v1'
    slots=[]
    for i in range(80):
        if i<78:
            name=ROLES[i//3]
            relative=(f'raw/native/{name}.start.json',f'raw/native/{name}.json',f'raw/stdout/{name}.bin')[i%3]
            limit=(65536,960*1024,MIB)[i%3]
        else:
            relative=('failure/native-first-output.bin','failure/native-first-failure.json')[i-78]
            limit=(24*MIB,8*MIB)[i-78]
        path=root/relative; path.parent.mkdir(parents=True,exist_ok=True); path.touch(exist_ok=False)
        slots.append(dict(path=path.as_posix(),limit=limit,win32_id=identity(path)))
    for variant in ('original','restored'):
        destination=root/'raw/metadata/source'/variant
        for name,digest in r['source_files'].items():
            source=Path(r['source_root'])/name
            assert sha(source.read_bytes())==digest
            p=destination/name; p.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(source,p)
    preflight=save(root/'raw/metadata/guardian-preflight.json',dict(schema='PILOT74-GUARDIAN-PREFLIGHT-v1',
        source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],native_slots=slots,
        roles=[dict(role=n,request_bound=4096,grant_bound=16384,frame_bound=65536,native_record_bound=960*1024) for n in ROLES]))
    assert exchange('READY',slots=slots,preflight=preflight)['schema']=='PILOT74-GUARDIAN-READY-v1'
    observations=[]
    for i,name in enumerate(ROLES):
        request=save(root/f'raw/requests/{name}.json',dict(source_sha256=r['source_sha256'],
            configuration_sha256=r['configuration_sha256'],ordinal=i,fixture=True))
        cwd=root/'raw/metadata/source'/('restored' if 8<=i<16 else 'original')
        extra=16<=i<=24
        target='digital_pilot74_source_ready_v2' if i in (0,8) else 'digital_pilot74_closed_audit_child_v2' if i==25 else 'digital_pilot74_journal_observed_child_v2' if extra else 'digital_pilot74_child'
        command=[r['python']['path'],'-B',(cwd/'experiments/digital_pilot74_entrypoint_v2.py').as_posix(),target,
                 request['path'],str(request['extent']),request['sha256']]+(['fixture'] if extra else [])
        grant=dict(version='PILOT74-NATIVE-CAPTURE-GRANT-v2',root=root.as_posix(),
            source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],role=name,
            operator_lock=r['operator_lock'],raw=dict(path=slots[i*3+2]['path'],limit=MIB),
            overflow=dict(path=slots[78]['path'],limit=24*MIB),command_sha256=sha(enc(command)))
        result=exchange('ROLE_REQUEST',ordinal=i,role=name,command=command,cwd=cwd.as_posix(),
            request=request,capture_grant=grant,capture_seal=sha(enc(grant)))
        assert result['ordinal']==i and result['role']==name
        native=json.loads(read(result['native'])); start=json.loads(read(native['start']))
        assert start['root_member'] and start['child_member']
        assert native['exit_code']==(78 if i in (16,18,20) else 0)
        assert native['active_before_close']==0 and native['started_processes']==1 and native['post_close_processes_exited']
        cap=native['stdout_capture']; output=read(cap['raw']); spill=read(cap['overflow'])
        assert cap['capture_complete'] and cap['eof'] and not cap['errors'] and not cap['stdout_limit_exceeded']
        assert len(output)+len(spill)==cap['received_bytes']==cap['retained_bytes']
        assert json.loads(output)['ordinal']==i
        observations.append(dict(role=name,pid=native['pid'],exit_code=native['exit_code'],native=result['native']))
    save(root/'fixture-observations.json',dict(schema='NATIVE-GUARDIAN-VM-FREE-FIXTURE-v1',roles=observations,worlds=0,production_admission=False))
    assert exchange('ARCHIVE_BARRIER')['schema']=='PILOT74-GUARDIAN-BARRIER-v1'
    members={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
    archive=root/'archive/complete.zip'; archive.parent.mkdir()
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_STORED) as z:
        for name in sorted(members): z.write(root/name,name)
    restored=root/'fixture-restore'; restored.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert sorted(z.namelist())==sorted(members)
        z.extractall(restored)
    assert {p.relative_to(restored).as_posix():sha(p.read_bytes()) for p in restored.rglob('*') if p.is_file()}==members
    proof=dict(schema='PILOT74-AVAILABLE-EVIDENCE-RESTORE-v2',evidence_complete=True,
               available_files_exactly_restored=True,archive=pin(archive))
    assert exchange('FINISH',complete=True,archive=proof)['schema']=='PILOT74-GUARDIAN-FINISH-v1'
    writer.close(); reader.close()
    print(json.dumps(dict(fixture_roles=26,archive_files=len(members),worlds=0,production_admission=False)))


if __name__=='__main__': main()
