"""Prospective INHERITANCE-01; existing VM law, disclosed fixed genotypes."""
import json
import sys
from experiments.digital_ecosystem import World, ANCESTOR

MOBILE=[1,2,4,5,6,3]  # Authored ordinary mobile copier, never discovery credit.
HORIZON=1536  # Greater than all 1292 available energy units; every opcode costs >=1.

def history(seed,mode,program,label):
    assert len(program)==6 and all(type(x) is int and 0<=x<16 for x in program)
    w=World(seed,mode)
    for cell,value in zip(w.entities[0]['code'],program):cell[0]=value
    w.check()
    while w.tick<64 and w.step():pass
    clone=World.restore(w.snapshot());row=w.run(HORIZON)
    assert row==clone.run(HORIZON) and not row['final']['entities']
    row.update(checkpoint_replay=True,genesis_program=program,label=label)
    return row

def generation_cases():
    return [dict(seed=s,mode=m,program=ANCESTOR,label='generation') for s in range(24100,24164) for m in ('mutating','faithful')]

def select(rows):
    # Static capability filter, independent of survival/food/birth success.
    programs=sorted({tuple(g[0] for g in e['birth']['child']['code']) for r in rows if r['mode']=='mutating' for e in r['events'] if 'birth' in e})
    eligible=[p for p in programs if 3 in p]
    return dict(all_programs=[list(p) for p in programs],candidate=list(eligible[0]) if eligible else None,eligible_programs=[list(p) for p in eligible])

def assay_cases(candidate):
    return [dict(seed=s,mode=m,program=p,label=label) for s in range(24200,24204)
            for label,p in (('candidate',candidate),('ancestor',ANCESTOR),('fixed_mobile',MOBILE))
            for m in ('faithful','copy_disabled')]

if __name__=='__main__':
    # Trusted experiment output wrapper only; genomes cannot access this interface.
    import base64,zlib
    cases=json.loads(sys.argv[1]);assert 1<=len(cases)<=4
    rows=[history(**c) for c in cases]
    raw=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
    assert len(raw)<=8*1024**2
    print(base64.b64encode(zlib.compress(raw)).decode())
