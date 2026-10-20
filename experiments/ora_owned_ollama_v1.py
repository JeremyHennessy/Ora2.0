"""Owned CPU-only Ollama server/runner Job, separate from the user's shared server.

Only installed binaries and existing local models. No pull, cloud or boot setup.
The OS enforces RAM, CPU hard rate, aggregate CPU and process limits on the tree.
GPU avoidance is backend configuration plus observed zero VRAM, not an OS VRAM cap.
"""
import ctypes
from ctypes import wintypes as wt
import hashlib
import http.client
import json
import msvcrt
import os
from pathlib import Path
import socket
import threading
import time
from experiments.ora_native_slice_v1 import run_slice,Limits

PORT=11435
MEMORY=24*1024**3
CPU_RATE=2000


def retain_result(path,result):
    output=result.pop('output')
    raw=output.encode('utf8')[:1024**2]
    temporary=path/'server.log.next'; temporary.write_bytes(raw); temporary.replace(path/'server.log')
    result['output_sha256']=hashlib.sha256(raw).hexdigest()
    result['log_bytes']=len(raw)
    temporary=path/'native-result.next'; temporary.write_text(json.dumps(result,indent=2),encoding='utf8')
    temporary.replace(path/'native-result.json')


def listener_pid(port=PORT):
    class ROW(ctypes.Structure):
        _fields_=[('state',wt.DWORD),('local_addr',wt.DWORD),('local_port',wt.DWORD),
                  ('remote_addr',wt.DWORD),('remote_port',wt.DWORD),('pid',wt.DWORD)]
    library=ctypes.WinDLL('iphlpapi',use_last_error=True)
    fn=library.GetExtendedTcpTable
    fn.argtypes=[ctypes.c_void_p,ctypes.POINTER(wt.DWORD),wt.BOOL,wt.ULONG,ctypes.c_int,wt.ULONG]
    fn.restype=wt.DWORD
    size=wt.DWORD(); code=fn(None,ctypes.byref(size),False,2,3,0)
    if code not in (0,122) or size.value>4*1024**2: raise OSError('Cannot bound listener inventory')
    buffer=ctypes.create_string_buffer(size.value)
    code=fn(buffer,ctypes.byref(size),False,2,3,0)
    if code: raise OSError('Cannot authenticate loopback listener: '+str(code))
    count=wt.DWORD.from_buffer(buffer).value
    if 4+count*ctypes.sizeof(ROW)>size.value: raise OSError('Invalid native TCP inventory')
    for i in range(count):
        row=ROW.from_buffer(buffer,4+i*ctypes.sizeof(ROW))
        if socket.ntohs(row.local_port&65535)==port:
            if row.local_addr!=int.from_bytes(socket.inet_aton('127.0.0.1'),'little'):
                raise RuntimeError('Owned port exposed beyond literal loopback')
            return row.pid
    return None


def request(path,body=None,timeout=3):
    connection=http.client.HTTPConnection('127.0.0.1',PORT,timeout=timeout)
    try:
        connection.request('GET' if body is None else 'POST',path,
            None if body is None else json.dumps(body),{'Content-Type':'application/json'})
        response=connection.getresponse(); raw=response.read(65537)
        if response.status!=200 or len(raw)>65536: raise ValueError('Owned server response refused/oversized')
        return json.loads(raw)
    finally: connection.close()


def verify_owner(directory):
    marker=Path(directory)/'owned-ollama.json'
    with marker.open('rb') as stream: raw=stream.read(16385)
    if len(raw)>16384 or marker.is_symlink() or marker.stat().st_nlink!=1:
        raise ValueError('Invalid owned server marker')
    value=json.loads(raw)
    if value['port']!=PORT or value['policy']['memory_bytes']!=MEMORY or value['policy']['cpu_rate']!=CPU_RATE:
        raise ValueError('Wrong model server containment policy')
    if listener_pid()!=value['pid']: raise RuntimeError('Owned model listener identity changed; no fallback')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD]; k.OpenProcess.restype=wt.HANDLE
    k.GetProcessTimes.argtypes=[wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
    k.WaitForSingleObject.argtypes=[wt.HANDLE,wt.DWORD]; k.CloseHandle.argtypes=[wt.HANDLE]
    handle=k.OpenProcess(0x1000|0x100000,False,value['pid'])
    if not handle: raise RuntimeError('Owned model server unavailable')
    try:
        times=[ctypes.c_ulonglong() for _ in range(4)]
        if not k.GetProcessTimes(handle,*[ctypes.byref(v) for v in times]) or k.WaitForSingleObject(handle,0)!=258:
            raise RuntimeError('Owned model server is not live')
        if str(times[0].value)!=value['creation_filetime_decimal']: raise RuntimeError('Owned model server birth mismatch')
    finally: k.CloseHandle(handle)
    return value


class OwnedOllama:
    def __init__(self,directory,epoch,seconds=300):
        if type(epoch) is not int or not 0<=epoch<=3 or not 5<=seconds<=900:
            raise ValueError('Finite owned-server epoch required')
        self.root=Path(directory); self.path=self.root/f'model-server-{epoch}'
        self.seconds=seconds; self.result=None; self.error=None; self.start=None
        self.ready=threading.Event(); self.samples=dict(count=0,peak_active=0,observed_pids=[])
        self.lock=None; self.thread=None

    def __enter__(self):
        self.root.mkdir(parents=True,exist_ok=True)
        lock_path=self.root/'model-server.lock'
        if lock_path.exists() and (lock_path.is_symlink() or lock_path.stat().st_nlink!=1): raise ValueError('Invalid model lock')
        self.lock=lock_path.open('a+b'); self.lock.seek(0)
        try:
            msvcrt.locking(self.lock.fileno(),msvcrt.LK_NBLCK,1)
            if listener_pid() is not None: raise RuntimeError('Owned model port already in use; refuse takeover')
            self.path.mkdir(exist_ok=False)
            executable=Path(os.environ['LOCALAPPDATA'])/'Programs/Ollama/ollama.exe'
            models=Path('D:/OraLab/tools/ollama-models')
            if not executable.is_file() or not models.is_dir(): raise ValueError('Installed binary and model cache required')
            self.policy=dict(port=PORT,memory_bytes=MEMORY,cpu_rate=CPU_RATE,cpu_seconds=900,
                processes=8,wall_seconds=self.seconds,gpu_policy='CPU_ONLY_BACKENDS_DISABLED_VERIFY_ZERO_VRAM',
                binary_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
            environment=dict(OLLAMA_HOST=f'127.0.0.1:{PORT}',OLLAMA_MODELS=str(models),
                OLLAMA_NO_CLOUD='1',OLLAMA_NUM_PARALLEL='1',OLLAMA_MAX_LOADED_MODELS='1',
                OLLAMA_MAX_QUEUE='2',OLLAMA_CONTEXT_LENGTH='2048',OLLAMA_KEEP_ALIVE='30s',
                OLLAMA_VULKAN='0',CUDA_VISIBLE_DEVICES='-1',GGML_VK_VISIBLE_DEVICES='-1',
                ROCR_VISIBLE_DEVICES='-1',HIP_VISIBLE_DEVICES='-1')
            (self.path/'policy.json').write_text(json.dumps(self.policy,indent=2))
            def on_start(value):
                self.start=value
                (self.path/'suspended-start.json').write_text(json.dumps(value,indent=2))
                self.ready.set()
            def on_sample(value):
                self.samples['count']+=1
                self.samples['peak_active']=max(self.samples['peak_active'],value['usage']['active_before_close'])
                self.samples['observed_pids']=sorted(set(self.samples['observed_pids'])|set(value['pids']))[:128]
                self.samples['latest_usage']=value['usage']
            def worker():
                try:
                    self.result=run_slice(lambda *unused:[str(executable),'serve'],self.path,
                        Limits(memory_bytes=MEMORY,cpu_seconds=900,processes=8,wall_seconds=self.seconds),
                        stop_path=self.path/'STOP',environment=environment,cpu_rate=CPU_RATE,
                        on_start=on_start,on_sample=on_sample)
                    retain_result(self.path,self.result)
                except BaseException as error:
                    self.error=type(error).__name__+': '+str(error)
                    (self.path/'error.json').write_text(json.dumps(dict(error=self.error)))
                finally: self.ready.set()
            self.thread=threading.Thread(target=worker,daemon=True); self.thread.start()
            if not self.ready.wait(5) or self.start is None: raise RuntimeError('Owned server did not start suspended: '+str(self.error))
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                if not self.thread.is_alive(): raise RuntimeError('Owned server exited at startup: '+str(self.error or self.result))
                if listener_pid()==self.start['pid']:
                    try:
                        request('/api/version')
                        marker=dict(port=PORT,pid=self.start['pid'],creation_filetime_decimal=self.start['creation_filetime_decimal'],policy=self.policy)
                        temporary=self.root/'owned-ollama.next'; temporary.write_text(json.dumps(marker))
                        temporary.replace(self.root/'owned-ollama.json')
                        verify_owner(self.root)
                        return self
                    except (OSError,http.client.HTTPException): pass
                time.sleep(.1)
            raise TimeoutError('Owned server readiness deadline')
        except BaseException:
            self.close(); raise

    def prepare(self):
        verify_owner(self.root)
        value=request('/api/generate',dict(model='gpt-oss:20b',prompt='',stream=False,keep_alive='30s',
            options=dict(num_ctx=2048,num_predict=1,num_gpu=0,num_thread=2)),timeout=120)
        if value.get('done') is not True: raise RuntimeError('Owned model preparation incomplete')
        observed=self.check_model()
        if len(observed['models'])!=1: raise RuntimeError('Owned model did not remain prepared')
        return observed

    def check_model(self):
        verify_owner(self.root)
        value=request('/api/ps')
        if len(value['models'])>1 or any(m.get('size_vram')!=0 for m in value['models']):
            (self.path/'STOP').touch()
            raise RuntimeError('Owned server violated CPU-only/one-model policy')
        (self.path/'model-observation.json').write_text(json.dumps(value,indent=2))
        return value

    def close(self):
        try:
            if self.thread is not None:
                (self.path/'STOP').touch(); self.thread.join(8)
                if self.thread.is_alive(): raise RuntimeError('Owned model tree closure unknown')
                (self.path/'samples.json').write_text(json.dumps(self.samples,indent=2))
                if self.error: raise RuntimeError(self.error)
                if self.result is None or not self.result['post_close_processes_exited']:
                    raise RuntimeError('Owned model tree did not close')
                if self.result['output_limit_exceeded'] or self.result['descendant_leak'] or self.result['reason'] not in ('operator-stop','wall-limit'):
                    raise RuntimeError('Owned model epoch failed; tree closed but renewal requires failure handling')
        finally:
            if self.lock is not None: self.lock.close(); self.lock=None

    def __exit__(self,*unused): self.close()
