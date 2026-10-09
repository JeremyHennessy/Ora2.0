"""Independent GRADIENT-01 interpreter, accounting and productive-link assay."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random

ARMS=('candidate','ghost','free-transport','flattened','withdrawal','supplied-bonds')
FILES=('experiments/gradient_binding.py','experiments/gradient_binding_audit.py','docs/GRADIENT-01-PROTOCOL.md')
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def require(x,message):
    if not x:raise ValueError(message)


class Interpreter:
    def __init__(self,seed,arm,sites=None):
        self.arm=arm;self.rng=random.Random(seed)
        draws=[self.rng.getrandbits(16) for _ in range(64)];positions=sites if sites is not None else sorted(range(64),key=lambda k:(draws[k],k))[:48]
        self.pairs=[(i,j) for i in range(48) for j in range(i+1,48) if abs(positions[i]//8-positions[j]//8)+abs(positions[i]%8-positions[j]%8)==1]
        ranks=[self.rng.getrandbits(16) for _ in range(64)]
        self.s=dict(sites=positions,photons={i:[] for i in range(64)},q={i:[] for i in range(48)},energy={},next_energy=0,bonds={},active=[],next_bond=0,external=list(range(128)),exported=[],heat=0,cursor=128)
        for i in range(2048):self.s['photons'][i//32 if arm=='flattened' else (i//256)*8].append(i)
        self.setup=[]
        if arm=='supplied-bonds':
            indices=sorted(range(len(self.pairs)),key=lambda k:(ranks[k%64],self.pairs[k]))[:12]
            for i in indices:self.setup.append(self.apply(['external',list(self.pairs[i]),self.s['external'][:4]],-1))
        self.tracks={};self.endpoints={};self.counts={k:0 for k in ('capture','bind','unbind','transport','ghost','noop')};self.distal=0
        self.ever_charge=False;self.depletion=dict(charge_zero_after_positive=None,photons_zero=None)

    def snapshot(self):return dict(self.s,rng=self.rng.getstate())

    def two(self,ids,d):
        if len(ids)<2:return []
        first=ids[d[4]%len(ids)];others=[x for x in ids if x!=first];return [first,others[d[5]%len(others)]]

    def select(self,d):
        operation=d[0]%4
        if operation==0:
            atom=d[1]%48;return ['capture',atom,self.two(self.s['photons'][self.s['sites'][atom]],d)]
        if operation==1 and self.pairs:
            pair=list(self.pairs[d[1]%len(self.pairs)]);atom=pair[d[2]%2]
            return ['bind',pair,atom,self.two(self.s['q'][atom],d)] if d[3]%4==0 else ['noop']
        if operation==2 and self.s['active']:
            return ['unbind',self.s['active'][d[1]%len(self.s['active'])]] if d[3]%32==0 else ['noop']
        if operation==3:
            available=self.pairs if self.arm=='free-transport' else self.s['active']
            if available:
                chosen=available[d[1]%len(available)];bond=None if self.arm=='free-transport' else chosen
                pair=list(chosen) if bond is None else self.s['bonds'][bond]['pair'];sender=pair[d[2]%2];receiver=pair[1-d[2]%2]
                return ['transport',bond,sender,receiver,self.two(self.s['q'][sender],d)]
        return ['noop']

    def carrier(self,kind,parents,routes,assisted,t):
        key=self.s['next_energy'];self.s['next_energy']+=1;self.s['energy'][key]=dict(parents=parents,routes=routes,assisted=assisted,kind=kind,born=t);return key

    def apply(self,request,t):
        operation=request[0];s=self.s
        if operation=='capture':
            atom,inputs=request[1:];local=s['photons'][s['sites'][atom]]
            if len(inputs)==2 and len(set(inputs))==2 and len(s['q'][atom])<8 and all(p in local for p in inputs):
                for p in inputs:local.remove(p)
                key=self.carrier('capture',[['photon',p] for p in inputs],[],False,t);s['q'][atom].append(key);s['heat']+=1
                return ['capture',atom,inputs,key]
        elif operation in ('bind','external'):
            pair=request[1];payer=None if operation=='external' else request[2];inputs=request[2] if payer is None else request[3]
            stock=s['external'] if payer is None else s['q'][payer];price=4 if payer is None else 2
            possible=tuple(pair) in self.pairs and (payer is None or payer in pair) and not any(s['bonds'][i]['pair']==pair for i in s['active'])
            if possible and len(inputs)==len(set(inputs))==price and all(x in stock for x in inputs):
                for x in inputs:stock.remove(x)
                key=s['next_bond'];s['next_bond']+=1
                assisted=payer is None or any(s['energy'][x]['assisted'] for x in inputs)
                s['bonds'][key]=dict(pair=pair,payer=payer,paid=inputs,born=t,assisted=assisted);s['active'].append(key);s['heat']+=3 if payer is None else 1
                return ['bind',key]
        elif operation=='unbind' and request[1] in s['active']:
            s['active'].remove(request[1]);s['heat']+=1;return request
        elif operation=='transport':
            link,sender,receiver,inputs=request[1:]
            possible=tuple(sorted((sender,receiver))) in self.pairs if link is None and self.arm=='free-transport' else link in s['active'] and s['bonds'][link]['pair']==sorted((sender,receiver))
            if possible and len(inputs)==len(set(inputs))==2 and all(x in s['q'][sender] for x in inputs) and len(s['q'][receiver])<8:
                for x in inputs:s['q'][sender].remove(x)
                if self.arm=='ghost':s['heat']+=2;return ['ghost',link,sender,receiver,inputs]
                route=set()
                for x in inputs:route.update(tuple(r) for r in s['energy'][x]['routes'])
                if link is not None:route.add((link,t))
                assisted=any(s['energy'][x]['assisted'] for x in inputs) or (link is not None and s['bonds'][link]['assisted'])
                key=self.carrier('transport',[['carrier',x] for x in inputs],[list(x) for x in sorted(route)],assisted,t);s['q'][receiver].append(key);s['heat']+=1
                return ['transport',link,sender,receiver,inputs,key]
        return ['noop']

    def conserve(self):
        s=self.s;live=[k for ids in s['q'].values() for k in ids];photons=[k for ids in s['photons'].values() for k in ids]
        require(len(s['sites'])==len(set(s['sites']))==48,'48 immutable atoms')
        require(len(live)==len(set(live)) and all(k in s['energy'] for k in live) and all(len(v)<=8 for v in s['q'].values()),'Carrier ownership/capacity')
        require(len(photons)+len(s['exported'])==len(set(photons+s['exported'])) and all(0<=x<2048 for x in photons+s['exported']),'Photon ownership/export')
        require(len(s['external'])==len(set(s['external'])) and all(0<=x<128 for x in s['external']),'Finite external work')
        pairs=[s['bonds'][k]['pair'] for k in s['active']];require(len(pairs)==len({tuple(x) for x in pairs}),'No duplicate active link')
        require(all(sum(i in pair for pair in pairs)<=4 for i in range(48)),'Finite192 binding ports')
        require(len(live)+len(photons)+len(s['exported'])+len(s['external'])+len(pairs)+s['heat']==2176,'Complete energy/heat/endowment price')

    def measure(self,t,event):
        kind=event[0];self.counts[kind]+=1;s=self.s
        if kind=='bind':
            key=event[1];bond=s['bonds'][key]
            if bond['payer'] is not None and s['sites'][bond['payer']]%8>0:self.distal+=1
            if t>=8192 and not bond['assisted']:
                pair=':'.join(map(str,bond['pair']));old=self.tracks.get(pair)
                if old is None or ('loss' not in old and old['origin'] not in s['active']):self.tracks[pair]=dict(origin=key,formation=[t,key])
                old=self.tracks[pair]
                routes={tuple(r) for p in bond['paid'] for r in s['energy'][p]['routes']}
                if 'loss' in old and any(k!=old['origin'] and tick>old['loss'][0] and not s['bonds'][k]['assisted'] for k,tick in routes):old['replacement']=[t,key,bond['paid']]
                for name,track in self.tracks.items():
                    original=[r for r in routes if r[0]==track['origin'] and r[1]>=track['formation'][0]]
                    if original and 'first_use' not in track and track['origin'] in s['active']:track['first_use']=[min(original)[1],t,key,bond['paid']]
                    if 'replacement' in track:
                        new_tick,new_id,paid=track['replacement'];used=[r for r in routes if r[0]==new_id and r[1]>new_tick]
                        if used and key!=new_id:self.endpoints.setdefault(name,dict(**track,subsequent_use=[min(used)[1],t,key,bond['paid']]))
        elif kind=='unbind' and t>=8192:
            for track in self.tracks.values():
                if track['origin']==event[1] and 'first_use' in track and 'loss' not in track and t>track['first_use'][1]:track['loss']=[t,event[1]]
        charge=sum(len(v) for v in s['q'].values());self.ever_charge|=charge>0
        if charge==0 and self.ever_charge and self.depletion['charge_zero_after_positive'] is None:self.depletion['charge_zero_after_positive']=t
        if not any(s['photons'].values()) and self.depletion['photons_zero'] is None:self.depletion['photons_zero']=t


def world(folder):
    folder=Path(folder);initial=json.loads((folder/'initial.json').read_bytes());seed,arm,steps=(initial[k] for k in ('seed','arm','steps'))
    require(arm in ARMS and type(steps) is int and 0<steps<=16384,'Finite registered request')
    model=Interpreter(seed,arm);require(initial==json.loads(canon(dict(seed=seed,arm=arm,steps=steps,setup=model.setup,state=model.snapshot()))),'Exact initial unselected sites/stock/RNG/founders')
    model.conserve();count=0
    with (folder/'attempts.jsonl').open(encoding='utf-8') as stream:
        for t,line in enumerate(stream):
            d=[model.rng.getrandbits(16) for _ in range(8)];model.s['cursor']+=8;export=[]
            if arm=='withdrawal' and t==8192:
                export=sorted(x for stock in model.s['photons'].values() for x in stock);model.s['exported']+=export;model.s['photons']={i:[] for i in range(64)}
            request=model.select(d);event=model.apply(request,t)
            require(json.loads(line)==[t,d,[export,request,event]],'Independent request/transition/provenance');model.measure(t,event);count+=1
            if event[0]!='noop':model.conserve()
    require(count==steps,'Full attempt denominator')
    require(json.loads((folder/'final.json').read_bytes())==json.loads(canon(model.snapshot())),'Full immutable history/RNG/final ledger')
    return dict(seed=seed,arm=arm,steps=steps,endpoint_count=len(model.endpoints),endpoints=model.endpoints,counts=model.counts,distal_paid_bonds=model.distal,depletion=model.depletion,
        final=dict(charge=sum(len(v) for v in model.s['q'].values()),photons=sum(len(v) for v in model.s['photons'].values()),external=len(model.s['external']),exported=len(model.s['exported']),bonds=len(model.s['active']),heat=model.s['heat']),substrate_pairs=len(model.pairs))


def audit(folder,source,revision):
    folder,source=Path(folder),Path(source);m=json.loads((folder/'manifest.json').read_bytes())
    require(m['schema']=='gradient01-v1' and m['revision']==revision and m['batch'] in range(4),'Exact source/batch')
    require(m['seeds']==list(range(53000+8*m['batch'],53008+8*m['batch'])) and m['arms']==list(ARMS) and m['steps']==16384,'Frozen slots')
    require(m['source_sha256']=={p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in FILES},'Full law/protocol source')
    require(m['files_sha256']=={p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'},'Raw evidence hash')
    names=[f'{s}-{a}' for s in m['seeds'] for a in ARMS];require(m['worlds']==names,'Complete48 worlds')
    rows=[]
    for seed in m['seeds']:
        for arm in ARMS:
            row=world(folder/f'{seed}-{arm}');require((row['seed'],row['arm'],row['steps'])==(seed,arm,16384),'Exact per-world requested slots/denominator');rows.append(row)
    return dict(schema='gradient01-audit-v1',batch=m['batch'],worlds=48,attempts=48*16384,rows=rows)


def decision(reports):
    require(sorted(r['batch'] for r in reports)==list(range(4)),'Four fixed batches');rows=[x for r in reports for x in r['rows']];indexed={(r['seed'],r['arm']):r for r in rows}
    require(set(indexed)=={(s,a) for s in range(53000,53032) for a in ARMS} and len(rows)==192,'All unscreened samples')
    deltas=[indexed[(s,'candidate')]['endpoint_count']-indexed[(s,'ghost')]['endpoint_count'] for s in range(53000,53032)]
    wins=sum(x>0 for x in deltas);losses=sum(x<0 for x in deltas);n=wins+losses;num=sum(math.comb(n,k) for k in range(wins,n+1));den=2**n
    frequency={a:sum(indexed[(s,a)]['endpoint_count']>0 for s in range(53000,53032)) for a in ARMS};distal={a:sum(indexed[(s,a)]['distal_paid_bonds'] for s in range(53000,53032)) for a in ARMS}
    return dict(schema='gradient01-decision-v1',worlds=192,attempts=192*16384,frequency=frequency,paired_deltas=deltas,wins=wins,losses=losses,ties=32-n,sign_test=dict(numerator=num,denominator=den,p=num/den),positive_gate=frequency['candidate']>=8 and num/den<=0.05,distal_paid_bonds=distal,bound_network_necessity_rejected=distal['free-transport']>=distal['candidate'],life_demonstrated=False,reproduction_demonstrated=False,adaptation_demonstrated=False,rows=rows)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);p.add_argument('--source-dir',required=True);p.add_argument('--source-revision',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    try:result=audit(a.output_dir,a.source_dir,a.source_revision)
    except (ValueError,OSError,KeyError,TypeError) as error:print('Rejected:',error);raise SystemExit(2)
    Path(a.report).write_text(canon(result)+'\n',encoding='utf-8',newline='\n');print(json.dumps(dict(batch=result['batch'],worlds=48,attempts=result['attempts'])))
