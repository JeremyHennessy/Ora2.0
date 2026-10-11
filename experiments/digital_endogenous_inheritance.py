"""Unscreened populations under the unchanged frozen digital VM law."""
import base64,json,sys,zlib
from experiments.digital_inheritance import history,ANCESTOR,MOBILE

def cases(phase):
    assert phase in ('primary','replication')
    seeds=range(24600,24664) if phase=='primary' else range(24664,24728)
    return [dict(seed=s,mode=m,program=p,label=label) for s in seeds
            for label,m,p in (('population','mutating',ANCESTOR),
                              ('population','faithful',ANCESTOR),
                              ('population','copy_disabled',ANCESTOR),
                              ('fixed_mobile','faithful',MOBILE))]

if __name__=='__main__':
    batch=json.loads(sys.argv[1]);assert 1<=len(batch)<=4
    raw=json.dumps([history(**c) for c in batch],sort_keys=True,separators=(',',':')).encode()
    assert len(raw)<=8*1024**2
    print(base64.b64encode(zlib.compress(raw)).decode())
