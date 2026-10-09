"""Fixed disposable ISOLATION-03 pressure adapter; unchanged world law."""
import json
import os
from pathlib import Path
import sys
import time
from experiments import heartbeat_template as world


def main(workspace):
    workspace=Path(workspace)
    request=json.loads((workspace/'request.json').read_bytes())
    if set(request)!={'world_id','revision','resume','case'} or type(request['resume']) is not bool:
        raise ValueError('Fixed request required')
    case=request['case']
    if case not in {'reference','cpu','cpu-control','memory','memory-control','wall','wall-control'}:
        raise ValueError('Frozen case required')
    if request['resume'] and case!='reference':
        raise ValueError('Pressure never repeats during resume')
    (workspace/'world-started').write_text('started\n',encoding='utf-8')
    original=world.write_file
    def mark(**values):
        (workspace/'pressure.json').write_text(json.dumps(values)+'\n',encoding='utf-8')
    def inject(path,frame):
        original(path,frame)
        if case=='reference' or path.name!='checkpoint.pending' or frame['state']['simulation_tick']!=5 or frame['reason']!='advanced':
            return
        control=case.endswith('-control'); kind=case.split('-')[0]
        amount=(0.05 if control else 7) if kind=='cpu' else ((32 if control else 256)*1024**2 if kind=='memory' else (0.05 if control else 12))
        trace=dict(case=case,tick=5,kind=kind,requested=amount,completed=False,memory_denied=False)
        mark(**trace)
        if kind=='cpu':
            end=time.process_time()+amount
            value=1
            while time.process_time()<end:
                for _ in range(10_000):
                    value=(value*1664525+1013904223) % 2**32
        elif kind=='wall':
            time.sleep(amount)
        else:
            try:
                allocation=bytearray(amount)
            except MemoryError:
                trace['memory_denied']=True; mark(**trace); os._exit(42)
            del allocation
        trace['completed']=True; mark(**trace)
    world.write_file=inject
    try:
        world.run(workspace/'world',request['world_id'],request['revision'],work=2,max_ticks=32,seed=1,resume=request['resume'])
    finally:
        world.write_file=original


if __name__=='__main__':
    try:
        main(sys.argv[1])
    except (ValueError,OSError,KeyError,TypeError) as error:
        (Path(sys.argv[1])/'rejection.json').write_text(json.dumps(dict(reason=str(error)))+'\n',encoding='utf-8')
        raise SystemExit(2)
