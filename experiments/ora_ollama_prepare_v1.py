"""Explicit finite cold-start stage; loads installed model without generating tasks."""
import http.client
import json
from pathlib import Path
import sys
from experiments.ora_native_slice_v1 import run_slice,Limits


def worker():
    connection=http.client.HTTPConnection('127.0.0.1',11434,timeout=120)
    try:
        body=json.dumps(dict(model='gpt-oss:20b',prompt='',stream=False,keep_alive='60s',
                             options=dict(num_gpu=0,num_ctx=2048,num_predict=1)))
        connection.request('POST','/api/generate',body,{'Content-Type':'application/json'})
        response=connection.getresponse(); raw=response.read(16385)
        if response.status!=200 or len(raw)>16384:
            raise RuntimeError('Cold preparation refused or oversized')
        result=json.loads(raw)
        if result.get('done') is not True:
            raise RuntimeError('Cold preparation incomplete')
        print(json.dumps(dict(prepared=True,model='gpt-oss:20b',response=result)))
    finally:
        connection.close()


def prepare():
    return run_slice(lambda *unused:[sys.executable,'-B','-m','experiments.ora_ollama_prepare_v1','--worker'],
        Path(__file__).resolve().parents[1],Limits(memory_bytes=64*1024**2,cpu_seconds=5,processes=2,wall_seconds=125))


if __name__=='__main__':
    if sys.argv[1:]==['--worker']: worker()
    elif not sys.argv[1:]:
        result=prepare(); print(json.dumps(result))
        raise SystemExit(0 if result['exit_code']==0 and result['reason']=='exit' else 1)
    else: raise SystemExit('No arbitrary model or endpoint configuration allowed in preparation v1')
