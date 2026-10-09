"""KINETIC-01 prospective finite chemistry; no service, reward or chosen founders."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import time

ARMS=('candidate','inert','well-mixed','regeneration-off','withdrawal','supplied-dimers')
FILES=('experiments/kinetic_dynamics.py','experiments/kinetic_dynamics_audit.py',
       'docs/KINETIC-01-PROTOCOL.md','docs/KINETIC-01-DRAW-CONTRACT.md')
ROOT=Path(__file__).resolve().parents[1]


def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'))
def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()
def save(path,value): Path(path).write_text(canonical(value)+'\n',encoding='utf-8',newline='\n')


class Chemistry:
    def __init__(self,seed,arm):
        if arm not in ARMS: raise ValueError('Registered arm')
        self.seed,self.arm=seed,arm; self.rng=random.Random(seed)
        self.bits=[self.rng.getrandbits(1) for _ in range(96)]; self.cursor=96
        self.objects={i:dict(atoms=[i],parents=[],born=-1,site=i//6,assisted=False) for i in range(96)}
        self.active={i:i//6 for i in range(96)}; self.next_id=96
        self.tokens={i:[i//16,True] for i in range(256)}
        self.photons=[32]*16; self.heat=0; self.exported=0; self.setup=[]
        if arm=='supplied-dimers':
            for i in range(0,24,2):
                fuel=[k for k,v in self.tokens.items() if v==[i//6,True]][:2]
                self.setup.append(self.join(i,i+1,fuel,-1,None,True))

    def word(self,obj): return ''.join(str(self.bits[a]) for a in self.objects[obj]['atoms'])

    def new(self,atoms,parents,step,site,assisted):
        key=self.next_id; self.next_id+=1
        self.objects[key]=dict(atoms=atoms,parents=parents,born=step,site=site,assisted=assisted)
        self.active[key]=site; return key

    def join(self,left,right,fuel,step,catalyst,assisted=False):
        a,b=self.objects[left],self.objects[right]; site=self.active[left]
        key=self.new(a['atoms']+b['atoms'],[left,right],step,site,assisted or a['assisted'] or b['assisted'])
        del self.active[left]; del self.active[right]
        for token in fuel: self.tokens[token][1]=False
        self.heat+=1
        return ['associate',left,right,key,catalyst,fuel]

    def pool(self,site):
        return sorted(k for k,v in self.active.items() if self.arm=='well-mixed' or v==site)

    def token_pool(self,site,charged=None):
        return sorted(k for k,v in self.tokens.items() if (self.arm=='well-mixed' or v[0]==site) and (charged is None or v[1]==charged))

    def request(self,step,draw):
        operation,site=draw[0]%4,draw[1]%16
        withdrawal=0
        if self.arm=='withdrawal' and step==4096:
            withdrawal=sum(self.photons); self.exported+=withdrawal; self.photons=[0]*16
        outcome=['noop']
        pool=self.pool(site)
        if operation==0:
            carriers=[('object',k) for k in pool]+[('token',k) for k in self.token_pool(site)]
            if carriers:
                kind,key=carriers[draw[2]%len(carriers)]
                old=self.active[key] if kind=='object' else self.tokens[key][0]
                x,y=old%4,old//4; dx,dy=((-1,0),(1,0),(0,-1),(0,1))[draw[5]%4]
                target=((y+dy)%4)*4+(x+dx)%4
                if kind=='object': self.active[key]=target
                else: self.tokens[key][0]=target
                outcome=['diffuse',kind,key,old,target]
        elif operation==1 and len(pool)>=2:
            left=pool[draw[2]%len(pool)]; others=[k for k in pool if k!=left]; right=others[draw[3]%len(others)]
            cats=[k for k in pool if k not in (left,right) and len(self.objects[k]['atoms'])>=2]
            catalyst=cats[draw[4]%len(cats)] if cats else None
            mapped=catalyst is not None and hashlib.sha256(f'KINETIC01|{self.seed}|{self.word(catalyst)}|{self.word(left)}|{self.word(right)}'.encode()).digest()[0]<8
            helped=mapped and self.arm!='inert'
            fuel=self.token_pool(site,True)
            if len(self.objects[left]['atoms'])+len(self.objects[right]['atoms'])<=6 and len(fuel)>=2 and draw[6]%32<(8 if helped else 1):
                first=fuel[draw[7]%len(fuel)]; second=[k for k in fuel if k!=first]; second=second[draw[3]%len(second)]
                outcome=self.join(left,right,[first,second],step,catalyst if helped else None)
        elif operation==2 and pool:
            key=pool[draw[2]%len(pool)]; obj=self.objects[key]
            if len(obj['atoms'])>=2 and draw[6]%16<1:
                split=1+draw[5]%(len(obj['atoms'])-1); site=self.active.pop(key)
                children=[self.new(atoms,[key],step,site,obj['assisted']) for atoms in (obj['atoms'][:split],obj['atoms'][split:])]
                self.heat+=1; outcome=['cleave',key,split,children]
        elif operation==3 and self.arm!='regeneration-off':
            waste=self.token_pool(site,False)
            if waste:
                key=waste[draw[2]%len(waste)]; where=self.tokens[key][0]
                if self.photons[where]>=2 and draw[6]%2<1:
                    self.tokens[key][1]=True; self.photons[where]-=2; self.heat+=1; outcome=['regenerate',key,where]
        return [withdrawal,outcome]

    def state(self):
        return dict(bits=self.bits,objects=self.objects,active=self.active,tokens=self.tokens,
            next_id=self.next_id,photons=self.photons,heat=self.heat,exported=self.exported,
            cursor=self.cursor,rng=self.rng.getstate())

    def draw(self):
        value=[self.rng.getrandbits(16) for _ in range(8)]; self.cursor+=8; return value


def run_world(output,seed,arm,steps=8192):
    output=Path(output); output.mkdir(); chem=Chemistry(seed,arm)
    save(output/'initial.json',dict(seed=seed,arm=arm,steps=steps,setup=chem.setup,state=chem.state()))
    with (output/'attempts.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
        for step in range(steps):
            draws=chem.draw(); stream.write(canonical([step,draws,chem.request(step,draws)])+'\n')
    save(output/'final.json',chem.state())


def batch(output,index,revision):
    if index not in range(4) or len(revision)!=40: raise ValueError('Fixed batch/source')
    output=Path(output)
    if output.exists() or output.resolve().drive.upper()!='D:' or shutil.disk_usage(output.parent).free<5*1024**3: raise ValueError('Fresh D: output / floor')
    output.mkdir(); start=time.monotonic()
    metadata=dict(schema='kinetic01-dynamics-v1',revision=revision,batch=index,seeds=list(range(43000+8*index,43008+8*index)),arms=list(ARMS),steps=8192,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},worlds=[])
    save(output/'manifest.json',metadata)
    for seed in metadata['seeds']:
        for arm in ARMS:
            if time.monotonic()-start>280 or sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>256*1024**2: raise RuntimeError('Fixed batch cap')
            run_world(output/f'{seed}-{arm}',seed,arm)
            metadata['worlds'].append(f'{seed}-{arm}'); save(output/'manifest.json',metadata)
    metadata['files_sha256']={p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*') if p.is_file() and p.name!='manifest.json'}
    save(output/'manifest.json',metadata)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output-dir',required=True); parser.add_argument('--batch',type=int,required=True); parser.add_argument('--source-revision',required=True)
    args=parser.parse_args(); batch(args.output_dir,args.batch,args.source_revision)
