"""Separate COFACTOR interpreter; never imports producer."""
import argparse,json,math
from pathlib import Path
MODES=('candidate','catalyst-ghost','annealed','recycle-ghost','food-withdrawn','sham')
def random_next(n):
    n^=(n*8192)&4294967295;n^=n//131072;n^=(n*32)&4294967295;return n&4294967295
def audit_record(r):
    seed,mode=r['seed'],r['arm']
    if seed not in (*range(77000,77032),77999) or mode not in MODES:raise ValueError('Sample')
    pairs=[(a,b) for a in range(4) for b in range(a,4)];n=seed^2654435769;table=[]
    for pair in pairs:
        row=[]
        for target in range(4):n=random_next(n);row.append(int(n%256<64))
        table.append(row)
    def make(atom,kind,born=0,species=None,parents=None,fuel=None,cofactors=None):
        o=dict(id=len(objects),atom=atom,kind=kind,species=species,born=born,parents=parents or [],fuel=fuel,cofactors=cofactors or [],alive=True);objects.append(o);return o
    objects=[]
    for i in range(144):make(i,'F' if i<120 else 'W')
    bank=288;heat=0;windows=[];stats=dict(direct=0,recycled=0,decay=0,extra=0,post_withdrawal=0,losses=0);depleted=None;n=seed
    if len(r['trace'])!=8192 or r['cursor']!=65536:raise ValueError('Horizon')
    for tick,(raw,actual) in enumerate(r['trace']):
        nums=[]
        for _ in range(8):n=random_next(n);nums.append(n)
        if raw!=''.join(format(x,'08x') for x in nums):raise ValueError('Draw stream')
        special=None
        if tick in (2048,4096):
            target=seed%4 if tick==2048 else (seed//4)%4;victims=[o for o in objects if o['alive'] and o['kind']=='M' and o['species']==target]
            windows.append(dict(start=tick,target=target,lost=len(victims) if mode!='sham' else 0,exposed=bool(victims) and mode!='sham',eliminated=mode!='sham',first_birth=None,outputs=[],end_counts=None,end_fresh=None,success=False));special=['loss',target,[o['id'] for o in victims],mode=='sham']
            for old in victims:
                bank-=1;heat+=1
                if mode!='sham':old['alive']=False;make(old['atom'],'W',tick,parents=[old['id']]);heat+=2;stats['losses']+=1
        if tick==6144 and mode=='food-withdrawn':
            food=[o for o in objects if o['alive'] and o['kind']=='F'];special=['withdraw',[o['id'] for o in food]]
            for o in food:o['alive']=False;make(o['atom'],'R',tick,parents=[o['id']])
        ids=[i for i,o in enumerate(objects) if o['alive']];x,y,c,d=[objects[ids[nums[j]%144]] for j in (1,2,3,4)];target=nums[5]%4;byte=nums[6]%256;reaction=nums[0]%3;actors=[];outcome=None;product=None
        if c['kind']=='M' and d['kind']=='M' and c['id']!=d['id']:
            row=table[pairs.index(tuple(sorted((c['species'],d['species']))))];accepted=nums[7]%4<sum(row) if mode=='annealed' else row[target]==1
            if accepted and mode!='catalyst-ghost':actors=[c['id'],d['id']]
        if reaction in (0,1) and byte<(64 if actors else 4) and ((reaction==0 and x['kind']=='F') or (reaction==1 and x['kind']=='W' and y['kind']=='F')):
            food=x if reaction==0 else y;parents=[x['id']] if reaction==0 else [x['id'],y['id']];x['alive']=False
            if reaction==1:y['alive']=False;make(y['atom'],'W',tick,parents=parents)
            kind='X' if reaction==1 and mode=='recycle-ghost' else 'M';product=make(x['atom'],kind,tick,target,parents,food['id'],actors);heat+=4;stats['direct' if reaction==0 else 'recycled']+=1
            if actors and byte>=4:stats['extra']+=1
            if mode=='food-withdrawn' and tick>=6144:stats['post_withdrawal']+=1
            outcome=['convert',reaction,x['id'],food['id'],product['id'],kind,target,actors]
        elif reaction==2 and x['kind']=='M' and byte<8:
            x['alive']=False;product=make(x['atom'],'W',tick,parents=[x['id']]);heat+=2;stats['decay']+=1;outcome=['decay',x['id'],product['id']]
        if actual!=[special,outcome]:raise ValueError('Reaction/payment/cofactor/identity')
        for w in windows:
            if w['start']<=tick<w['start']+1024 and product and product['kind']=='M':
                if w['first_birth'] is None and product['species']==w['target']:w['first_birth']=tick
                if w['first_birth'] is not None and tick>w['first_birth']:w['outputs']=sorted(set(w['outputs'])|{product['species']})
            if tick==w['start']+1023:
                active=[o for o in objects if o['alive'] and o['kind']=='M'];counts=[sum(o['species']==s for o in active) for s in range(4)];fresh=sum(o['species']==w['target'] and o['born']>=w['start'] for o in active);w['end_counts']=counts;w['end_fresh']=fresh
                w['success']=bool(w['exposed'] and w['eliminated'] and w['outputs']==[0,1,2,3] and min(counts)>0 and fresh>0)
        live=[o for o in objects if o['alive']]
        if sorted(o['atom'] for o in live)!=list(range(144)):raise ValueError('Mass ownership')
        if heat+bank+sum(6 if o['kind'] in ('F','R') else 2 if o['kind'] in ('M','X') else 0 for o in live)!=1008 or bank<0:raise ValueError('Full energy')
        if depleted is None and not any(o['kind']=='F' for o in live):depleted=tick
    expected=dict(seed=seed,arm=mode,rng=n,step=8192,work=bank,heat=heat,catalogue=table,objects=objects,windows=windows,depleted_at=depleted,stats=stats);success=all(w['success'] for w in windows)
    if r['final']!=expected or r['success']!=success:raise ValueError('Complete state/endpoint')
    return dict(seed=seed,arm=mode,success=success,windows=windows,catalogue_degrees=[sum(row) for row in table],remaining_food=sum(o['kind']=='F' for o in live),reserved_food=sum(o['kind']=='R' for o in live),live_species=[sum(o['kind']=='M' and o['species']==s for o in live) for s in range(4)],bank=bank,heat=heat,depleted_at=depleted,**stats)
def panel(root,revision):
    root=Path(root);meta=json.loads((root/'manifest.json').read_bytes())
    if meta!=dict(revision=revision,seeds=list(range(77000,77032)),arms=list(MODES),worlds=192,attempts=1572864):raise ValueError('Manifest')
    if {p.name for p in root.iterdir()}!={'manifest.json'}|{f'{s}-{a}.json' for s in range(77000,77032) for a in MODES}:raise ValueError('Coverage')
    records=[audit_record(json.loads((root/f'{s}-{a}.json').read_bytes())) for s in range(77000,77032) for a in MODES];lookup={(r['seed'],r['arm']):r['success'] for r in records};counts={a:sum(r['success'] for r in records if r['arm']==a) for a in MODES};tests={}
    for null in ('catalyst-ghost','annealed'):
        wins=sum(lookup[s,'candidate'] and not lookup[s,null] for s in range(77000,77032));losses=sum(lookup[s,null] and not lookup[s,'candidate'] for s in range(77000,77032));n=wins+losses;tests[null]=dict(wins=wins,losses=losses,p=sum(math.comb(n,k) for k in range(wins,n+1))/2**n if n else 1.0)
    ps=sorted(t['p'] for t in tests.values());passed=counts['candidate']>=8 and ps[0]<=.025 and ps[1]<=.05
    totals={a:{k:sum(r[k] for r in records if r['arm']==a) for k in ('direct','recycled','decay','extra','post_withdrawal','losses')} for a in MODES}
    rounds={a:[dict(exposed=sum(r['windows'][j]['exposed'] for r in records if r['arm']==a),rebuilt=sum(r['windows'][j]['first_birth'] is not None for r in records if r['arm']==a),outputs_complete=sum(r['windows'][j]['outputs']==[0,1,2,3] for r in records if r['arm']==a),success=sum(r['windows'][j]['success'] for r in records if r['arm']==a)) for j in range(2)] for a in MODES}
    return dict(source_revision=revision,worlds=192,attempts=1572864,success=counts,comparisons=tests,primary_pass=passed,totals=totals,rounds=rounds,records=records,self_maintenance_accepted=False)
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:print(json.dumps(panel(a.input,a.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,TypeError) as e:print(e);raise SystemExit(2)
if __name__=='__main__':main()
