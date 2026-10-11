"""Prospective task kernel only; no organism controller or ecosystem activation."""
import hashlib,json

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class Task:
    def __init__(self,orientation,mode='normal',flip=32):
        assert type(orientation) is int and orientation in (0,1)
        assert mode in ('normal','memory_disabled') and type(flip) is int and flip==32
        self.initial=orientation;self.mode=mode;self.flip=flip
        self.energy=12;self.heat=0;self.memory=[0]*8;self.food=list(range(64))
        self.index=0;self.events=[];self.cost=0;self.alive=True

    def step(self,op,arg=None):
        assert op in ('sense','read','write','act')
        if op=='read':assert type(arg) is int and 0<=arg<8
        if op=='write':assert isinstance(arg,list) and len(arg)==2 and all(type(x) is int for x in arg) and 0<=arg[0]<8 and 0<=arg[1]<16
        if op=='act':assert type(arg) is int and arg in (0,1)
        if op=='sense':assert arg is None
        if not self.alive or len(self.events)>=256 or (self.index>=64 and op in ('sense','act')):return None
        self.energy-=1;self.heat+=1;self.cost+=1
        out=None;food=None
        if op=='sense':out=self.index%2
        elif op=='read':out=self.memory[arg] if self.mode=='normal' else 0
        elif op=='write':self.memory[arg[0]]=arg[1] if self.mode=='normal' else 0
        else:
            target=(self.index%2)^self.initial^int(self.index>=self.flip)
            out=int(arg==target)
            if out:
                food=self.index;self.food.remove(food)
                gained=min(20,64-self.energy);self.energy+=gained;self.heat+=20-gained
            self.index+=1
        if self.energy==0:self.alive=False
        self.events.append(dict(tick=len(self.events),op=op,arg=arg,out=out,food=food,
                                index=self.index,energy=self.energy,heat=self.heat,
                                memory_hash=digest(self.memory),alive=self.alive))
        assert self.energy+self.heat+20*len(self.food)==1292
        return out

    def record(self):
        final=dict(index=self.index,energy=self.energy,heat=self.heat,memory=self.memory,
                   food=self.food,cost=self.cost,alive=self.alive)
        return dict(orientation=self.initial,mode=self.mode,flip=self.flip,events=self.events,
                    final=final,state_hash=digest(final),supplied='Scripted software measurement witness; no organism policy')
