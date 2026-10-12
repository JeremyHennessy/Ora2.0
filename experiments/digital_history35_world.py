"""Fresh History33 comparison input scope; unchanged Exposure23/Controls31 laws."""
import base64,json,zlib
from . import digital_informative_exposure23 as law
from .digital_pc_controls31 import Control,MODES
from .digital_source32_admission import manifest as source_manifest
from .digital_history33_endpoint import FRESH_SEEDS

VERSION='DIGITAL-HISTORY-35-FRESH-v1'
SEEDS=FRESH_SEEDS

def manifest():
    m=source_manifest();m.update(contract=VERSION,seeds=list(SEEDS),candidate_histories=1344,reference_histories=264,total_histories=1608,primary=True)
    return m

def programmes():
    m=manifest()
    return dict([(f"candidate{x['candidate_id']}",x['program']) for x in m['candidates']]+[(x['role'],x['program']) for x in m['references']])

def chunks():
    roles=list(programmes())
    return [roles[i:i+8] for i in range(0,56,8)]+[roles[56:64],roles[64:67]]

def install():
    codes=programmes();registry={};routes={}
    for role,code in codes.items():
        key='genome-'+law.h(code)
        if key in registry:assert registry[key]==code
        registry[key]=code;routes[role]=key
    law.PROGRAMS=registry
    return codes,routes

def local(e):return dict(r=e['registers'][:],m=e['memory'][:],pc=e['pc'],feedback=e['feedback'])

class World(law.World):
    def __init__(self,seed,mode='faithful',route=None,control='intact'):
        assert type(seed) is int and seed in SEEDS and mode=='faithful' and control in MODES
        self.control_mode=control
        super().__init__(seed,mode,route)
        code=[[v[0] for v in self.entities[0]['code'][i:i+3]] for i in range(0,len(self.entities[0]['code']),3)]
        self._control=Control(code,local(self.entities[0]),control,seed);self._origin=None

    def snapshot(self,include_events=True):
        return law.clone({k:v for k,v in self.__dict__.items() if not k.startswith('_') and (include_events or k!='events')})

    def step(self):
        if not self.entities:return False
        assert set(self.entities)=={0};e=self.entities[0];assert e['inbox'] is None and e['pos']==0 and not e['nursery']
        before=local(e);assert [v[0] for v in e['code']]==sum(self._control.code,[])
        assert super().step();event=self.events[-1]
        native=local(e);updated,annotation=self._control.apply(before,native)
        sample=None
        if event['decoded'][0]==1:
            sample=dict(read_index=self._control.reads,own_source_tick=self._origin,original=native['r'][event['decoded'][1]%2],value=updated['r'][event['decoded'][1]%2])
        if event['decoded'][0]==6:self._origin=event['tick'] if 'attempt' in event else None
        annotation['personal_read']=sample;annotation['latest_own_source_tick']=self._origin
        e['registers']=updated['r'];e['memory']=updated['m'];e['pc']=updated['pc'];assert e['feedback']==updated['feedback']
        event['control']=annotation
        if 'after' in event:event['after']=law.clone(e)
        self.check();event['state_hash']=law.h(self.snapshot(False));return True

    @classmethod
    def restore(cls,state):
        law.state_types(state);assert type(state['tick']) is int and 0<=state['tick']<=512
        routes=[name for name,program in law.PROGRAMS.items() if sum(program,[])==[cell['value'] for cell in state['formation'][:3*len(program)]] and len(state['formation'])==3*len(program)+16]
        assert len(routes)==1
        world=cls(state['seed'],state['mode'],routes[0],state['control_mode'])
        while world.tick<state['tick']:assert world.step()
        assert law.h(world.snapshot())==law.h(state)
        return world

def history(seed,route,control):
    world=World(seed,'faithful',route,control)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot();restored=World.restore(checkpoint);final=world.run(512)
    assert final==restored.run(512)
    return dict(version=law.VERSION,experiment=VERSION,seed=seed,mode='faithful',control_mode=control,route=route,genesis_program=law.PROGRAMS[route],checkpoint=checkpoint,final=final,hash=law.h(final),ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False)

def batch(seed,control,chunk):
    if type(seed) is not int or seed not in SEEDS or control not in MODES or type(chunk) is not int or not 0<=chunk<9:
        raise ValueError('Unregistered fresh History33 batch')
    codes,routes=install();source={f"candidate{x['candidate_id']}":x for x in manifest()['candidates']}
    return dict(contract=VERSION,seed=seed,control=control,chunk=chunk,
                histories=[dict(role=role,ancestry=source.get(role),source_descriptor_is_static=True,
                                row=history(seed,routes[role],control)) for role in chunks()[chunk]],
                learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    raw=json.dumps(batch(int(sys.argv[1]),sys.argv[2],int(sys.argv[3])),sort_keys=True,separators=(',',':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
