"""OneShot77: prospective one-shot task on the same paid VM."""
import base64,hashlib,json,zlib

VERSION='DIGITAL-ONESHOT77-WORLD-v1'
from experiments.digital_oneshot77_source import programmes,OPS,PRIMARY,UNSEEN,SOFTWARE
from experiments.digital_oneshot77_controls import Control,MODES as CONTROL_MODES
PROGRAMS=programmes()

MODES=('faithful',)

def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def clone(x):return json.loads(json.dumps(x))

def state_types(x,key=None):
    if key=='mutated':assert type(x) is bool
    elif isinstance(x,dict):
        for k,v in x.items():state_types(v,k)
    elif isinstance(x,list):
        for v in x:state_types(v)
    else:assert x is None or type(x) in (int,str)

class World:
    def __init__(self,seed,mode='faithful',route='supplied_cognitive',control='intact'):
        assert type(seed) is int and seed in PRIMARY+UNSEEN+SOFTWARE and mode=='faithful' and route in PROGRAMS and control in CONTROL_MODES
        self.control_mode=control;self._origin=None
        self.seed=seed;self.mode=mode;self.tick=0;self.last=-1;self.next_id=1;self.writes=0
        code=sum(PROGRAMS[route],[]);bill=len(code)+16
        self.constructor_remaining=128-bill-32;self.heat=bill
        self.startup=dict(energy=32,assistance='supplied paid common endowment')
        self.formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(code+[0]*16)]
        self.food={i:[0 if i<32 else 1+(i-32)//16,int(h([seed,'food',i])[:8],16)%2] for i in range(64)}
        for segment in (0,1):
            self.food[16*segment][1]=seed%2;self.food[16*segment+1][1]=(seed%2)^1
            order=sorted(range(2,16),key=lambda i:h([seed,'oneshot77-cue-order',segment,i]))
            for rank,index in enumerate(order):self.food[16*segment+index][1]=int(rank>=7)
        self.free=list(range(bill,512));self.entities={0:self.body(0,None,0,[[v,i] for i,v in enumerate(code)],list(range(len(code),bill)),0)}
        self.events=[];self.births=0;self.deaths=0;self.maximum=1;self.check()
        self._control=Control(PROGRAMS[route],self._local(self.entities[0]),control,seed)

    @staticmethod
    def body(identity,parent,generation,code,units,pos):
        return dict(id=identity,parent=parent,generation=generation,code=code,state_units=units,
                    memory=[0]*8,registers=[0,0],pc=0,cue=0,feedback=0,inbox=None,pos=pos,
                    energy=32,nursery=[])

    def check(self):
        units=self.free[:]
        for e in self.entities.values():
            units += [v[1] for v in e['code']]+e['state_units']+[v['unit'] for v in e['nursery']]
            assert 3<=len(e['code'])<=96 and len(e['code'])%3==0 and len(e['state_units'])==16
            assert all(type(v[0]) is int and 0<=v[0]<32 for v in e['code'])
            assert len(e['memory'])==8 and all(type(v) is int and 0<=v<16 for v in e['memory']+e['registers'])
            assert 0<=e['pc']<len(e['code'])//3 and 0<=e['pos']<4 and 0<e['energy']<=64
            assert len(e['nursery'])%3==0 and len(e['nursery'])<=len(e['code'])
        assert sorted(units)==list(range(512)) and len(self.entities)<=32
        assert sum(e['energy'] for e in self.entities.values())+self.constructor_remaining+self.heat+20*len(self.food)==1408

    def _native_step(self):
        if not self.entities:return False
        ids=sorted(self.entities);actor=next((i for i in ids if i>self.last),ids[0]);self.last=actor
        e=self.entities[actor];self.tick+=1;n=len(e['code'])//3
        release=None
        if self.tick==64:
            assert self.constructor_remaining>=16
            self.constructor_remaining-=16;self.heat+=16
            release=dict(packets=list(range(16,32)),energy=16,assistance='supplied exogenous stock boundary')
        opcode,a,b=[v[0] for v in e['code'][3*e['pc']:3*e['pc']+3]]
        assert opcode in OPS
        event=dict(tick=self.tick,actor=actor,decoded=[opcode,a,b],before=h(e),outcome='executed')
        if release:event['release']=release
        e['energy']-=1;self.heat+=1;e['pc']=(e['pc']+1)%n
        reg=e['registers'];neighbors=[self.entities[i] for i in ids if i!=actor and self.entities[i]['pos']==e['pos']]
        local=sorted(i for i,v in self.food.items() if v[0]==e['pos'] and (not 16<=i<32 or self.tick>=64))
        if opcode==0:
            e['cue']=self._present()[1];reg[a%2]=e['cue'];event['cue']=e['cue'];event['sensor_packet']=local[0] if local else None
        elif opcode==1:reg[a%2]=e['feedback']
        elif opcode==2:reg[a%2]=e['memory'][b%8]
        elif opcode==3:e['memory'][a%8]=reg[b%2]
        elif opcode==4:reg[a%2]=b%16
        elif opcode==5:reg[a%2]^=reg[b%2]
        elif opcode==6:
            e['feedback']=2;event['penalty']=0
            if local:
                packet=local[0];position,kind=self.food[packet];target=self._target(packet,kind)
                e['feedback']=int(reg[a%2]%2==target)
                event['attempt']=dict(packet=packet,position=position,cue=kind,port=reg[a%2]%2,target=target,success=e['feedback'])
                del self.food[packet]
                if e['feedback']:
                    gain=min(20,64-e['energy']);e['energy']+=gain;self.heat+=20-gain
                    event['packet_outflow']=dict(packet=packet,energy=20,captured=gain,heat=20-gain)
                else:
                    self.heat+=20
                    event['packet_outflow']=dict(packet=packet,energy=20,captured=0,heat=20)
                    penalty=min(4,e['energy']);e['energy']-=penalty;self.heat+=penalty;event['penalty']=penalty
            event['feedback']=e['feedback']
        elif opcode==7:e['pc']=b%n
        elif opcode==8:
            if reg[a%2]==0:e['pc']=b%n
        elif opcode==9:
            address=b%len(e['code']);old=e['code'][address][0];e['code'][address][0]=reg[a%2]
            event['self_write']=dict(unit=e['code'][address][1],index=address,old=old,value=reg[a%2])
        elif opcode==10:
            if self.mode!='copy_disabled' and len(e['nursery'])<len(e['code']) and len(self.free)>=3 and e['energy']>=3:
                writes=[]
                for index in range(len(e['nursery']),len(e['nursery'])+3):
                    source=e['code'][index];value=source[0];draw=int(h([self.seed,'mutation',self.writes])[:16],16)
                    if self.mode=='mutating' and draw%100<8:value=(value+1+(draw//100)%31)%32
                    unit=self.free.pop(0)
                    write=dict(unit=unit,value=value,index=index,tick=self.tick,source_unit=source[1],source_value=source[0],write_id=self.writes,mutated=value!=source[0])
                    self.writes+=1;e['nursery'].append(write);writes.append(clone(write))
                e['energy']-=3;self.heat+=3;event['writes']=writes
            else:event['outcome']='copy_refused'
        elif opcode==11:
            if len(e['nursery'])<len(e['code']):e['pc']=b%n
        elif opcode==12:
            if len(e['nursery'])==len(e['code']) and e['energy']>=30 and len(self.free)>=16 and len(self.entities)<32:
                child=self.next_id;self.next_id+=1;units=self.free[:16];del self.free[:16]
                daughter=self.body(child,actor,e['generation']+1,[[w['value'],w['unit']] for w in e['nursery']],units,e['pos'])
                event['birth']=dict(child=clone(daughter),write_ids=[w['write_id'] for w in e['nursery']],state_formation=[dict(unit=u,value=e['pos'] if i==14 else 0,energy=1) for i,u in enumerate(units)],release_energy=2,startup_energy=12)
                self.entities[child]=daughter;e['energy']-=30;self.heat+=18;e['nursery']=[];self.births+=1
            else:event['outcome']='division_refused'
        elif opcode==13:e['pos']=(e['pos']+(1 if reg[a%2]%2 else -1))%4
        elif opcode==14:
            if neighbors and neighbors[0]['inbox'] is None:
                neighbors[0]['inbox']=reg[a%2];event['message']=dict(recipient=neighbors[0]['id'],value=reg[a%2])
        elif opcode==15:
            if e['inbox'] is not None:reg[a%2]=e['inbox'];e['inbox']=None
        elif opcode==16:
            if neighbors and e['energy']>=1 and neighbors[0]['energy']<64:e['energy']-=1;neighbors[0]['energy']+=1;event['transfer']=neighbors[0]['id']
        elif opcode==17:self.heat+=e['energy'];e['energy']=0;event['outcome']='halt'
        elif opcode==19:reg[a%2]=e['memory'][reg[b%2]%8]
        elif opcode==20:e['memory'][reg[a%2]%8]=reg[b%2]
        elif opcode==21:reg[a%2]^=15
        if e['energy']==0:
            released=[v[1] for v in e['code']]+e['state_units']+[w['unit'] for w in e['nursery']]
            self.free=sorted(self.free+released);del self.entities[actor];self.deaths+=1;event['death']=released
        else:event['after']=clone(e)
        self.maximum=max(self.maximum,len(self.entities));self.check()
        event['state_hash']=h(self.snapshot(include_events=False));self.events.append(event);return True

    def snapshot(self,include_events=True):
        return clone({k:v for k,v in self.__dict__.items() if not k.startswith('_') and (include_events or k!='events')})

    def run(self,horizon):
        assert type(horizon) is int and 0<=horizon<=512
        while self.tick<horizon and self.step():pass
        return self.snapshot()

    @staticmethod
    def _local(e):return dict(r=e['registers'][:],m=e['memory'][:],pc=e['pc'],feedback=e['feedback'])

    def _present(self,next_tick=None):
        tick=self.tick if next_tick is None else next_tick
        available=sorted(i for i,v in self.food.items() if v[0]==0 and (not 16<=i<32 or tick>=64))
        return (available[0],self.food[available[0]][1]) if available else (None,0)

    def _target(self,packet,kind):
        assert 0<=packet<32 and kind in (0,1)
        if self.seed in SOFTWARE:return (self.seed%2)^int(packet>=16)
        index=(self.seed-(PRIMARY[0] if self.seed in PRIMARY else UNSEEN[0]))//2
        target=(index>>1)&1 if kind==0 else index&1
        return target^int(packet>=16)

    def step(self):
        if not self.entities or not any(v[0]==0 for v in self.food.values()):return False
        assert set(self.entities)=={0};e=self.entities[0]
        assert e['inbox'] is None and e['pos']==0 and not e['nursery']
        assert [v[0] for v in e['code']]==sum(self._control.code,[])
        before=self._local(e);cue=self._present(self.tick+1)[1]
        assert self._native_step();event=self.events[-1];native=self._local(e)
        updated,annotation=self._control.apply(before,native,current_cue=cue)
        sample=None
        if event['decoded'][0]==1:
            sample=dict(read_index=self._control.reads,own_source_tick=self._origin,original=native['r'][event['decoded'][1]%2],value=updated['r'][event['decoded'][1]%2])
        if event['decoded'][0]==6:self._origin=event['tick'] if 'attempt' in event else None
        annotation['personal_read']=sample;annotation['latest_own_source_tick']=self._origin
        event['control']=annotation
        e['registers']=updated['r'];e['memory']=updated['m'];e['pc']=updated['pc']
        assert e['feedback']==updated['feedback']
        if 'after' in event:event['after']=clone(e)
        self.check();event['state_hash']=h(self.snapshot(False));return True
