"""INHERITANCE-02, new prospective samples under the unchanged digital law."""
import base64,json,sys,zlib
from experiments.digital_inheritance import history

CANDIDATE=[1,2,4,3,6,12]
PROGRAMS=(('candidate',CANDIDATE),('ancestor',[1,2,4,5,6,12]),('fixed_mobile',[1,2,4,5,6,3]))
SEEDS={'primary':range(24400,24408),'replication':range(24408,24416)}

def cases(phase):
    return [dict(seed=s,mode=m,program=p,label=label) for s in SEEDS[phase]
            for label,p in PROGRAMS for m in ('faithful','copy_disabled')]

if __name__=='__main__':
    batch=json.loads(sys.argv[1]);assert 1<=len(batch)<=4
    raw=json.dumps([history(**c) for c in batch],sort_keys=True,separators=(',',':')).encode()
    assert len(raw)<=8*1024**2
    print(base64.b64encode(zlib.compress(raw)).decode())
