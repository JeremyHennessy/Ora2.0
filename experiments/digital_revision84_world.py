"""Narrow task/control adapter over unchanged MEMORY80 transitions.

The weak per-object runtime stores only a transient actual packet identifier and
the namespace-bound function. It contains no acquired state or phase knowledge
accessible to an organism. Every ACT overwrites it before label lookup; no host
snapshot/checkpoint needs this scratch value. All persistent state is recorded.
"""
import types
import weakref
from experiments import digital_memory80 as engine
from experiments.digital_revision84_source import (
    SEEDS, CONTROLS, WARM, DECISIONS, HORIZON, admit, descriptor, programme,
    finish_pc, target_mask)

_RUNTIME = weakref.WeakKeyDictionary()

def bind(function, labels=None):
    namespace = dict(function.__globals__)
    namespace.update(SOFTWARE=SEEDS, MASKS=labels)
    return types.FunctionType(function.__code__,namespace,function.__name__,
                              function.__defaults__,function.__closure__)

_genesis = bind(engine.World.__init__)

class Labels:
    def __init__(self, seed, admission, scratch):
        self.seed=seed; self.admission=admission; self.scratch=scratch

    def __getitem__(self, index):
        assert SEEDS[index] == self.seed
        packet=self.scratch['packet']
        assert type(packet) is int and packet >= 0, 'Actual ACT packet required'
        return target_mask(self.seed,packet,self.admission)

def channel(memory,index,owner):
    source=index
    if owner.control_active and owner.control_mode=='model_erased':source=None
    elif owner.control_active and owner.control_mode=='history_misbound':source=(index+1)%len(memory)
    value=0 if source is None else list.__getitem__(memory,source)
    return dict(address=index,source_address=source,value=value,
        truthful_cell=list.__getitem__(memory,index),active=owner.control_active)

class ModelView(list):
    def __init__(self, values, owner):
        super().__init__(values);self.owner=owner

    def __getitem__(self,index):
        return channel(self,index,self.owner)['value']

    def __setitem__(self,index,value):
        if not (self.owner.control_active and self.owner.control_mode=='update_frozen'):
            super().__setitem__(index,value)

class World(engine.World):
    def __init__(self, seed, role='learner8', control='intact', admission=None):
        admit(seed,admission)
        assert control in CONTROLS
        _genesis(self,seed,descriptor(role),'no_variation',1,0,programme(role))
        self.control_mode=control;self.control_active=0;self.decisions=0
        self.source_role=role;self.finish_pc=finish_pc(role)
        self.entities[0]['memory']=ModelView(self.entities[0]['memory'],self)
        scratch={'packet':None}
        _RUNTIME[self]=dict(scratch=scratch,
            transition=bind(engine.World.step,Labels(seed,admission,scratch)))

    def packet(self,e,reserve=False):
        packet=engine.World.packet(self,e,reserve)
        if not reserve:
            _RUNTIME[self]['scratch']['packet']=packet
        return packet

    def done(self):
        return not self.entities or self.tick>=HORIZON or (
            self.decisions>=DECISIONS and self.entities[0]['pc']==self.finish_pc)

    def step(self):
        if self.done():return False
        e=self.entities[0]
        cut=None
        if not self.control_active and self.decisions>=WARM and e['pc']==self.finish_pc:
            cut=dict(tick_before=self.tick,decisions=self.decisions,pc=e['pc'],energy=e['energy'])
            self.control_active=1
        op,a,b=[v[0] for v in e['code'][3*e['pc']:3*e['pc']+3]]
        read=None;store=None
        if op in (2,19):
            index=b%len(e['memory']) if op==2 else e['registers'][b%2]%len(e['memory'])
            read=channel(e['memory'],index,self)
        elif op in (3,20):
            index=a%len(e['memory']) if op==3 else e['registers'][a%2]%len(e['memory'])
            store=dict(address=index,value=e['registers'][b%2],
                before=list.__getitem__(e['memory'],index),active=self.control_active,
                blocked=int(bool(self.control_active and self.control_mode=='update_frozen')))
        assert _RUNTIME[self]['transition'](self)
        event=self.events[-1]
        if cut is not None:event['control_cut']=cut
        if read is not None:event['history_read']=read
        if store is not None:
            store['after']=list.__getitem__(e['memory'],store['address'])
            event['history_store']=store
        if op==6:self.decisions+=1
        event['state_hash']=engine.h(self.snapshot(False))
        return True

    def run(self,horizon=HORIZON):
        assert type(horizon) is int and horizon==HORIZON
        return super().run(horizon)
