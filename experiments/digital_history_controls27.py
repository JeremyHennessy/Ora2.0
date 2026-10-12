"""External causal-control admission adapter; frozen Exposure23 laws unchanged."""
import base64,json,zlib
from . import digital_informative_exposure23 as law
from .digital_candidate_admission26 import install_registry
from .digital_neutral_catalogue25 import candidate

VERSION='DIGITAL-HISTORY-CONTROLS-27-v1'
CONTROLS=('intact','retained_disabled','own_disrupted')
CONTROL='intact'

class Control:
    """Operator sidecar, not entity memory or an installed successful policy."""
    def __init__(self,mode,seed):
        assert mode in CONTROLS
        self.mode=mode;self.seed=seed;self.sr=[0,0];self.sm=[0]*8
        self.tr=[set(),set()];self.tm=[set() for _ in range(8)]
        self.origin=None;self.reads=0

    def apply(self,e,event):
        op,a,b=event['decoded'];assert op in (1,2,3,4,5,6,7,18)
        a2,b2,a8,b8=a%2,b%2,a%8,b%8;substitution=None;rewrites=[]
        if op==1:
            self.reads+=1;original=e['registers'][a2]
            value=int(law.h([self.seed//2,'own-disrupt27',self.reads])[:8],16)%2 if self.mode=='own_disrupted' else original
            e['registers'][a2]=value;self.sr[a2]=0
            self.tr[a2]={-self.reads} if self.mode=='own_disrupted' else {self.origin} if self.origin is not None else set()
            substitution=dict(register=a2,original=original,value=value,own_source_tick=self.origin,read_index=self.reads)
        elif op==2:self.sr[a2]=self.sm[b8];self.tr[a2]=set(self.tm[b8])
        elif op==3:self.sm[a8]=self.sr[b2];self.tm[a8]=set(self.tr[b2])
        elif op==4:self.sr[a2]=b%16;self.tr[a2]=set()
        elif op==5:self.sr[a2]^=self.sr[b2];self.tr[a2]|=self.tr[b2]
        elif op==6:
            self.origin=event['tick'] if 'attempt' in event else None
            if self.mode=='retained_disabled':
                for channel,values,shadow,tags in (('register',e['registers'],self.sr,self.tr),('memory',e['memory'],self.sm,self.tm)):
                    for i,origins in enumerate(tags):
                        if origins:
                            rewrites.append(dict(channel=channel,index=i,original=values[i],value=shadow[i],origins=sorted(origins)))
                            values[i]=shadow[i];tags[i]=set()
        return dict(mode=self.mode,source_tick=self.origin,read_count=self.reads,shadow_registers=self.sr[:],shadow_memory=self.sm[:],register_tags=[sorted(t) for t in self.tr],memory_tags=[sorted(t) for t in self.tm],substitution=substitution,rewrites=rewrites)

class World(law.World):
    def __init__(self,seed,mode='faithful',route='alternating'):
        self._control=Control(CONTROL,seed)
        super().__init__(seed,mode,route)

    def snapshot(self,include_events=True):
        return law.clone({k:v for k,v in self.__dict__.items() if not k.startswith('_') and (include_events or k!='events')})

    def step(self):
        if not self.entities:return False
        assert set(self.entities)=={0};e=self.entities[0]
        assert e['inbox'] is None and e['pos']==0
        assert super().step()
        event=self.events[-1];event['control']=self._control.apply(e,event)
        if 'after' in event:event['after']=law.clone(e)
        self.check();event['state_hash']=law.h(self.snapshot(False));return True

def history(seed,role,route):
    world=World(seed,'faithful',route)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot();restored=World.restore(checkpoint)
    final=world.run(512);assert final==restored.run(512)
    return dict(version=law.VERSION,experiment=VERSION,control_mode=CONTROL,seed=seed,mode='faithful',route=route,genesis_program=law.PROGRAMS[route],checkpoint=checkpoint,final=final,hash=law.h(final),ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False)

def batch(seed,group,control):
    global CONTROL
    if type(seed) is not int or seed not in (27090,27091) or group not in ('candidates','references') or control not in CONTROLS:raise ValueError('Unregistered control batch')
    CONTROL=control;codes,routes=install_registry();roles=list(codes)[:8] if group=='candidates' else list(codes)[8:]
    return dict(contract=VERSION,seed=seed,group=group,control=control,histories=[dict(role=role,ancestry=candidate(int(role[9:])) if role.startswith('candidate') else None,row=history(seed,role,routes[role])) for role in roles],learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    raw=json.dumps(batch(int(sys.argv[1]),sys.argv[2],sys.argv[3]),sort_keys=True,separators=(',',':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
