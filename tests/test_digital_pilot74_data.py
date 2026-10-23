"""Invented structural data only; no executed ancestry or resume authority."""
import copy,hashlib,unittest
from unittest.mock import patch
from experiments import digital_pilot74_data as data

IDENTITY=dict(revision='a'*40,source_sha256='b'*64,config_sha256='c'*64,law='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1')
def prepared(cut=8192,seed=3):
    # Every actor is invented and expired. No ordinary VM execution produced this.
    count=cut//256
    base=dict(_dose=8,inheritance_mode='parent_copy',fuel_mode='renewed',turns={str(i):256 for i in range(count)},offered=16*(cut//64),admitted=0,rejected=16*(cut//64),next_packet=64+16*(cut//64),seed=seed,mode='faithful',tick=cut,last=count-1,next_id=count,writes=0,constructor_remaining=69,heat=71,formation=[dict(unit=i,value=0,energy=1,assistance='supplied ancestor assembly') for i in range(43)],food={str(i):[0 if i<32 else 1+(i-32)//16,0] for i in range(64)},free=list(range(512)),entities={},events=[dict(tick=i+1,actor=i//256) for i in range(cut)],births=count-1,deaths=count,maximum=1)
    checkpoint=copy.deepcopy(base)
    body=dict(id=0,parent=None,generation=0,code=[[0,i] for i in range(27)],state_units=list(range(27,43)),memory=[0]*8,registers=[0,0],pc=0,cue=0,feedback=0,inbox=None,pos=0,energy=12,nursery=[])
    checkpoint.update(turns={'0':64},offered=16,rejected=16,next_packet=80,tick=64,last=0,next_id=1,constructor_remaining=85,heat=43,free=list(range(43,512)),entities={'0':body},events=copy.deepcopy(base['events'][:64]),births=0,deaths=0)
    checkpoint['events'][-1]['state_hash']=data.digest({k:v for k,v in checkpoint.items() if k!='events'})
    base['events'][63]=copy.deepcopy(checkpoint['events'][-1])
    base['events'][-1]['state_hash']=data.digest({k:v for k,v in base.items() if k!='events'})
    return base,checkpoint
def packet(state=None,checkpoint=None):
    if state is None:state,checkpoint=prepared()
    raw=data.canonical(dict(version=data.VERSION,identity=IDENTITY,checkpoint64=checkpoint,state=state,state_sha256=data.digest(state)))
    return raw,hashlib.sha256(raw).hexdigest()

class PilotDataPrepared(unittest.TestCase):
    def reject(self,edit):
        state,checkpoint=prepared();edit(state,checkpoint);raw,sha=packet(state,checkpoint)
        with self.assertRaises(ValueError):data.decode_prepared(raw,IDENTITY,sha,40*1024**2)
    def test_long_cuts_and_seed_pair_normalize_without_mutating(self):
        for cut in (8192,9216,10240):
            for seed in (3,):
                state,checkpoint=prepared(cut,seed);before=copy.deepcopy(state);raw,sha=packet(state,checkpoint)
                loaded=data.decode_prepared(raw,IDENTITY,sha,40*1024**2)
                self.assertEqual(state,before);self.assertEqual(loaded['_dose'],8)
                self.assertTrue(all(type(k) is int for name in ('turns','food','entities') for k in loaded[name]))
    def test_custody_is_checked_before_decode(self):
        raw,sha=packet()
        with patch.object(data.json,'loads',side_effect=AssertionError('decode reached')):
            for bad,cap in ((raw[:-1],len(raw)),(raw+b'x',len(raw)+1),(raw,len(raw)-1)):
                with self.assertRaises(ValueError):data.decode_prepared(bad,IDENTITY,sha,cap)
    def test_old_scope_wrong_dose_and_boolean_fields(self):
        for key,value in (('seed',1),('seed',4),('seed',True),('_dose',1),('_dose',True),('tick',4096),('tick',True),('mode','mutating'),('inheritance_mode','ancestor_copy')):
            self.reject(lambda s,c,k=key,v=value:s.update({k:v}))
    def test_exact_field_identity_and_canonical_json(self):
        self.reject(lambda s,c:s.pop('_dose'));self.reject(lambda s,c:s.update(host_command='anything'))
        raw,_=packet()
        for bad in (raw+b'\n',raw.replace(b'"_dose":8',b'"_dose":8,"_dose":8'),raw.replace(b'"_dose":8',b'"_dose":8.0')):
            with self.assertRaises(ValueError):data.decode_prepared(bad,IDENTITY,hashlib.sha256(bad).hexdigest(),40*1024**2)
        raw,sha=packet()
        with self.assertRaises(ValueError):data.decode_prepared(raw,dict(IDENTITY,revision='d'*40),sha,40*1024**2)
    def test_resource_material_and_actor_opportunity_limits(self):
        self.reject(lambda s,c:s.update(heat=72));self.reject(lambda s,c:s['free'].__setitem__(0,1))
        self.reject(lambda s,c:s['turns'].__setitem__('0',257));self.reject(lambda s,c:s.update(next_packet=2625))
        self.reject(lambda s,c:s['turns'].__setitem__('00',s['turns'].pop('0')))
    def test_checkpoint_is_complete_and_prefix_bound(self):
        self.reject(lambda s,c:c.update(seed=4));self.reject(lambda s,c:c.update(_dose=1))
        self.reject(lambda s,c:c['events'][0].update(actor=1));self.reject(lambda s,c:c.update(tick=65))
    def test_actual_channel_structure_rejects_bool_and_oversize(self):
        self.reject(lambda s,c:c['entities']['0']['memory'].__setitem__(0,True))
        self.reject(lambda s,c:c['entities']['0']['registers'].append(0))
        self.reject(lambda s,c:c['entities']['0'].update(pc=9))
        self.reject(lambda s,c:c['entities']['0'].update(inbox=16))

if __name__=='__main__':unittest.main()
