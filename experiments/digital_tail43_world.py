"""Tail42 frozen inventory admission; unchanged Exposure23/Controls31 semantics."""
import base64,hashlib,json,zlib
from pathlib import Path
from . import digital_informative_exposure23 as law
from .digital_pc_controls31 import Control,MODES
from .digital_source32_admission import manifest as reference_manifest

VERSION='DIGITAL-TAIL-43-ADMISSION-v1'
SEEDS=(43100,43101)
# No future primary or reserve assigned by this admission.
SOURCE_SHA256='b257e45c1fa59903b9460b6e46efc392fea02c80f2095e3be13917f6da0cf5ba'

def source_manifest():
    raw=(Path(__file__).resolve().parents[1]/'data/digital-neutral-tail42-manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Frozen Tail42 byte identity mismatch')
    m=json.loads(raw)
    assert m['contract']=='DIGITAL-NEUTRAL-TAIL-42-v1' and m['declared_samples']==256
    assert [x['sample_id'] for x in m['candidates']]==list(range(256))
    assert m['accepted_assignments']==6144 and not m['performance_selection'] and not m['semantic_deduplication']
    return m

def manifest():
    m=source_manifest()
    m.update(contract=VERSION,seeds=list(SEEDS),candidate_histories=1536,
             reference_histories=66,total_histories=1602,primary=False,
             references=reference_manifest()['references'])
    return m

def programmes():
    m=manifest()
    return dict([(f"candidate{x['sample_id']}",x['program']) for x in m['candidates']]+
                [(x['role'],x['program']) for x in m['references']])

def chunks():
    roles=list(programmes())
    return [roles[i:i+8] for i in range(0,256,8)]+[roles[256:264],roles[264:267]]

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
    if type(seed) is not int or seed not in SEEDS or control not in MODES or type(chunk) is not int or not 0<=chunk<34:
        raise ValueError('Unregistered Tail42 paid admission batch')
    codes,routes=install();source={f"candidate{x['sample_id']}":x for x in manifest()['candidates']}
    return dict(contract=VERSION,seed=seed,control=control,chunk=chunk,
                histories=[dict(role=role,ancestry=source.get(role),source_descriptor_is_static=True,
                                row=history(seed,routes[role],control)) for role in chunks()[chunk]],
                learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    raw=json.dumps(batch(int(sys.argv[1]),sys.argv[2],int(sys.argv[3])),sort_keys=True,separators=(',',':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
