"""Paid neutral-source admission only; unchanged Exposure23 VM and laws."""
import base64,json,zlib
from . import digital_informative_exposure23 as substrate
from .digital_neutral_catalogue25 import candidate
from .digital_affine_source18 import compile_program

VERSION='DIGITAL-CANDIDATE-ADMISSION-26-v1'
SEEDS=(26900,26901,26902,26903)
# All and only radius-one loop opcode substitutions to FEEDBACK. Structural
# accessibility, never measured fitness, determines this complete inclusion.
CANDIDATES=(1,94,187,280,373,466,559,652)

def programmes():
    codes={f'candidate{i}':candidate(i)['program'] for i in CANDIDATES}
    codes.update({f'affine{i}':compile_program(i) for i in range(8)})
    codes.update(alternating=[[4,1,1],[6,0,0],[5,0,1],[7,0,1]],fixed0=[[4,0,0],[6,0,0],[7,0,0]],fixed1=[[4,0,1],[6,0,0],[7,0,0]])
    return codes

def install_registry():
    # Canonical genesis names avoid duplicate-genome restore ambiguity. No old
    # module file/law is edited; this process-local input registry is disclosed.
    codes=programmes(); registry={}; routes={}
    for role,code in codes.items():
        key='genome-'+substrate.h(code)
        if key in registry:assert registry[key]==code
        registry[key]=code;routes[role]=key
    substrate.PROGRAMS=registry
    return codes,routes

def batch(seed,group):
    if type(seed) is not int or seed not in SEEDS or group not in ('candidates','references'):raise ValueError('Unregistered batch')
    codes,routes=install_registry()
    roles=list(codes)[:8] if group=='candidates' else list(codes)[8:]
    histories=[]
    for role in roles:
        row=substrate.history(seed,routes[role],'faithful')
        ancestry=candidate(int(role[9:])) if role.startswith('candidate') else None
        histories.append(dict(role=role,ancestry=ancestry,row=row))
    return dict(contract=VERSION,seed=seed,group=group,histories=histories,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    raw=json.dumps(batch(int(sys.argv[1]),sys.argv[2]),sort_keys=True,separators=(',',':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
