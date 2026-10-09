"""Fixed ISOLATION-04 adapter. Faults are instrumentation, not world physics."""
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
from experiments import heartbeat_template as world
from experiments import isolation_resource_worker as pressure


def main(workspace):
    workspace=Path(workspace)
    request=json.loads((workspace/'request.json').read_bytes())
    if set(request)!={'world_id','revision','resume','case'} or type(request['resume']) is not bool:
        raise ValueError('Fixed request')
    case=request['case']
    if case in {'reference','cpu','memory','wall'}:
        return pressure.main(workspace)
    if case not in {'io-journal','io-pending','io-replace'} or request['resume'] is not True:
        raise ValueError('Frozen continuation fault')
    (workspace/'world-started').write_text('started\n',encoding='utf-8')
    output=workspace/'world'; kind=case[3:]
    opened,fsync,replaced,write_file=Path.open,os.fsync,Path.replace,world.write_file
    payload=None; active=None; injected=False
    def trigger():
        nonlocal injected
        if injected or payload is None: raise ValueError('Exactly one targeted injection')
        injected=True
        trace=dict(kind=kind,tick=8,injections=1,payload_size=len(payload),payload_sha256=hashlib.sha256(payload).hexdigest())
        for path,data in ((workspace/'target-frame.json',payload),(workspace/'io-fault.json',(json.dumps(trace)+'\n').encode())):
            with opened(path,'xb') as stream:
                if stream.write(data)!=len(data): raise OSError('Incomplete trace')
                stream.flush(); fsync(stream.fileno())
    class Stream:
        def __init__(self,stream,path): self.stream,self.path,self.targeted=stream,path,False
        def __enter__(self): self.stream.__enter__(); return self
        def __exit__(self,*args): return self.stream.__exit__(*args)
        def __getattr__(self,name): return getattr(self.stream,name)
        def write(self,data):
            nonlocal payload,active
            try: frame=json.loads(data); target=frame['state']['simulation_tick']==8 and frame['reason']=='advanced'
            except (ValueError,KeyError,TypeError): target=False
            if target and not injected:
                payload=data
                if self.path.name=='frames.jsonl' and kind=='journal':
                    trigger(); part=data[:len(data)//2]
                    if self.stream.write(part)!=len(part): raise OSError('Injector incomplete')
                    self.stream.flush(); fsync(self.stream.fileno())
                    raise OSError('Injected half journal write')
                if self.path.name=='checkpoint.pending': self.targeted=True; active=self
            return self.stream.write(data)
    def wrapped(path,*args,**kwargs):
        stream=opened(path,*args,**kwargs)
        return Stream(stream,path) if path.parent==output and path.name in {'frames.jsonl','checkpoint.pending'} else stream
    def synced(fd):
        if kind=='pending' and active is not None and active.targeted and not injected and fd==active.fileno():
            trigger(); fsync(fd); raise OSError('Injected pending fsync-after failure')
        return fsync(fd)
    def replace(path,target):
        if kind=='replace' and path==output/'checkpoint.pending' and payload is not None and not injected:
            trigger(); raise OSError('Injected replacement-before failure')
        return replaced(path,target)
    def capture(path,frame):
        write_file(path,frame)
        if path==output/'checkpoint.pending' and frame['state']['simulation_tick']==7 and frame['reason']=='advanced':
            snapshot=workspace/'trusted-snapshot'; snapshot.mkdir()
            for name in ('manifest.json','frames.jsonl','checkpoint.json','checkpoint.pending'):
                with opened(output/name,'rb') as inp,opened(snapshot/name,'xb') as out:
                    data=inp.read()
                    if out.write(data)!=len(data): raise OSError('Snapshot incomplete')
                    out.flush(); fsync(out.fileno())
            with opened(snapshot/'writer.lock','xb') as out: out.write(b'L')
    with patch.object(Path,'open',wrapped),patch.object(os,'fsync',synced),patch.object(Path,'replace',replace),patch.object(world,'write_file',capture):
        world.run(output,request['world_id'],request['revision'],work=2,max_ticks=32,seed=1,resume=True)
    raise ValueError('Registered fault not reached')


if __name__=='__main__':
    try: main(sys.argv[1])
    except (ValueError,OSError,KeyError,TypeError) as error:
        try: (Path(sys.argv[1])/'rejection.json').write_text(json.dumps(dict(reason=str(error)))+'\n',encoding='utf-8')
        except OSError: pass  # Permission-denied workspace must still exit deterministically.
        raise SystemExit(2)
