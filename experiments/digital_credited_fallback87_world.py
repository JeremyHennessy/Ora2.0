"""Fresh label/seed binding over exact MEMORY80 paid code and source86 controls."""
import types
import weakref
from experiments import digital_memory80 as engine
from experiments import digital_credited_fallback86_controls as controls86
from experiments import digital_credited_fallback87_source as source

_RUNTIME=weakref.WeakKeyDictionary()

def bind(function, labels=None):
    namespace=dict(function.__globals__)
    namespace.update(SOFTWARE=source.SEEDS,MASKS=labels)
    return types.FunctionType(function.__code__,namespace,function.__name__,
                              function.__defaults__,function.__closure__)

_genesis=bind(engine.World.__init__)

class Labels:
    def __init__(self,seed,admission,scratch):
        self.seed=seed;self.admission=admission;self.scratch=scratch
    def __getitem__(self,index):
        assert source.SEEDS[index]==self.seed
        packet=self.scratch['packet']
        assert type(packet) is int and packet>=0, 'Actual served packet required'
        return source.target_mask(self.seed,packet,self.admission)

class ReferenceRuntime:
    def __init__(self,descriptor):
        self.completed=0;self.dispatch_pc=None;self.ledger=[]
        self.finish=2 if descriptor=='fixed_alternation' else 1
    def before(self,entity):
        self.dispatch_pc=entity['pc'];return None
    def after(self,event):
        after=event.get('after')
        if after is not None and self.dispatch_pc!=0 and event['decoded'][0]==7 and after['pc']==self.finish:
            self.completed+=1
            return dict(completed=self.completed,previous_pc=self.dispatch_pc,
                        entry=self.finish,energy=after['energy'])
        return None

class World(engine.World):
    def __init__(self,seed,descriptor,control='intact',admission=None):
        source.admit(seed,admission)
        code=source.programme(descriptor);reference=source.is_reference(descriptor)
        assert type(control) is str and control in source.ARMS
        if reference:assert control=='intact'
        runtime=ReferenceRuntime(descriptor) if reference else controls86.Runtime(descriptor[1],control)
        _genesis(self,seed,code[0][1],'no_variation',1,0,code)
        if not reference:
            self.entities[0]['memory']=controls86.ModelView(self.entities[0]['memory'],runtime)
        scratch={'packet':None}
        _RUNTIME[self]=dict(runtime=runtime,reference=reference,scratch=scratch,
            transition=bind(engine.World.step,Labels(seed,admission,scratch)))
    def packet(self,entity,reserve=False):
        packet=engine.World.packet(self,entity,reserve)
        if not reserve:_RUNTIME[self]['scratch']['packet']=packet
        return packet
    def done(self):
        return not self.entities or self.tick>=source.HORIZON or _RUNTIME[self]['runtime'].completed>=source.DECISIONS
    def step(self):
        if self.done():return False
        owner=_RUNTIME[self];runtime=owner['runtime'];entity=self.entities[0]
        completed=runtime.completed;entry=runtime.before(entity);pc=runtime.dispatch_pc
        read=runtime.read(entity['memory'],entity['registers'][1]) if not owner['reference'] and pc in (7,12) else None
        assert owner['transition'](self)
        event=self.events[-1];completion=runtime.after(event)
        runtime.ledger.append(dict(tick=event['tick'],dispatch_pc=pc,
            completed_before=completed,entry=entry,read=read,completion=completion))
        return True
    def control_ledger(self):return _RUNTIME[self]['runtime'].ledger
    def run(self,horizon=1024):
        raise RuntimeError('Separate registered custody must use bounded step loop and terminal_view')
