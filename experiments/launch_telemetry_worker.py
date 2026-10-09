"""LAUNCH-01 fixed finite child; scheduling holds do not alter world physics."""
import json
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import sys
import time
from experiments import heartbeat_template as world


def write(path,value):path.write_text(json.dumps(value)+'\n',encoding='utf-8')


def main(workspace):
    workspace=Path(workspace);request=json.loads((workspace/'request.json').read_bytes())
    if set(request)!={'world_id','revision','resume','resource','binding_path'} or type(request['resume']) is not bool or type(request['resource']) is not bool:raise ValueError('Fixed finite request')
    binding=Path(request['binding_path']).absolute()
    if binding.parent!=workspace.absolute().parent/'operator-bindings':raise ValueError('Fixed parent-only fixture binding')
    try:binding.write_text('forged-child-binding',encoding='utf-8')
    except PermissionError as error:
        kernel=c.WinDLL('kernel32',use_last_error=True)
        kernel.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];kernel.CreateFileW.restype=w.HANDLE
        kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle.restype=w.BOOL
        handle=kernel.CreateFileW(str(binding),0x40000000,0,None,3,0x80,None);native_error=c.get_last_error()
        if handle!=c.c_void_p(-1).value:
            kernel.CloseHandle(handle);raise RuntimeError('Native child can open launch authority for writing')
        write(workspace/'binding-probe.json',dict(denied=True,error='PermissionError',python_errno=error.errno,python_winerror=error.winerror,winerror=native_error,path=str(binding)))
    else:write(workspace/'binding-probe.json',dict(denied=False,path=str(binding)));raise RuntimeError('Child can overwrite launch authority')
    ticks=(5,6,7) if request['resume'] else (1,2,5);original=world.next_state
    def advance(old):
        tick=old['simulation_tick']
        if tick in ticks:
            write(workspace/'hold.pending',dict(tick=tick));(workspace/'hold.pending').replace(workspace/'hold.json')
            started=time.monotonic()
            while True:
                try:release=json.loads((workspace/'release.json').read_bytes())['tick']
                except (OSError,ValueError,KeyError):release=-1
                if release==tick:break
                if time.monotonic()-started>12:raise RuntimeError('Finite operator hold exceeded')
                time.sleep(0.01)
            if request['resource'] and tick==5:
                try:allocation=bytearray(256*1024**2)
                except MemoryError:
                    write(workspace/'resource-result.json',dict(requested_bytes=256*1024**2,allocation_denied=True,error='MemoryError',tick=tick));raise SystemExit(86)
                else:
                    write(workspace/'resource-result.json',dict(allocation_denied=False,size=len(allocation)));raise RuntimeError('Resource allowance failed')
        return original(old)
    world.next_state=advance
    try:world.run(workspace/'world',request['world_id'],request['revision'],work=2,max_ticks=32,seed=1,resume=request['resume'])
    finally:
        modules={name:getattr(module,'__file__') for name,module in sys.modules.items() if getattr(module,'__file__',None) and getattr(getattr(module,'__spec__',None),'origin',None) not in ('frozen','built-in')}
        write(workspace/'origins.json',dict(executable=sys.executable,prefix=sys.prefix,path=sys.path,modules=modules))


if __name__=='__main__':
    try:main(sys.argv[1])
    except (ValueError,OSError,KeyError,TypeError,RuntimeError) as error:
        write(Path(sys.argv[1])/'rejection.json',dict(error=str(error)));raise SystemExit(2)
