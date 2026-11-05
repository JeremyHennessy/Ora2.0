"""Reusable guardian DATA capsule prototype. No launch or authority API.

Only immutable release pins remain compiled. Fresh owner/ledger/deadline data
is frozen once from the existing bound transport. Matching hashes are never
human approval or independent source-to-image proof; C and Python remain HELD.
"""
import ctypes
from ctypes import wintypes as wt
import hashlib
import json
import os
from pathlib import Path
import struct
from tools import eka1_native_owner_candidate as owners
from tools.eka1_cpu_grant_transport import CpuGrantTransport,hexhash,tick,plain

MAGIC=b'EKACAP1\0';VERSION=1;FORMAT=struct.Struct('<8sIIII6Q16s'+('65s'*6));SIZE=478
HASH_FIELDS=('ledger_sha','registration_sha','assignment_sha','manifest_sha','guardian_sha','binding_sha')
INTEGER_FIELDS=('owner_pid','owner_birth','ledger_volume','ledger_extent','global_end','role_end')

def release_header(pins):
    """Only immutable release pins; never embed an owner/ledger/assignment clock."""
    import sys
    root=Path(__file__).resolve().parents[1]
    if type(pins) is not dict or set(pins)!={'python','python_sha','program','program_sha','watchdog','watchdog_sha'}:
        raise ValueError('Fixed release pin fields only')
    if Path(pins['python'])!=Path(sys.executable).resolve() or Path(pins['program'])!=root/'tools/eka1_probe_child.py':
        raise ValueError('Only fixed interpreter and CPU child source')
    values=[]
    for name,macro in [('python','EKA_PYTHON'),('program','EKA_PROGRAM'),('watchdog','EKA_OWNER_DLL')]:
        path=Path(pins[name])
        if not path.is_absolute() or len(str(path))>1024 or any(c in str(path) for c in '\r\n\0'):
            raise ValueError('Fixed absolute release file required')
        values += ['#define '+macro+' L'+json.dumps(str(path)),
                   '#define '+macro+'_SHA '+json.dumps(hexhash(pins[name+'_sha']))]
    values.append('#define EKA_RUNTIME_REGISTRY_ROOT L'+json.dumps(str(root/'runs/eka1-native-runtime-registry-v1')))
    return ('\n'.join(values)+'\n').encode('ascii')

def integer(v,low,high):
    if type(v) is not int or not low<=v<=high:raise ValueError('Exact bounded capsule integer required')
    return v
def encode(value):
    if type(value) is not dict or set(value)!=set(INTEGER_FIELDS+HASH_FIELDS+('ledger_id',)):
        raise ValueError('Fixed capsule fields; no paths/commands/limits')
    for name in INTEGER_FIELDS:integer(value[name],0 if name=='ledger_volume' else 1,2**64-1)
    integer(value['owner_pid'],1,2**32-1);integer(value['ledger_extent'],1,80*1024**2)
    if type(value['ledger_id']) is not bytes or len(value['ledger_id'])!=16:raise ValueError('Native16byte FileID required')
    if value['role_end']>value['global_end']:raise ValueError('Role cannot extend original deadline')
    raw=FORMAT.pack(MAGIC,VERSION,SIZE,3,0,*[value[n] for n in INTEGER_FIELDS],value['ledger_id'],
                    *[hexhash(value[n]).encode('ascii')+b'\0' for n in HASH_FIELDS])
    assert len(raw)==SIZE
    return raw
def decode(raw,now):
    integer(now,0,2**64-1)
    if type(raw) is not bytes or len(raw)!=SIZE:raise ValueError('Exact capsule extent required')
    values=FORMAT.unpack(raw)
    if values[:5]!=(MAGIC,VERSION,SIZE,3,0):raise ValueError('Capsule version/mode/reserved differs')
    result=dict(zip(INTEGER_FIELDS,values[5:11]));result['ledger_id']=values[11]
    for name,field in zip(HASH_FIELDS,values[12:]):
        if field[-1:]!=b'\0':raise ValueError('Canonical terminated hash required')
        result[name]=hexhash(field[:-1].decode('ascii'))
    if encode(result)!=raw:raise ValueError('Noncanonical capsule')
    if not now<result['role_end']<=min(result['global_end'],now+8000) or not now<result['global_end']<=now+120000:
        raise ValueError('Expired or extended capsule deadline')
    return result

def ledger_file_id(owner):
    """Native FILE_ID_INFO, not an assumption that Python st_ino is FILE_ID128."""
    import msvcrt
    class FileId(ctypes.Structure):_fields_=[('volume',ctypes.c_ulonglong),('identifier',ctypes.c_ubyte*16)]
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetFileInformationByHandleEx.argtypes=[wt.HANDLE,ctypes.c_int,ctypes.c_void_p,wt.DWORD]
    k.GetFileInformationByHandleEx.restype=wt.BOOL
    value=FileId()
    if not k.GetFileInformationByHandleEx(msvcrt.get_osfhandle(owner._fd),18,ctypes.byref(value),ctypes.sizeof(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    return value.volume,bytes(value.identifier)

class CapsuleReadHandle:
    """Retained verified read-only capsule/image; denies write/delete sharing."""
    def __init__(self,path,expected_sha256):
        self.handle=None;self.close_attempted=False;plain(path)
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        self.k.CreateFileW.argtypes=[wt.LPCWSTR,wt.DWORD,wt.DWORD,ctypes.c_void_p,wt.DWORD,wt.DWORD,wt.HANDLE]
        self.k.CreateFileW.restype=wt.HANDLE;self.k.CloseHandle.argtypes=[wt.HANDLE];self.k.CloseHandle.restype=wt.BOOL
        h=self.k.CreateFileW(str(path),0x80000000,1,None,3,0x00200000,None)
        if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        self.handle=h
        try:
            self.k.GetFileSizeEx.argtypes=[wt.HANDLE,ctypes.POINTER(ctypes.c_longlong)];self.k.GetFileSizeEx.restype=wt.BOOL
            self.k.ReadFile.argtypes=[wt.HANDLE,ctypes.c_void_p,wt.DWORD,ctypes.POINTER(wt.DWORD),ctypes.c_void_p];self.k.ReadFile.restype=wt.BOOL
            self.k.SetFilePointerEx.argtypes=[wt.HANDLE,ctypes.c_longlong,ctypes.c_void_p,wt.DWORD];self.k.SetFilePointerEx.restype=wt.BOOL
            size=ctypes.c_longlong()
            if not self.k.GetFileSizeEx(h,ctypes.byref(size)) or not 0<size.value<=64*1024**2:raise ValueError('Bounded retained file required')
            digest=hashlib.sha256();count=0;buffer=ctypes.create_string_buffer(65536);used=wt.DWORD()
            while True:
                if not self.k.ReadFile(h,buffer,65536,ctypes.byref(used),None):raise ctypes.WinError(ctypes.get_last_error())
                if not used.value:break
                count+=used.value
                if count>64*1024**2:raise ValueError('Retained file extent exceeded')
                digest.update(buffer.raw[:used.value])
            if count!=size.value or digest.hexdigest()!=hexhash(expected_sha256):raise ValueError('Retained file bytes differ')
            if not self.k.SetFilePointerEx(h,0,None,0):raise ctypes.WinError(ctypes.get_last_error())
        except BaseException as error:
            try:self.close()
            except BaseException as cleanup:error.add_note('Retained file closure UNKNOWN: '+repr(cleanup))
            raise
    def close(self):
        if self.handle is not None:
            if self.close_attempted:raise RuntimeError('Prior handle closure incomplete; no retry')
            self.close_attempted=True;h=self.handle
            if not self.k.CloseHandle(h):raise ctypes.WinError(ctypes.get_last_error())
            self.handle=None

def prepare(transport,owner,guardian,guardian_sha256,role_end=None):
    """Freeze one non-authorizing capsule; any failure poisons original owner."""
    if type(transport) is not CpuGrantTransport or type(owner) is not owners.NativeOwnerCandidate:
        raise TypeError('Exact existing bound transport/owner required')
    if transport.owner is not owner:raise ValueError('Alternate owner refused')
    if getattr(transport,'_capsule_consumed',False):
        error=RuntimeError('Capsule attempt consumed; no replacement');transport._poison(error);raise error
    transport._capsule_consumed=True
    path=transport.out/'3.runtime-capsule.bin';handle=None;image=None
    try:
        status=transport.preflight();assert status['native_entry_enabled'] is False
        guardian=Path(guardian)
        if guardian!=transport.out/'eka1_probe_guardian.exe':raise ValueError('Fixed image path required')
        plain(guardian);actual=hexhash(guardian_sha256)
        image=CapsuleReadHandle(guardian,actual)
        now=tick();volume,file_id=ledger_file_id(owner)
        data={'owner_pid':owner._birth[0],'owner_birth':owner._birth[1],
              'ledger_volume':volume,'ledger_id':file_id,'ledger_extent':owner._ledger._bytes,
              'global_end':transport.original_end,'role_end':min(transport.original_end,now+8000) if role_end is None else role_end,
              'ledger_sha':hashlib.sha256(owner._path.read_bytes()).hexdigest(),
              'registration_sha':owner._assignment,'assignment_sha':hashlib.sha256(transport.manifest['assignment_id'].encode('ascii')).hexdigest(),
              'manifest_sha':transport.manifest_sha,'guardian_sha':actual,
              'binding_sha':status['binding_sha256']}
        raw=encode(data);decode(raw,now)
        if data['role_end']-now<4000:raise TimeoutError('No role and closure room in original deadline')
        with path.open('xb') as stream:
            if stream.write(raw)!=len(raw):raise OSError('Partial capsule retained; no retry')
            stream.flush();os.fsync(stream.fileno())
        handle=CapsuleReadHandle(path,hashlib.sha256(raw).hexdigest())
        transport.preflight()
        decode(raw,tick())
        if data['role_end']-tick()<4000:raise TimeoutError('Capsule IO exhausted original role/closure room')
        return {'scope':'SOURCE_ONLY_IMMUTABLE_CAPSULE_NOT_AUTHORITY','path':path,'handle':handle,'image_handle':image,
                'sha256':hashlib.sha256(raw).hexdigest(),'facts':data,'native_entry_enabled':False,
                'release_source_to_binary_custody':'UNQUALIFIED','operator_grant_origin':'UNQUALIFIED'}
    except BaseException as error:
        for retained in (handle,image):
            if retained is not None:
                try:retained.close()
                except BaseException as cleanup:error.add_note('Capsule/image handle closure UNKNOWN: '+repr(cleanup))
        transport._poison(error);raise
