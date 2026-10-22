"""Data-only enrollment verification. No VM, sampling, actor or primary launcher."""
import hashlib
import json
from fractions import Fraction
from math import comb
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST='data/digital-budgeted-transfer-enrollment-v1.json'
SEALED_SHA256='61139d0c281ca8f067811e6dec97bdfcb5fc14ff72b7c44e82a4ce1d56bd6b50'
CANDIDATE_SHA256='b5871c5ea21c62be8eaefb872389bbeaf50984a38c72653e03fbebc727d61656'
WITNESS_SHA256='3549477f161841836b0e406bdfb1d2f72dd0e48e65567f28a65ab678d55f5838'

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()

def verify(raw,root=ROOT):
    if type(raw) is not bytes or len(raw)>65536 or hashlib.sha256(raw).hexdigest()!=SEALED_SHA256:
        raise ValueError('Exact prospectively sealed enrollment required')
    value=json.loads(raw)
    candidate=value['candidate'];code=candidate['code']
    if hashlib.sha256(canonical(code)).hexdigest()!=CANDIDATE_SHA256 or CANDIDATE_SHA256==WITNESS_SHA256:
        raise ValueError('Candidate identity/exclusion')
    if len(code)!=13 or code[0]!=[7,4,1] or any(type(word) is not int for row in code for word in row):
        raise ValueError('Exact literal shape')
    for name,digest in value['input_sha256'].items():
        path=Path(root)/name
        if not path.resolve().is_relative_to(Path(root).resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('Qualified input source changed: '+name)
    if value['execution_gate']['primary_started'] or value['execution_gate']['primary_admitted']:
        raise ValueError('Source enrollment is not execution admission')
    return value

def sign_probability(differences):
    """Exact sign probability; synthetic arithmetic only, no actor evaluation."""
    if type(differences) is not list or len(differences)!=64 or any(type(x) is not int or not -4<=x<=4 for x in differences):
        raise ValueError('Exactly64 complete paired independent-unit differences')
    wins=sum(x>0 for x in differences);losses=sum(x<0 for x in differences)
    n=wins+losses
    p=Fraction(sum(comb(n,k) for k in range(wins,n+1)),2**n) if n else Fraction(1)
    return dict(wins=wins,losses=losses,ties=64-n,p=p,mean=Fraction(sum(differences),64),
                passes=p<=Fraction(1,140) and sum(differences)>=64)

def primary_authority(*unused,**kwargs):
    raise RuntimeError('Primary unavailable: source review,NEW-only qualification and finite original-owner execution registration required')

if __name__=='__main__':
    value=verify((ROOT/MANIFEST).read_bytes())
    print(json.dumps(dict(source_enrollment_verified=True,candidate=value['candidate']['id'],
        candidate_executions=0,primary_ready=False,primary_started=False)))
