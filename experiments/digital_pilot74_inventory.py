"""Prospective finite whole-writer inventory; no execution or activation entrypoint.

All files must be precharged before the first child. Smaller per-cut caps are
additional falsifiers inside the frozen 40MiB ceiling, not altered VM prices.
"""
MIB=1024**2
RAW_CAP=1280*MIB
CUT_CAP={8192:24*MIB,9216:32*MIB,10240:40*MIB}
VERSION='DIGITAL-PILOT74-WRITER-INVENTORY-v1'

def plan():
    roles=[];files=[]
    def file(name,limit):files.append(dict(name=name,limit=limit))
    def role(name,genesis=0,hydrates=0,steps=0,exit_code=0):
        roles.append(dict(name=name,genesis=genesis,hydrates=hydrates,steps=steps,exit_code=exit_code))
        file('requests/'+name+'.json',MIB);file('native/'+name+'.json',MIB)
        file('receipts/'+name+'.json',128*1024)
    for export in ('original','restored'):
        role(export+'/prepared')
        role(export+'/generate',genesis=1,steps=10240)
        for cut in (8192,9216,10240):
            file(f'data/{export}/capsule{cut}.json',CUT_CAP[cut])
            role(f'{export}/audit{cut}');file(f'data/{export}/audit{cut}.json',128*1024)
            role(f'{export}/resume{cut}',hydrates=1,steps=10240-cut)
            file(f'data/{export}/resume{cut}.json',40*MIB if cut<10240 else 8192)
    # Four distinct cases, each beginning at independently accepted9216.
    for fault in ('partial','orphan','committed','normal'):
        role('crash/'+fault,hydrates=1,steps=1024,exit_code=0 if fault=='normal' else 78)
        role('recover/'+fault,hydrates=1,steps=1024 if fault in ('partial','orphan') else 0)
        for name,limit in [('capsule-2.json',32*MIB),('capsule-3.json',40*MIB),('payload.pending',40*MIB),('recovery.json',40*MIB),('head.json',16384),('head.pending',16384),('observation.json',16384)]:
            file('journal/'+fault+'/'+name,limit)
    role('normal-sequence',hydrates=1,steps=2048)
    for name,limit in [('capsule-1.json',24*MIB),('capsule-2.json',32*MIB),('capsule-3.json',40*MIB),('payload.pending',40*MIB),('head.json',16384),('head.pending',16384),('observation.json',16384)]:
        file('journal/sequence/'+name,limit)
    # One closed reader authenticates projections/publication from full audited
    # records. No World or another prefix execution allowed in this child.
    role('closed-projection-publication-audit')
    file('compatibility/old-capsule8192.json',24*MIB)
    file('compatibility/old-audit8192.json',128*1024)
    file('publication/initial.000001.json',65536)
    file('publication/genesis.000001.json',16384)
    for index in range(1,17):file(f'publication/events.000001.{index:04d}.json',MIB)
    for sequence in (1,2,3):
        for kind in ('manifest','status','audit','process'):file(f'publication/{kind}.{sequence:06d}.json',16384)
    file('publication/head.json',16384);file('publication/head.pending',16384)
    # A source archive and both physical exports belong to archive/restore
    # ledgers. This raw allowance covers the exact reviewed source export,
    # registration, writer/helpers, seals, ledger snapshots and final summary.
    file('metadata-reserve',8*MIB)
    value=dict(version=VERSION,roles=roles,files=files)
    validate(value);return value

def validate(value):
    assert type(value) is dict and set(value)=={'version','roles','files'} and value['version']==VERSION
    roles=value['roles'];files=value['files']
    assert type(roles) is list and type(files) is list
    assert len(roles)==26 and len({r['name'] for r in roles})==26
    for r in roles:
        assert type(r) is dict and set(r)=={'name','genesis','hydrates','steps','exit_code'}
        assert type(r['name']) is str and r['name'] and '..' not in r['name'] and not r['name'].startswith('/')
        for key in ('genesis','hydrates','steps','exit_code'):assert type(r[key]) is int and r[key]>=0
        assert r['exit_code'] in (0,78)
    totals={k:sum(r[k] for r in roles) for k in ('genesis','hydrates','steps')}
    assert totals==dict(genesis=2,hydrates=15,steps=34816)
    assert len({f['name'] for f in files})==len(files)
    for f in files:
        assert type(f) is dict and set(f)=={'name','limit'}
        assert type(f['name']) is str and f['name'] and '..' not in f['name'] and not f['name'].startswith('/') and ':' not in f['name'] and '\\' not in f['name']
        assert type(f['limit']) is int and 0<f['limit']<=40*MIB
    raw=sum(f['limit'] for f in files);assert raw<=RAW_CAP
    return dict(native_children=len(roles),**totals,raw_precharge_bytes=raw,raw_margin_bytes=RAW_CAP-raw,stage_credit=False,execution_admitted=False)
