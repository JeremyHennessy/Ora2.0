"""DIGITAL-ECOSYSTEM-01. Inert integer VM; supplied ancestor, no host-call ISA."""
import hashlib
import json

ANCESTOR=[1,2,4,5,6,12]
MODES=('mutating','faithful','copy_disabled')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class World:
    def __init__(self, seed, mode='mutating'):
        if type(seed) is not int or seed<0 or mode not in MODES:raise ValueError('Invalid world')
        self.seed=seed;self.mode=mode;self.tick=0;self.last=-1;self.next_id=1
        self.food={i:[i//16,int(digest([seed,'food',i])[:8],16)%2] for i in range(64)}
        self.free=list(range(14,512));self.heat=0;self.writes=0
        self.entities={0:self.entity(0,None,0,[[v,i] for i,v in enumerate(ANCESTOR)],list(range(6,14)),12,0)}
        self.events=[];self.births=0;self.deaths=0;self.max_population=1
        self.check()

    @staticmethod
    def entity(identity,parent,generation,code,units,energy,pos):
        return dict(id=identity,parent=parent,generation=generation,code=code,mem=[0]*8,mem_units=units,
                    energy=energy,pos=pos,pc=0,r0=0,r1=0,read=0,nursery=[],inbox=None)

    def check(self):
        units=list(self.free)
        for e in self.entities.values():
            units.extend(g[1] for g in e['code']);units.extend(e['mem_units']);units.extend(g[1] for g in e['nursery'])
            assert 0<=e['energy']<=64 and len(e['mem'])==len(e['mem_units'])==8
            assert len(e['code'])==6 and all(type(g[0]) is int and 0<=g[0]<16 for g in e['code'])
            assert 0<=e['pos']<4 and 0<=e['pc']<6 and 0<=e['read']<=6
        assert sorted(units)==list(range(512)) and len(self.entities)<=32
        assert sum(e['energy'] for e in self.entities.values())+20*len(self.food)+self.heat==1292

    def step(self):
        if not self.entities:return False
        ids=sorted(self.entities);actor=next((i for i in ids if i>self.last),ids[0]);self.last=actor
        e=self.entities[actor];self.tick+=1
        op=e['code'][e['pc']][0];event=dict(tick=self.tick,actor=actor,op=op,pc=e['pc'],r0=e['r0'],r1=e['r1'],energy_before=e['energy'],outcome='executed')
        if e['energy']<1:raise AssertionError('Dead actor scheduled')
        e['energy']-=1;self.heat+=1;e['pc']=(e['pc']+1)%6
        neighbors=[self.entities[i] for i in ids if i!=actor and self.entities[i]['pos']==e['pos']]
        if op==1:
            local=[i for i,v in self.food.items() if v[0]==e['pos']]
            e['r0']=self.food[min(local)][1] if local else 2
            event['cue']=e['r0']
        elif op==2:
            found=[i for i,v in self.food.items() if v==[e['pos'],e['r0']%2]]
            e['r1']=int(bool(found))
            if found:
                i=min(found);event['food']=i;del self.food[i]
                gain=min(20,64-e['energy']);e['energy']+=gain;self.heat+=20-gain
        elif op==3:e['pos']=(e['pos']+(1 if e['r0']%2 else -1))%4
        elif op==4:
            if self.mode!='copy_disabled' and e['read']<6 and self.free and e['energy']>=1:
                source=e['code'][e['read']];value=source[0]
                draw=int(digest([self.seed,'mutation',self.writes])[:16],16)
                if self.mode=='mutating' and draw%100<8:value=(value+1+(draw//100)%15)%16
                unit=self.free.pop(0);self.writes+=1;e['energy']-=1;self.heat+=1
                write=[value,unit,e['read'],len(self.events)]
                e['nursery'].append(write);event['write']=dict(source=list(source),destination=unit,index=e['read'],opcode=value,event_id=len(self.events),mutated=value!=source[0]);e['read']+=1
            else:event['outcome']='copy_refused'
        elif op==5:
            if e['read']<6:e['pc']=0
        elif op==6:
            if len(e['nursery'])==6 and e['energy']>=22 and len(self.free)>=8 and len(self.entities)<32:
                child=self.next_id;self.next_id+=1;units=self.free[:8];del self.free[:8]
                code=[[g[0],g[1]] for g in e['nursery']]
                daughter=self.entity(child,actor,e['generation']+1,code,units,12,e['pos'])
                event['birth']=dict(child=json.loads(json.dumps(daughter)),write_events=[g[3] for g in e['nursery']])
                self.entities[child]=daughter;e['energy']-=22;self.heat+=10;e['nursery']=[];e['read']=0;self.births+=1
            else:event['outcome']='division_refused'
        elif op==7:e['mem'][e['r0']%8]=e['r1']%16
        elif op==8:e['r0']=e['mem'][e['r1']%8]
        elif op==9:
            if e['energy']>=1:
                index=e['r0']%6;old=e['code'][index][0];new=e['r1']%16
                e['code'][index][0]=new;e['energy']-=1;self.heat+=1
                event['self_write']=dict(index=index,old=old,new=new,unit=e['code'][index][1])
        elif op==10:
            if neighbors and neighbors[0]['inbox'] is None:
                neighbors[0]['inbox']=e['r1']%16;event['message']=dict(recipient=neighbors[0]['id'],value=e['r1']%16)
        elif op==11:
            if e['inbox'] is not None:e['r0']=e['inbox'];e['inbox']=None
        elif op==12:e['pc']=0
        elif op==13:e['r0']=(e['r0']+1)%16
        elif op==14:
            if neighbors and e['energy']>=1 and neighbors[0]['energy']<64:
                e['energy']-=1;neighbors[0]['energy']+=1;event['transfer']=neighbors[0]['id']
        elif op==15:
            self.heat+=e['energy'];e['energy']=0;event['outcome']='halt'
        if e['energy']==0:
            units=[g[1] for g in e['code']]+e['mem_units']+[g[1] for g in e['nursery']]
            self.free=sorted(self.free+units);del self.entities[actor];self.deaths+=1;event['death']=units
        else:
            event['actor_after']=dict(energy=e['energy'],pc=e['pc'],pos=e['pos'],r0=e['r0'],r1=e['r1'],read=e['read'],program_hash=digest(e['code']),genome_hash=digest([g[0] for g in e['code']]),memory_hash=digest(e['mem']))
        self.max_population=max(self.max_population,len(self.entities));self.check()
        event['ledger']=dict(live_energy=sum(o['energy'] for o in self.entities.values()),food=len(self.food),heat=self.heat,free=len(self.free),population=len(self.entities))
        self.events.append(event);return True

    def snapshot(self):
        return json.loads(json.dumps(self.__dict__,sort_keys=True))

    @classmethod
    def restore(cls,state):
        x=cls.__new__(cls);x.__dict__.update(json.loads(json.dumps(state)))
        x.food={int(k):v for k,v in x.food.items()};x.entities={int(k):v for k,v in x.entities.items()}
        x.check();return x

    def run(self,horizon=256):
        if type(horizon) is not int or not 0<=horizon<=4096:raise ValueError('Finite horizon required')
        while self.tick<horizon and self.step():pass
        return dict(seed=self.seed,mode=self.mode,ticks=self.tick,births=self.births,deaths=self.deaths,maximum_population=self.max_population,
                    events=self.events,final=self.snapshot(),state_hash=digest(self.snapshot()),ancestor_supplied=True,learning_demonstrated=False)


def study():
    rows=[]
    for seed in range(24000,24004):
        for mode in MODES:
            w=World(seed,mode)
            while w.tick<64 and w.step():pass
            checkpoint=w.snapshot();resumed=World.restore(checkpoint)
            result=w.run();assert result==resumed.run()
            result['checkpoint_replay']=True;rows.append(result)
    return dict(schema='digital-ecosystem01-v1',rows=rows,controller_activated=False,persistent_world=False)


if __name__=='__main__':print(json.dumps(study(),sort_keys=True,separators=(',',':')))
