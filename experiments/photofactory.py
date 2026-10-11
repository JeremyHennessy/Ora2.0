"""Source-to-work controlled feasibility, not autonomous action selection."""
import hashlib
import itertools
import json
import sys

ROLES=('C','H','F','S','L')


class Fixture:
    def __init__(self,name,engines,fabricator=False,disabled=False):
        self.name=name;self.n=engines;self.fabricator=fabricator;self.disabled=disabled
        self.events=[];self.active={};self.next_energy=0;self.next_component=0
        self.raw=set(range(20));self.parts={};self.banks=[[] for _ in range(engines)]
        self.photons=[[] for _ in range(engines)];self.tester=[];self.epoch=-1
        self.loads=0;self.bills=[]
        self.tester=self.emit('tester',[],[('t',20)])

    def emit(self,op,inputs,outputs,**fields):
        if len(set(inputs))!=len(inputs) or any(i not in self.active for i in inputs):
            raise ValueError('Consumed or duplicate energy identity')
        if op not in ('tester','feed') and len(inputs)!=sum(n for _,n in outputs):
            raise ValueError('Unit energy conservation')
        for i in inputs:del self.active[i]
        ids=[]
        for kind,count in outputs:
            for _ in range(count):
                i=self.next_energy;self.next_energy+=1;ids.append(i)
                self.active[i]=(kind,self.epoch)
        self.events.append(dict(op=op,phase=self.epoch,inputs=inputs,
                                outputs=[[k,n] for k,n in outputs],**fields))
        return ids

    def take(self,engine,count):
        if len(self.photons[engine])<count:raise ValueError('No source top-up')
        values=self.photons[engine][:count];del self.photons[engine][:count]
        return values

    def required(self,engine,roles):
        for role in roles:
            p=self.parts.get((engine,role))
            if not p or not p['working'] or p['maintained']!=self.epoch:
                raise ValueError('Unformed, broken or unpaid apparatus')

    def form(self,engine,role,route):
        if (engine,role) in self.parts:raise ValueError('Occupied device position')
        mat=[4*ROLES.index(role)+2*engine+i for i in range(2)]
        if any(i not in self.raw for i in mat):raise ValueError('Locked material')
        if route=='photo':inputs=self.take(engine,3);heat=2;cost=3
        elif route=='fabricate':
            self.required(engine,('C','H','F'))
            if self.disabled:raise ValueError('Disabled fabricator')
            if len(self.banks[engine])<2:raise ValueError('No private fabrication charge')
            inputs=self.banks[engine][:2];del self.banks[engine][:2]
            heat=1;cost=4 # Both carriers have paid two-photon capture ancestry.
        else:raise ValueError('Unknown formation route')
        cid=self.next_component;self.next_component+=1
        ids=self.emit(route,inputs,[('b',1),('h',heat)],engine=engine,role=role,
                      component=cid,material=mat)
        self.raw.difference_update(mat)
        self.parts[engine,role]=dict(component=cid,potential=ids[0],material=mat,
                                    working=True,maintained=-1)
        self.bills[self.epoch]['formation']+=cost

    def upkeep(self,engine,role):
        p=self.parts[engine,role]
        if not p['working'] or p['maintained']==self.epoch:raise ValueError('Invalid upkeep')
        self.emit('upkeep',self.take(engine,1),[('h',1)],engine=engine,role=role,
                  component=p['component'])
        p['maintained']=self.epoch;self.bills[self.epoch]['upkeep']+=1

    def capture(self,engine):
        self.required(engine,('C','H'))
        capacity=2
        p=self.parts.get((engine,'S'))
        if p and p['working'] and p['maintained']==self.epoch:capacity=6
        if len(self.banks[engine])>=capacity:raise ValueError('Finite carrier capacity')
        ids=self.emit('capture',self.take(engine,2),[('c',1),('h',1)],engine=engine)
        self.banks[engine].append(ids[0])

    def load(self,engine):
        self.required(engine,('C','H','S','L'))
        if len(self.banks[engine])<4 or self.loads+2>1200:raise ValueError('Unfunded load')
        inputs=self.banks[engine][:4];del self.banks[engine][:4]
        self.emit('load',inputs,[('w',2),('h',2)],engine=engine,
                  loads=[self.loads,self.loads+1])
        self.loads+=2;self.bills[self.epoch]['work']+=2

    def damage(self):
        for (engine,role),p in sorted(self.parts.items()):
            if not p['working']:raise ValueError('Duplicate damage')
            token=self.tester.pop(0)
            self.emit('damage',[token],[('h',1)],engine=engine,role=role,
                      component=p['component'])
            p['working']=False

    def release(self,engine,role):
        p=self.parts[engine,role]
        if p['working']:raise ValueError('No free release of working apparatus')
        self.emit('release',self.take(engine,2)+[p['potential']],[('h',3)],
                  engine=engine,role=role,component=p['component'],material=p['material'])
        self.raw.update(p['material']);del self.parts[engine,role]
        self.bills[self.epoch]['release']+=2

    def execute(self):
        for phase in range(3):
            self.epoch=phase;self.bills.append(dict(formation=0,upkeep=0,release=0,work=0))
            for e in range(self.n):
                self.photons[e]=self.emit('feed',[],[('p',576//self.n)],engine=e)
            if phase:
                for e,r in sorted(list(self.parts)):self.release(e,r)
            for e in range(self.n):
                if self.fabricator:
                    for r in ('C','H','F'):self.form(e,r,'photo');self.upkeep(e,r)
                    for r in ('S','L'):
                        if self.disabled:self.form(e,r,'photo')
                        else:
                            self.capture(e);self.capture(e);self.form(e,r,'fabricate')
                        self.upkeep(e,r)
                else:
                    for r in ('C','H','S','L'):self.form(e,r,'photo');self.upkeep(e,r)
                while len(self.photons[e])>=2:
                    self.capture(e)
                    if len(self.banks[e])>=4:self.load(e)
                residual=self.photons[e]+self.banks[e]
                self.emit('expiry',residual,[('h',len(residual))],engine=e)
                self.photons[e]=[];self.banks[e]=[]
            if phase<2:self.damage()
        totals={k:sum(x[k] for x in self.bills) for k in self.bills[0]}
        payback=totals['work']-sum(totals[k] for k in ('formation','upkeep','release'))
        return dict(name=self.name,engines=self.n,events=self.events,
                    epoch_bills=self.bills,totals=totals,payback=payback,
                    assistance_work=20-len(self.tester),
                    assistance_inclusive_payback=payback-(20-len(self.tester)))


def experiment():
    runs=[Fixture('candidate',1,True).execute(),Fixture('stationary',1).execute(),
          Fixture('independent',2).execute(),Fixture('fabricator_disabled',1,True,True).execute()]
    canonical=json.dumps(runs[0]['events'],sort_keys=True,separators=(',',':')).encode()
    # Exact trace quotient: anonymous-position permutations do not change any
    # role, material, energy identity or transition under the registered law.
    shuffle=[dict(layout=list(p),trace_sha256=hashlib.sha256(canonical).hexdigest(),
                  payback=runs[0]['payback']) for p in itertools.permutations(range(5))]
    return dict(schema='photofactory01-v1',runs=runs,shuffle_cases=shuffle,
                scheduling='CONTROLLED_ASSISTANCE_NOT_AUTONOMY',
                scheduling_cost='UNKNOWN',mechanism_admitted=False,natural_worlds=0)


if __name__=='__main__':
    from pathlib import Path
    data=json.dumps(experiment(),sort_keys=True,separators=(',',':')).encode()
    if len(data)>4*1024**2:raise ValueError('Registered file cap')
    with Path(sys.argv[1]).open('wb') as out:
        if out.write(data)!=len(data):raise OSError('Partial evidence write')
    print(json.dumps(dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())))
