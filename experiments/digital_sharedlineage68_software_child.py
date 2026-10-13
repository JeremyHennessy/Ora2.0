"""Trusted finite software-run child. VM entities cannot call this host recorder.

The parent owns the lock, whole file grants, budget and verified parsing.
No admission, selection or scientific claim is conveyed by this module.
"""
import hashlib,json,sys
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    request=json.loads(Path(sys.argv[1]).read_bytes())
    root=Path.cwd();pins=request['source_files']
    assert all(sha(root/name)==digest for name,digest in pins.items())
    source_sha=hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert source_sha==request['source_sha256']
    provenance=dict(source_sha256=source_sha,configuration_sha256=request['configuration_sha256'])
    from experiments import evidence_write_grant68 as transport
    from experiments import digital_sharedlineage68_population as kernel
    calls=0;original=kernel.World.__init__
    def counted(self,*args,**kwargs):
        nonlocal calls
        calls+=1;return original(self,*args,**kwargs)
    kernel.World.__init__=counted
    def read(spec):
        path=Path(spec['path']);assert sha(path)==spec['sha256']
        assert path.stat().st_size==spec['extent'] and spec['extent']<=64*1024**2
        return json.loads(path.read_bytes())
    kind=request['kind'];role=request['role']
    if kind=='population':
        assert request['seed'] in (1,2)
        value=kernel.history(request['seed'],mode=request['mode'],inheritance_mode=request['inheritance_mode'])
    elif kind=='fork':
        from experiments import digital_sharedlineage68_world as fork
        natural=read(request['input']);assert natural['seed'] in (1,2)
        assert request['generation']==1
        value=fork.history(natural,1,request['fork_role'],provenance)
    elif kind=='population_ref':
        from experiments import digital_sharedlineage68_observe as observer
        from experiments import digital_sharedlineage68_interpret as natural
        row=read(request['input']);value=observer.audit_row(row,provenance)
        refusals=[]
        for field in ('clock','energy','material'):
            bad=natural.clone(row);event=bad['final']['events'][0]
            if field=='clock':event['tick']+=1
            elif field=='energy':event['after']['energy']+=1
            else:event['after']['code'][0][1]=511
            try:natural.audit(bad)
            except AssertionError:refusals.append(field)
            else:raise AssertionError('Forged complete population accepted')
        value['full_history_tamper_refusals']=refusals
    else:
        assert kind=='fork_ref'
        from experiments import digital_sharedlineage68_fork_interpret as referee
        row=read(request['input']);value=referee.audit(row,provenance)
        refusals=[]
        if row['branch'] is not None:
            for field in ('prefix_clock','boundary_hash','boundary_value'):
                bad=referee.clone(row)
                if field=='prefix_clock':bad['branch']['final']['events'][0]['tick']+=1
                elif field=='boundary_hash':bad['transition']['after_hash']='0'*64
                else:bad['transition']['after_code'][0][0]=(bad['transition']['after_code'][0][0]+1)%32
                try:referee.audit(bad,provenance)
                except AssertionError:refusals.append(field)
                else:raise AssertionError('Forged complete fork accepted')
        value['full_history_tamper_refusals']=refusals
    receipt=transport.record(request['grant'],request['grant_seal'],source_sha,
        request['configuration_sha256'],role,value)
    assert all(sha(root/name)==digest for name,digest in pins.items())
    receipt.update(world_constructors=calls,kind=kind,software_only=True)
    print(json.dumps(receipt,sort_keys=True,separators=(',',':')))


if __name__=='__main__':main()
