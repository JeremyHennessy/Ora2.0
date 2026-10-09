"""Separate KINETIC-01 interpreter and lifecycle evaluator; no producer imports."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random

ARMS=('candidate','inert','well-mixed','regeneration-off','withdrawal','supplied-dimers')
FILES=('experiments/kinetic_dynamics.py','experiments/kinetic_dynamics_audit.py','docs/KINETIC-01-PROTOCOL.md','docs/KINETIC-01-DRAW-CONTRACT.md')


def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def require(value,message):
    if not value: raise ValueError(message)


class Interpreter:
    def __init__(self,seed,arm):
        self.seed,self.arm=seed,arm; self.random=random.Random(seed)
        self.s=dict(bits=[self.random.getrandbits(1) for _ in range(96)],objects={},active={},tokens={},next_id=96,photons=[32]*16,heat=0,exported=0,cursor=96,rng=self.random.getstate())
        for i in range(96):
            self.s['objects'][str(i)]=dict(atoms=[i],parents=[],born=-1,site=i//6,assisted=False);self.s['active'][str(i)]=i//6
        for i in range(256):self.s['tokens'][str(i)]=[i//16,True]
        self.setup=[]
        if arm=='supplied-dimers':
            for i in range(0,24,2):
                fuel=[int(k) for k,v in self.s['tokens'].items() if v==[i//6,True]][:2]
                self.setup.append(self.associate(i,i+1,fuel,-1,None,True))
        self.tracks={};self.endpoints={};self.counts=dict(associate=0,catalytic=0,cleave=0,regenerate=0,diffuse=0,noop=0)
        self.depletion=dict(charged_zero=None,photons_zero=None)

    def word(self,key):return ''.join(str(self.s['bits'][a]) for a in self.s['objects'][str(key)]['atoms'])

    def birth(self,atoms,parents,step,site,assisted):
        key=self.s['next_id'];self.s['next_id']+=1
        self.s['objects'][str(key)]=dict(atoms=atoms,parents=parents,born=step,site=site,assisted=assisted)
        self.s['active'][str(key)]=site;return key

    def associate(self,left,right,fuel,step,catalyst,supplied=False):
        x,y=(self.s['objects'][str(k)] for k in (left,right));site=self.s['active'][str(left)]
        product=self.birth(x['atoms']+y['atoms'],[left,right],step,site,supplied or x['assisted'] or y['assisted'])
        for k in (left,right):del self.s['active'][str(k)]
        for k in fuel:self.s['tokens'][str(k)][1]=False
        self.s['heat']+=1;return ['associate',left,right,product,catalyst,fuel]

    def ids(self,collection,site,charge=None):
        result=[]
        for k,v in self.s[collection].items():
            location=v if collection=='active' else v[0]
            if (self.arm=='well-mixed' or location==site) and (charge is None or v[1]==charge):result.append(int(k))
        return sorted(result)

    def interpret(self,t,d):
        op,site=d[0]%4,d[1]%16;export=0
        if self.arm=='withdrawal' and t==4096:
            export=sum(self.s['photons']);self.s['exported']+=export;self.s['photons']=[0]*16
        result=['noop']; molecules=self.ids('active',site)
        if op==0:
            choices=[['object',k] for k in molecules]+[['token',k] for k in self.ids('tokens',site)]
            if choices:
                kind,key=choices[d[2]%len(choices)]; collection=self.s['active'] if kind=='object' else self.s['tokens']
                old=collection[str(key)] if kind=='object' else collection[str(key)][0]
                delta=((-1,0),(1,0),(0,-1),(0,1))[d[5]%4];new=((old//4+delta[1])%4)*4+(old%4+delta[0])%4
                if kind=='object':collection[str(key)]=new
                else:collection[str(key)][0]=new
                result=['diffuse',kind,key,old,new]
        elif op==1 and len(molecules)>1:
            left=molecules[d[2]%len(molecules)]; rest=[k for k in molecules if k!=left];right=rest[d[3]%len(rest)]
            eligible=[k for k in molecules if k not in (left,right) and len(self.s['objects'][str(k)]['atoms'])>1]
            cat=eligible[d[4]%len(eligible)] if eligible else None
            threshold=1
            if cat is not None:
                key='KINETIC01|'+str(self.seed)+'|'+self.word(cat)+'|'+self.word(left)+'|'+self.word(right)
                if hashlib.sha256(key.encode('utf-8')).digest()[0]<8 and self.arm!='inert':threshold=8
            price=self.ids('tokens',site,True)
            if len(self.word(left))+len(self.word(right))<=6 and len(price)>1 and d[6]%32<threshold:
                first=price[d[7]%len(price)];rest=[k for k in price if k!=first];second=rest[d[3]%len(rest)]
                result=self.associate(left,right,[first,second],t,cat if threshold==8 else None)
        elif op==2 and molecules:
            parent=molecules[d[2]%len(molecules)];old=self.s['objects'][str(parent)]
            if len(old['atoms'])>1 and d[6]%16==0:
                cut=1+d[5]%(len(old['atoms'])-1);site=self.s['active'].pop(str(parent))
                children=[]
                for atoms in (old['atoms'][:cut],old['atoms'][cut:]):children.append(self.birth(atoms,[parent],t,site,old['assisted']))
                self.s['heat']+=1;result=['cleave',parent,cut,children]
        elif op==3 and self.arm!='regeneration-off':
            spent=self.ids('tokens',site,False)
            if spent:
                token=spent[d[2]%len(spent)];where=self.s['tokens'][str(token)][0]
                if self.s['photons'][where]>1 and d[6]%2==0:
                    self.s['tokens'][str(token)][1]=True;self.s['photons'][where]-=2;self.s['heat']+=1;result=['regenerate',token,where]
        return [export,result]

    def conserve(self):
        atoms=[a for k in self.s['active'] for a in self.s['objects'][k]['atoms']]
        require(sorted(atoms)==list(range(96)),'Atom ownership/finite material')
        require(len(self.s['tokens'])==256 and all(0<=v[0]<16 and type(v[1]) is bool for v in self.s['tokens'].values()),'Fuel ownership')
        bonds=sum(len(self.s['objects'][k]['atoms'])-1 for k in self.s['active'])
        fuel=sum(v[1] for v in self.s['tokens'].values())
        require(fuel+sum(self.s['photons'])+bonds+self.s['heat']+self.s['exported']==768,'Energy/waste/full reaction price')
        require(all(0<=v for v in self.s['photons']) and all(1<=len(self.s['objects'][k]['atoms'])<=6 for k in self.s['active']),'Nonnegative finite stocks')

    def measure(self,t,event):
        kind=event[0];self.counts[kind]+=1
        if kind=='associate' and event[4] is not None:self.counts['catalytic']+=1
        if t>=4096:
            if kind=='associate':
                product,cat=event[3],event[4];word=self.word(product);obj=self.s['objects'][str(product)]
                if not obj['assisted']:
                    track=self.tracks.setdefault(word,dict(formation=[t,product]))
                    if 'loss' in track and cat is not None and 'reconstruction' not in track:
                        track['reconstruction']=[t,product,cat]
                if cat is not None:
                    word=self.word(cat);track=self.tracks.get(word)
                    if track and not self.s['objects'][str(cat)]['assisted']:
                        if 'first_use' not in track:track['first_use']=[t,cat,product]
                        if 'reconstruction' in track and cat==track['reconstruction'][1] and t>track['reconstruction'][0]:
                            self.endpoints.setdefault(word,dict(**track,subsequent_use=[t,cat,product]))
            elif kind=='cleave':
                word=self.word(event[1]);track=self.tracks.get(word)
                if track and 'first_use' in track and 'loss' not in track and not any(self.word(k)==word for k in self.s['active']):track['loss']=[t,event[1]]
        fuel=sum(v[1] for v in self.s['tokens'].values())
        if fuel==0 and self.depletion['charged_zero'] is None:self.depletion['charged_zero']=t
        if sum(self.s['photons'])==0 and self.depletion['photons_zero'] is None:self.depletion['photons_zero']=t


def world(folder):
    folder=Path(folder);initial=json.loads((folder/'initial.json').read_bytes())
    seed,arm,steps=initial['seed'],initial['arm'],initial['steps'];require(arm in ARMS and type(steps) is int and 0<steps<=8192,'Finite world request')
    model=Interpreter(seed,arm)
    require(canon(initial)==canon(dict(seed=seed,arm=arm,steps=steps,setup=model.setup,state=model.s)),'Full initial RNG/provenance/accounting')
    model.conserve(); count=0
    with (folder/'attempts.jsonl').open(encoding='utf-8') as stream:
        for t,line in enumerate(stream):
            raw=json.loads(line);draws=[model.random.getrandbits(16) for _ in range(8)]
            expected=model.interpret(t,draws);require(raw==[t,draws,expected],'Independent raw draw and causal transition')
            model.s['cursor']+=8;model.measure(t,expected[1]);count+=1
            if expected[1][0]!='noop':model.conserve()
    require(count==steps,'Full attempt denominator')
    model.s['rng']=model.random.getstate();require(canon(model.s)==canon(json.loads((folder/'final.json').read_bytes())),'Complete final state/ancestry/RNG cursor')
    return dict(seed=seed,arm=arm,steps=steps,endpoints=model.endpoints,endpoint_count=len(model.endpoints),counts=model.counts,depletion=model.depletion,
        final=dict(charged=sum(v[1] for v in model.s['tokens'].values()),waste=sum(not v[1] for v in model.s['tokens'].values()),photons=sum(model.s['photons']),heat=model.s['heat'],exported=model.s['exported']))


def audit(folder,source,revision):
    folder,source=Path(folder),Path(source);meta=json.loads((folder/'manifest.json').read_bytes())
    require(meta['schema']=='kinetic01-dynamics-v1' and meta['revision']==revision and meta['batch'] in range(4),'Pinned source/batch')
    require(meta['seeds']==list(range(43000+8*meta['batch'],43008+8*meta['batch'])) and meta['arms']==list(ARMS) and meta['steps']==8192,'Frozen full panel slots')
    require(meta['source_sha256']=={p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in FILES},'Full implemented source')
    files={p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    require(meta['files_sha256']==files,'Raw evidence bytes')
    require(meta['worlds']==[f'{seed}-{arm}' for seed in meta['seeds'] for arm in ARMS],'All unscreened worlds')
    rows=[world(folder/name) for name in meta['worlds']]
    return dict(schema='kinetic01-audit-v1',batch=meta['batch'],worlds=48,attempts=48*8192,rows=rows)


def decision(audits):
    require(sorted(a['batch'] for a in audits)==list(range(4)),'All four fixed batches')
    rows=[r for a in audits for r in a['rows']];require(len(rows)==192,'Full192 denominator')
    indexed={(r['seed'],r['arm']):r for r in rows};require(len(indexed)==192,'Unique paired worlds')
    deltas=[indexed[(s,'candidate')]['endpoint_count']-indexed[(s,'inert')]['endpoint_count'] for s in range(43000,43032)]
    wins=sum(x>0 for x in deltas);losses=sum(x<0 for x in deltas);n=wins+losses
    numerator=sum(math.comb(n,k) for k in range(wins,n+1));denominator=2**n
    frequency={a:sum(indexed[(s,a)]['endpoint_count']>0 for s in range(43000,43032)) for a in ARMS}
    return dict(schema='kinetic01-decision-v1',worlds=192,attempts=192*8192,frequency=frequency,paired_deltas=deltas,wins=wins,losses=losses,ties=32-n,
        sign_test=dict(numerator=numerator,denominator=denominator,p=numerator/denominator),positive_gate=frequency['candidate']>=8 and numerator/denominator<=0.05,
        reproduction_demonstrated=False,inheritance_demonstrated=False,adaptation_demonstrated=False,rows=rows)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);p.add_argument('--source-dir',required=True);p.add_argument('--source-revision',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    try:result=audit(a.output_dir,a.source_dir,a.source_revision)
    except (OSError,ValueError,KeyError,TypeError) as error:print('Rejected:',error);raise SystemExit(2)
    Path(a.report).write_text(canon(result)+'\n',encoding='utf-8',newline='\n');print(json.dumps(dict(batch=result['batch'],worlds=48,attempts=result['attempts'])))
