"""Configuration-only ordinary viability preflight; old VM laws unchanged."""
import base64,json,zlib
from . import digital_singlecopy09 as matched
from . import digital_release07 as ordinary

CONTRACT='DIGITAL-ORDINARY-ADMISSION-10-v1'
DOUBLE=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]
CONFIGURATIONS=('matched_double','disabled_double','actual_ordinary')
SEEDS=(25890,25891)

def history(seed,configuration):
    assert type(seed) is int and seed in SEEDS and configuration in CONFIGURATIONS
    if configuration=='actual_ordinary':
        row=ordinary.history(seed,'ancestor','faithful')
    else:
        # This process-local disclosed founder configuration changes no opcode,
        # resource or cost semantics. Never insert a selected descendant.
        name='admission10_double';assert name not in matched.PROGRAMS
        assert 3*len(DOUBLE)+18+16<=128
        matched.PROGRAMS[name]=[triple[:] for triple in DOUBLE]
        try:row=matched.history(seed,name,'copy_disabled' if configuration=='disabled_double' else 'faithful')
        finally:del matched.PROGRAMS[name]
    return dict(contract=CONTRACT,configuration=configuration,history=row)

if __name__=='__main__':
    import sys
    raw=json.dumps(history(int(sys.argv[1]),sys.argv[2]),sort_keys=True,separators=(',',':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
