"""Frozen supplied non-learning exploration software admission, unchanged law."""
import base64,json,zlib
from . import digital_release07 as law
SEEDS=(26190,26191)
ROUTES=('alternating','fixed0','fixed1')
CONTRACT='DIGITAL-EXPLORATION-13-v1'

def history(seed,route):
    assert type(seed) is int and seed in SEEDS and route in ROUTES
    return dict(contract=CONTRACT,history=law.history(seed,route,'faithful'))

if __name__=='__main__':
    import sys
    print(base64.b64encode(zlib.compress(json.dumps(history(int(sys.argv[1]),sys.argv[2]),sort_keys=True,separators=(',',':')).encode())).decode())
