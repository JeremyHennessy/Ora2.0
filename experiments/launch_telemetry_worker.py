"""LAUNCH-01 fixed finite child; scheduling holds do not alter world physics."""
import json
from pathlib import Path
import sys
import time
from experiments import heartbeat_template as world


def write(path,value):path.write_text(json.dumps(value)+'\n',encoding='utf-8')


def main(workspace):
    workspace=Path(workspace);request=json.loads((workspace/'request.json').read_bytes())
    if set(request)!={'world_id','revision','resume','resource'} or type(request['resume']) is not bool or type(request['resource']) is not bool:raise ValueError('Fixed finite request')
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
