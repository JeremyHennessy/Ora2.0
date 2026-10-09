"""GRADIENT-01 finite paid surface physics; no organism/controller/service."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import time

ARMS=('candidate','ghost','free-transport','flattened','withdrawal','supplied-bonds')
FILES=('experiments/gradient_binding.py','experiments/gradient_binding_audit.py','docs/GRADIENT-01-PROTOCOL.md')
ROOT=Path(__file__).resolve().parents[1]
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def save(p,x):Path(p).write_text(canon(x)+'\n',encoding='utf-8',newline='\n')


class Surface:
    def __init__(self,seed,arm,sites=None):
        if arm not in ARMS:raise ValueError('Registered arm')
        self.seed,self.arm=seed,arm;self.rng=random.Random(seed)
        priorities=[self.rng.getrandbits(16) for _ in range(64)]
        self.sites=sites if sites is not None else sorted(range(64),key=lambda i:(priorities[i],i))[:48]
        if len(self.sites)!=48 or len(set(self.sites))!=48 or any(type(i) is not int or not 0<=i<64 for i in self.sites):raise ValueError('48 distinct sites')
        self.pairs=[(i,j) for i in range(48) for j in range(i+1,48) if abs(self.sites[i]//8-self.sites[j]//8)+abs(self.sites[i]%8-self.sites[j]%8)==1]
        ranks=[self.rng.getrandbits(16) for _ in range(64)];self.cursor=128
        self.photons={i:[] for i in range(64)}
        for i in range(2048):self.photons[i//32 if arm=='flattened' else (i//256)*8].append(i)
        self.q={i:[] for i in range(48)};self.energy={};self.next_energy=0
        self.bonds={};self.active=[];self.next_bond=0;self.external=list(range(128));self.exported=[];self.heat=0
        self.setup=[]
        if arm=='supplied-bonds':
            order=sorted(range(len(self.pairs)),key=lambda i:(ranks[i%64],self.pairs[i]))[:12]
            for index in order:self.setup.append(self.perform(['external',list(self.pairs[index]),self.external[:4]],-1))

    def snapshot(self):
        return dict(sites=self.sites,photons=self.photons,q=self.q,energy=self.energy,next_energy=self.next_energy,
            bonds=self.bonds,active=self.active,next_bond=self.next_bond,external=self.external,exported=self.exported,
            heat=self.heat,cursor=self.cursor,rng=self.rng.getstate())

    def choose_two(self,pool,d):
        if len(pool)<2:return []
        first=pool[d[4]%len(pool)];rest=[i for i in pool if i!=first];return [first,rest[d[5]%len(rest)]]

    def request(self,d):
        op=d[0]%4
        if op==0:
            node=d[1]%48;return ['capture',node,self.choose_two(self.photons[self.sites[node]],d)]
        if op==1 and self.pairs:
            pair=list(self.pairs[d[1]%len(self.pairs)]);payer=pair[d[2]%2]
            return ['bind',pair,payer,self.choose_two(self.q[payer],d)] if d[3]%4==0 else ['noop']
        if op==2 and self.active:
            return ['unbind',self.active[d[1]%len(self.active)]] if d[3]%32==0 else ['noop']
        if op==3:
            pool=self.pairs if self.arm=='free-transport' else self.active
            if pool:
                selected=pool[d[1]%len(pool)];bond=None if self.arm=='free-transport' else selected
                pair=list(selected) if bond is None else self.bonds[bond]['pair'];donor=pair[d[2]%2];receiver=pair[1-d[2]%2]
                return ['transport',bond,donor,receiver,self.choose_two(self.q[donor],d)]
        return ['noop']

    def charged(self,parents,routes,assisted,kind,step):
        key=self.next_energy;self.next_energy+=1
        self.energy[key]=dict(parents=parents,routes=routes,assisted=assisted,kind=kind,born=step);return key

    def perform(self,r,t):
        op=r[0];event=['noop']
        if op=='capture':
            node,paid=r[1:];stock=self.photons[self.sites[node]]
            if len(paid)==len(set(paid))==2 and len(self.q[node])<8 and all(p in stock for p in paid):
                for p in paid:stock.remove(p)
                key=self.charged([['photon',p] for p in paid],[],False,'capture',t);self.q[node].append(key);self.heat+=1;event=['capture',node,paid,key]
        elif op in ('bind','external'):
            pair=r[1];payer=None if op=='external' else r[2];paid=r[2] if op=='external' else r[3]
            pool=self.external if payer is None else self.q[payer]
            if tuple(pair) in self.pairs and (payer is None or payer in pair) and not any(self.bonds[k]['pair']==pair for k in self.active) and len(paid)==len(set(paid))==(4 if payer is None else 2) and all(p in pool for p in paid):
                for p in paid:pool.remove(p)
                key=self.next_bond;self.next_bond+=1
                self.bonds[key]=dict(pair=pair,payer=payer,paid=paid,born=t,assisted=payer is None or any(self.energy[p]['assisted'] for p in paid))
                self.active.append(key);self.heat+=3 if payer is None else 1;event=['bind',key]
        elif op=='unbind' and r[1] in self.active:
            self.active.remove(r[1]);self.heat+=1;event=r
        elif op=='transport':
            bond,donor,receiver,paid=r[1:]
            allowed=tuple(sorted((donor,receiver))) in self.pairs if bond is None and self.arm=='free-transport' else bond in self.active and self.bonds[bond]['pair']==sorted((donor,receiver))
            if allowed and len(paid)==len(set(paid))==2 and all(p in self.q[donor] for p in paid) and len(self.q[receiver])<8:
                for p in paid:self.q[donor].remove(p)
                if self.arm=='ghost':self.heat+=2;event=['ghost',bond,donor,receiver,paid]
                else:
                    routes={tuple(route) for p in paid for route in self.energy[p]['routes']}
                    if bond is not None:routes.add((bond,t))
                    assisted=any(self.energy[p]['assisted'] for p in paid) or (bond is not None and self.bonds[bond]['assisted'])
                    key=self.charged([['carrier',p] for p in paid],[list(x) for x in sorted(routes)],assisted,'transport',t)
                    self.q[receiver].append(key);self.heat+=1;event=['transport',bond,donor,receiver,paid,key]
        return event

    def step(self,t,d):
        exported=[]
        if self.arm=='withdrawal' and t==8192:
            exported=sorted(p for stock in self.photons.values() for p in stock);self.exported+=exported
            self.photons={i:[] for i in range(64)}
        r=self.request(d);return [exported,r,self.perform(r,t)]


def world(folder,seed,arm,steps=16384,sites=None):
    folder=Path(folder);folder.mkdir();model=Surface(seed,arm,sites)
    save(folder/'initial.json',dict(seed=seed,arm=arm,steps=steps,setup=model.setup,state=model.snapshot()))
    with (folder/'attempts.jsonl').open('w',encoding='utf-8',newline='\n') as out:
        for t in range(steps):
            d=[model.rng.getrandbits(16) for _ in range(8)];model.cursor+=8
            out.write(canon([t,d,model.step(t,d)])+'\n')
    save(folder/'final.json',model.snapshot())


def batch(folder,index,revision):
    folder=Path(folder)
    if index not in range(4) or len(revision)!=40 or folder.exists() or folder.resolve().drive.upper()!='D:' or shutil.disk_usage(folder.parent).free<5*1024**3:raise ValueError('Fixed fresh D: batch/source/floor')
    folder.mkdir();started=time.monotonic()
    meta=dict(schema='gradient01-v1',revision=revision,batch=index,seeds=list(range(53000+8*index,53008+8*index)),arms=list(ARMS),steps=16384,worlds=[],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES});save(folder/'manifest.json',meta)
    for seed in meta['seeds']:
        for arm in ARMS:
            if time.monotonic()-started>280 or sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())>256*1024**2:raise RuntimeError('Fixed batch ceiling')
            name=f'{seed}-{arm}';world(folder/name,seed,arm);meta['worlds'].append(name);save(folder/'manifest.json',meta)
    if time.monotonic()-started>280 or sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())>256*1024**2:raise RuntimeError('Fixed final batch ceiling')
    meta['files_sha256']={p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'};save(folder/'manifest.json',meta)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);p.add_argument('--batch',type=int,required=True);p.add_argument('--source-revision',required=True);a=p.parse_args();batch(a.output_dir,a.batch,a.source_revision)
