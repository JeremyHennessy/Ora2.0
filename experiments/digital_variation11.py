"""Prospective natural lineages in the admitted configuration; old laws unchanged."""
import base64,json,zlib
from . import digital_singlecopy09 as matched
from . import digital_release07 as ordinary
CONTRACT='DIGITAL-VARIATION-11-v1'
DOUBLE=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]
CONFIGURATIONS=('single','per_word','faithful','actual_ordinary')

def history(seed,configuration):
    assert type(seed) is int and 25900<=seed<25908 and configuration in CONFIGURATIONS
    if configuration=='actual_ordinary':row=ordinary.history(seed,'ancestor','faithful')
    else:
        name='variation11_double';assert name not in matched.PROGRAMS
        matched.PROGRAMS[name]=[t[:] for t in DOUBLE]
        try:row=matched.history(seed,name,configuration)
        finally:del matched.PROGRAMS[name]
    return dict(contract=CONTRACT,configuration=configuration,history=row)

if __name__=='__main__':
    import sys
    raw=json.dumps(history(int(sys.argv[1]),sys.argv[2]),sort_keys=True,separators=(',',':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
