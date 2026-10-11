"""Supplied fixed exploration admission under unchanged Release07 laws."""
import base64, json, zlib
from . import digital_release07 as law
from .digital_affine_source18 import compile_program
CONTRACT='DIGITAL-AFFINE-ADMISSION-19-v1'
SEEDS=(26590,26591)
ROUTES=('affine3','alternating','fixed0','fixed1')

def history(seed, route):
    assert type(seed) is int and seed in SEEDS and route in ROUTES
    assert 'affine3' not in law.PROGRAMS
    law.PROGRAMS['affine3']=compile_program(3)
    try: return dict(contract=CONTRACT,history=law.history(seed,route,'faithful'))
    finally: del law.PROGRAMS['affine3']

if __name__=='__main__':
    import sys
    print(base64.b64encode(zlib.compress(json.dumps(history(int(sys.argv[1]),sys.argv[2]),sort_keys=True,separators=(',',':')).encode())).decode())
