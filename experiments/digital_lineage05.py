"""Endogenous all-birth comparison; unchanged finite Descent04 world law."""
import base64,json,sys,zlib
from experiments.digital_descent04 import history as original_history

VERSION='DIGITAL-LINEAGE-05-v1'

def history(seed,mode='faithful',route='parity'):
    assert route in ('parity','fixed') and (route=='parity' or mode=='faithful')
    row=original_history(seed,mode,route);row['version']=VERSION
    return row

if __name__=='__main__':
    seed=int(sys.argv[1]);mode=sys.argv[2];route=sys.argv[3]
    assert seed in range(25400,25408)
    raw=json.dumps([history(seed,mode,route)],sort_keys=True,separators=(',',':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
