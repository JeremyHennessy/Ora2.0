"""Thin prospective task/control adapter; immutable MEMORY80 VM byte code.

No old module/global mutation. New namespaces supply only admitted seed and
label data. The host-installed read lens is a disclosed causal intervention,
not writable organism memory, a new instruction or an organism callback.
"""
import types
from experiments import digital_memory80 as engine
from experiments.digital_learning81_source import PRIMARY,UNSEEN,SOFTWARE,CONTROLS,descriptor,programme,finish_pc
VERSION='DIGITAL-LEARNING81-WORLD-v1'
SEEDS=SOFTWARE+PRIMARY+UNSEEN

def target_mask(seed):
    assert type(seed) is int and seed in SEEDS
    if seed in SOFTWARE:return (0,255,90,165)[SOFTWARE.index(seed)]
    bank=PRIMARY if seed in PRIMARY else UNSEEN
    index=bank.index(seed)
    if index<2:return (0,255)[index]
    return int(engine.h(['LEARNING81-LABELS-v1',seed])[:2],16)

class Labels:
    def __getitem__(self,index):return target_mask(SEEDS[index])

def bind(function):
    namespace=dict(function.__globals__)
    namespace.update(SOFTWARE=SEEDS,MASKS=Labels())
    return types.FunctionType(function.__code__,namespace,function.__name__,function.__defaults__,function.__closure__)

_genesis=bind(engine.World.__init__)
_transition=bind(engine.World.step)

def channel(memory,index,owner):
    active=owner.decisions>=32
    source=index
    if active and owner.control_mode=='model_erased':source=None
    elif active and owner.control_mode=='history_misbound':source=(index+1)%len(memory)
    value=0 if source is None else list.__getitem__(memory,source)
    return dict(address=index,source_address=source,value=value,
                truthful_cell=list.__getitem__(memory,index),active=int(active))

class ModelView(list):
    def __init__(self,values,owner):super().__init__(values);self.owner=owner
    def __getitem__(self,index):return channel(self,index,self.owner)['value']
    # Writes/iteration/JSON retain the real cells; only VM indexed reads change.

class World(engine.World):
    def __init__(self,seed,role='learner8',control='intact'):
        assert type(seed) is int and seed in SEEDS and control in CONTROLS
        bind(_genesis)(self,seed,descriptor(role),'no_variation',1,0,programme(role))
        self.control_mode=control;self.decisions=0;self.source_role=role;self.finish_pc=finish_pc(role)
        self.entities[0]['memory']=ModelView(self.entities[0]['memory'],self)

    def done(self):
        return not self.entities or self.tick>=1024 or (
            self.decisions>=64 and self.entities[0]['pc']==self.finish_pc)

    def step(self):
        if self.done():return False
        e=self.entities[0];op,a,b=[v[0] for v in e['code'][3*e['pc']:3*e['pc']+3]]
        read=None
        if op in (2,19):
            index=b%len(e['memory']) if op==2 else e['registers'][b%2]%len(e['memory'])
            read=channel(e['memory'],index,self)
        assert bind(_transition)(self)
        event=self.events[-1]
        if read is not None:event['history_read']=read
        if op==6:self.decisions+=1
        event['state_hash']=engine.h(self.snapshot(False))
        return True

    def run(self,horizon=1024):
        assert type(horizon) is int and horizon==1024
        return super().run(horizon)
