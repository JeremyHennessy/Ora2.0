"""Paid cold-start reachability fixtures; none installed as discovered organisms."""
import base64,json,zlib
from . import digital_release07 as law
ANCESTOR=[[4,1,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]
ROUTES=('feedback6','feedback9','feedback12','feedback15','ancestor','alternating','fixed0','fixed1')
def history(seed,route):
    assert type(seed) is int and seed in (26090,26091) and route in ROUTES
    if not route.startswith('feedback'):row=law.history(seed,route,'faithful')
    else:
        code=sum(ANCESTOR,[]);code[int(route[8:])]=1;program=[code[i:i+3] for i in range(0,18,3)]
        assert route not in law.PROGRAMS;law.PROGRAMS[route]=program
        try:row=law.history(seed,route,'faithful')
        finally:del law.PROGRAMS[route]
    return dict(contract='DIGITAL-EXPERIENCE-12-PAID-FIXTURE-v1',history=row)
if __name__=='__main__':
    import sys
    print(base64.b64encode(zlib.compress(json.dumps(history(int(sys.argv[1]),sys.argv[2]),sort_keys=True,separators=(',',':')).encode())).decode())
