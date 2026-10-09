"""Disposable subprocess-only STORAGE-02 operation injection; never a service."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch
from experiments import heartbeat_template as worker

CASES = tuple(f'{where}-{how}' for where in ('journal','pending') for how in
              ('short-return','zero-return','short-error','flush-error','fsync-before','fsync-after','kill')) + ('replace-before','replace-after')

def run(output, trace_dir, case, world_id, revision, work=2, max_ticks=32, seed=1):
    if case not in CASES:
        raise ValueError('Frozen fault required')
    output, trace_dir = Path(output).resolve(), Path(trace_dir).resolve()
    if output.parent != trace_dir or output.exists() or not trace_dir.is_dir():
        raise ValueError('Fresh disposable world inside explicit trace directory')
    original_open, original_replace, original_fsync = Path.open, Path.replace, os.fsync
    injected = False
    payload = None
    active = None
    def trigger():
        nonlocal injected
        if injected or payload is None:
            raise ValueError('Exactly one injection with captured payload')
        injected = True
        trace = dict(case=case,tick=5,injections=1,payload_size=len(payload),payload_sha256=hashlib.sha256(payload).hexdigest())
        for path, data in ((trace_dir/'target-frame.json',payload),
                           (trace_dir/'injection.json',(json.dumps(trace,sort_keys=True)+'\n').encode())):
            with original_open(path,'xb') as f:
                if f.write(data) != len(data):
                    raise OSError('Incomplete injector trace')
                f.flush(); original_fsync(f.fileno())
    class Stream:
        def __init__(self, stream, path):
            self.stream, self.path, self.targeted = stream, path, False
        def __enter__(self):
            self.stream.__enter__(); return self
        def __exit__(self,*args):
            return self.stream.__exit__(*args)
        def __getattr__(self,name):
            return getattr(self.stream,name)
        def write(self,data):
            nonlocal payload,active
            if not injected:
                try:
                    value=json.loads(data)
                    match=value['state']['simulation_tick']==5 and value['reason']=='advanced'
                except (ValueError,KeyError,TypeError):
                    match=False
                if match:
                    payload=data
                    where='journal' if self.path.name=='frames.jsonl' else 'pending'
                    if case.startswith(where+'-'):
                        self.targeted=True; active=self
                        how=case.split('-',1)[1]
                        if how in ('short-return','zero-return','short-error','kill'):
                            trigger()
                            if how=='zero-return':
                                return 0
                            part=data[:len(data)//2]
                            count=self.stream.write(part)
                            if count != len(part):
                                raise OSError('Injector itself short-wrote')
                            if how=='short-return':
                                return count
                            self.stream.flush(); original_fsync(self.stream.fileno())
                            if how=='kill':
                                os._exit(81 if where=='journal' else 82)
                            raise OSError('Injected half-write error')
            return self.stream.write(data)
        def flush(self):
            if self.targeted and not injected and case.endswith('flush-error'):
                trigger(); raise OSError('Injected flush error before delegation')
            return self.stream.flush()
    def opened(path,*args,**kwargs):
        stream=original_open(path,*args,**kwargs)
        if path.parent.resolve()==output and path.name in ('frames.jsonl','checkpoint.pending'):
            return Stream(stream,path)
        return stream
    def synced(fd):
        if active is not None and active.targeted and not injected and fd==active.fileno() and case.endswith(('fsync-before','fsync-after')):
            trigger()
            if case.endswith('after'):
                original_fsync(fd)
            raise OSError('Injected fsync error')
        return original_fsync(fd)
    def replaced(path,target):
        if not injected and case.startswith('replace-') and path.parent.resolve()==output and path.name=='checkpoint.pending' and payload is not None:
            trigger()
            if case=='replace-after':
                original_replace(path,target)
            raise OSError('Injected replacement error')
        return original_replace(path,target)
    with patch.object(Path,'open',opened),patch.object(Path,'replace',replaced),patch.object(os,'fsync',synced):
        worker.run(output,world_id,revision,work,max_ticks,seed)
    if not injected:
        raise ValueError('Fault target was not reached')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('case','trace-dir','output-dir','world-id','source-revision'):
        p.add_argument('--'+key,required=True)
    p.add_argument('--work',type=int,default=2); p.add_argument('--max-ticks',type=int,default=32); p.add_argument('--seed',type=int,default=1)
    a=p.parse_args()
    try:
        run(a.output_dir,a.trace_dir,a.case,a.world_id,a.source_revision,a.work,a.max_ticks,a.seed)
    except (ValueError,OSError,KeyError,TypeError) as e:
        p.exit(2,f'Faulted writer: {e}\n')
