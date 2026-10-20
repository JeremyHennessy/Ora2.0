"""Loopback-only Ollama proposals plus explicit operator-signed corrections.

The model gets prompt text only: no feedback key, tools, file or task execution.
An operator-approved correction is the only model-mode path into trusted memory.
"""
import hashlib
import hmac
import http.client
import json
from pathlib import Path
import re


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')


def generate(model, prompt):
    if type(model) is not str or not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,128}',model):
        raise ValueError('Explicit installed model name required')
    if type(prompt) is not str or not 0<len(prompt.encode('utf8'))<=4096:
        raise ValueError('Prompt exceeds bounds')
    # http.client uses this literal loopback destination, no proxy or redirects.
    connection=http.client.HTTPConnection('127.0.0.1',11434,timeout=50)
    try:
        body=canonical(dict(model=model,prompt=prompt,stream=False,keep_alive=0,
            think='low' if model.split(':')[0].endswith('gpt-oss') else False,
            options=dict(num_predict=128,num_ctx=2048,temperature=0)))
        connection.request('POST','/api/generate',body,{'Content-Type':'application/json'})
        response=connection.getresponse(); raw=response.read(65537)
        if response.status!=200 or len(raw)>65536:
            raise ValueError('Ollama refused or exceeded bounded response')
        result=json.loads(raw)
        answer=result.get('response')
        if result.get('done') is not True or type(answer) is not str or not 0<len(answer.encode('utf8'))<=4096:
            raise ValueError('Incomplete or oversized Ollama proposal')
        return answer
    finally:
        connection.close()


def sign(key, sequence, memory_key, proposal_sha256, corrected_value):
    value=dict(sequence=sequence,key=memory_key,proposal_sha256=proposal_sha256,value=corrected_value)
    value['mac']=hmac.new(key,canonical(value),hashlib.sha256).hexdigest()
    return json.dumps(value,sort_keys=True,separators=(',',':'))


def verify(key, sequence, memory_key, raw):
    value=json.loads(raw)
    if type(value) is not dict or set(value)!={'sequence','key','proposal_sha256','value','mac'}:
        raise ValueError('Explicit signed feedback required')
    mac=value.pop('mac')
    if type(mac) is not str or not hmac.compare_digest(mac,hmac.new(key,canonical(value),hashlib.sha256).hexdigest()):
        raise ValueError('Feedback authentication failed')
    if value['sequence']!=sequence or value['key']!=memory_key:
        raise ValueError('Feedback bound to another task')
    if type(value['value']) is not str or not 0<len(value['value'].encode('utf8'))<=2048:
        raise ValueError('Correction exceeds bounds')
    if type(value['proposal_sha256']) is not str or not re.fullmatch('[0-9a-f]{64}',value['proposal_sha256']):
        raise ValueError('Invalid proposal binding')
    return value


def configuration(root):
    path=Path(root)/'ollama.json'
    if not path.exists(): return None,None
    raw=path.read_bytes()
    if len(raw)>1024: raise ValueError('Oversized Ollama configuration')
    value=json.loads(raw)
    if type(value) is not dict or set(value)!={'model'}:
        raise ValueError('Only an explicit local model may be configured')
    model=value['model']
    if type(model) is not str or not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,128}',model):
        raise ValueError('Invalid model name')
    secret_path=Path(root)/'feedback.key'
    if secret_path.is_symlink() or getattr(secret_path.lstat(),'st_file_attributes',0)&0x400 or secret_path.stat().st_nlink!=1:
        raise ValueError('Feedback key must be a plain unshared local file')
    secret=secret_path.read_bytes()
    if len(secret)!=32: raise ValueError('A separately provisioned 32-byte feedback key is required')
    return lambda prompt:generate(model,prompt),secret
