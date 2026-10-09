"""Unreserved authored accounting/null feasibility; no screened science founders."""
import copy,json,unittest
from experiments import aggregate as m
from experiments import aggregate_audit as a
def relocate(w,particle,target):
    cost=min((target-particle['pos'])%8,(particle['pos']-target)%8)
    w['thermal']-=cost;w['heat']+=cost;w['stats']['thermal_motion']+=cost;particle['pos']=target
def request(w,op,cell,particle1=None,particle2=None,atom1=None,atom2=None,carrier1=None,carrier3=None,value=255,decay=255):
    ap=[i for i in range(24) if w['atoms'][i]['pos']==cell];cp=[i for i in range(16) if w['carriers'][i]['pos']==cell];pool=ap+[24+i for i in cp];d=[op,cell,0,0,0,1,value,decay]
    if particle1 is not None:d[2]=pool.index(particle1)
    if particle2 is not None:d[3]=pool.index(particle2)
    if atom1 is not None:d[2]=ap.index(atom1)
    if atom2 is not None:d[3]=ap.index(atom2)
    if carrier1 is not None:d[2]=cp.index(carrier1)
    if carrier3 is not None:d[4]=cp.index(carrier3)
    return d
class AggregateTests(unittest.TestCase):
    def test_unreserved_fixture_rng_and_all_arm_interpreters(self):
        for arm in m.ARMS:
            w=m.new(74999,arm);s=a.genesis(74999,arm);self.assertEqual(w,s)
            for t in range(1,257):
                d=[m.draw(w) for _ in range(8)];self.assertEqual(d,[a.random(s) for _ in range(8)])
                self.assertEqual(m.tick(w,t,d),a.advance(s,t,d));self.assertEqual(w,s)
    def test_paid_reversible_bind_and_mass_priced_motion(self):
        w=m.new(74999,'candidate');relocate(w,w['atoms'][0],0);relocate(w,w['carriers'][0],0);s=copy.deepcopy(w)
        d=request(w,1,0,particle1=0,particle2=24,value=0)
        self.assertEqual(m.tick(w,1,d),a.advance(s,1,d));self.assertEqual(w,s)
        old=w['thermal'];d=request(w,0,0,particle1=0)
        self.assertEqual(m.tick(w,2,d),a.advance(s,2,d));self.assertEqual(w['thermal'],old-2);self.assertEqual(w,s)
        old=sum(w['photons']);d=request(w,2,1,particle1=0,particle2=24,decay=0)
        self.assertEqual(m.tick(w,3,d),a.advance(s,3,d));self.assertEqual(sum(w['photons']),old-1);self.assertEqual(w['edges'],[]);self.assertEqual(w,s)
    def test_large_aggregate_refuses_one_carrier_transport(self):
        w=m.new(74999,'supplied');target=w['atoms'][0]['pos']
        for particle in (w['atoms'][2],w['atoms'][3]):
            # Move the complete supplied component, paying both particles' work.
            cost=min((target-particle['pos'])%8,(particle['pos']-target)%8);w['thermal']-=cost;w['heat']+=cost;w['stats']['thermal_motion']+=cost;particle['pos']=target
        w['objects'][1]['pos']=target
        relocate(w,w['carriers'][0],target);s=copy.deepcopy(w)
        d=request(w,1,target,particle1=0,particle2=2,value=0);self.assertEqual(m.tick(w,1,d),a.advance(s,1,d))
        d=request(w,3,target,carrier1=0,atom2=0,value=0);self.assertEqual(m.tick(w,2,d),a.advance(s,2,d))
        d=request(w,7,target,carrier1=0,atom2=0);self.assertEqual(m.tick(w,3,d),[]);self.assertEqual(a.advance(s,3,d),[])
        self.assertTrue(w['carriers'][0]['charged']);self.assertEqual(w,s);m.check(w)
    def test_blind_identity_damage_and_photon_withdrawal(self):
        w=m.new(74999,'supplied');s=copy.deepcopy(w)
        for t,ids in ((1024,[0,2]),(2048,[1,3])):
            d=[6,0,0,0,0,0,255,255];self.assertEqual(m.tick(w,t,d),a.advance(s,t,d));self.assertEqual(w['rounds'][-1]['damaged'],ids)
        before=sum(w['photons']);d=[6,0,0,0,0,0,255,255]
        self.assertEqual(m.tick(w,3072,d),a.advance(s,3072,d));self.assertEqual(w['removed'],before);self.assertEqual(w,s)
    def test_basal_capture_has_no_false_causal_parent(self):
        w=m.new(74999,'supplied');obj=w['objects'][0];ci=m.lane(obj['kind']);relocate(w,w['carriers'][ci],obj['pos']);s=copy.deepcopy(w)
        d=request(w,3,obj['pos'],carrier1=ci,atom2=obj['atoms'][0],value=0)
        self.assertEqual(m.tick(w,1,d),a.advance(s,1,d));self.assertIsNone(w['carriers'][ci]['charge']['donor']);self.assertEqual(w,s)
    def test_authored_two_round_path_in_both_primary_nulls(self):
        for arm in ('candidate','no-bond','shuffled'):
            w=m.new(74999,arm)
            for i in (0,1,2,3):relocate(w,w['atoms'][i],0)
            for i in (6,7,8,9):relocate(w,w['atoms'][i],4)
            s=copy.deepcopy(w);trace=[]
            def paid_carrier(ci,target):
                for state in (w,s):relocate(state,state['carriers'][ci],target)
            def act(t,op,cell,**kw):
                d=request(w,op,cell,**kw);events=m.tick(w,t,d);self.assertEqual(events,a.advance(s,t,d));self.assertEqual(w,s);trace.append(dict(step=t,draws=d,events=copy.deepcopy(events)));return events
            def charge(t,k,anchor,at,basal=False):
                ci=(m.lane(k)+int(arm=='shuffled' and t>=1024))%4+4
                paid_carrier(ci,at);act(t,3,at,carrier1=ci,atom2=anchor,value=0 if basal else 8);self.assertTrue(w['carriers'][ci]['charged']);return ci
            ci=charge(1,0,0,0,True);act(2,4,0,atom1=0,atom2=1,carrier3=ci)
            ci=charge(3,0,0,0);paid_carrier(ci,4);act(4,4,4,atom1=6,atom2=7,carrier3=ci)
            act(1024,6,0,atom1=0)
            ci=charge(1025,5,6,4);paid_carrier(ci,0);act(1026,5,0,atom1=0,atom2=1,carrier3=ci)
            ci=charge(1027,5,6,4);paid_carrier(ci,0);act(1028,4,0,atom1=0,atom2=1,carrier3=ci)
            ci=charge(1029,0,0,0);paid_carrier(ci,4);act(1030,4,4,atom1=8,atom2=9,carrier3=ci)
            self.assertTrue(w['rounds'][0]['qualified']);act(2048,6,4,atom1=6)
            ci=charge(2049,0,0,0);paid_carrier(ci,4);act(2050,5,4,atom1=6,atom2=7,carrier3=ci)
            ci=charge(2051,0,0,0);paid_carrier(ci,4);act(2052,4,4,atom1=6,atom2=7,carrier3=ci)
            ci=charge(2053,5,6,4);paid_carrier(ci,0);act(2054,4,0,atom1=2,atom2=3,carrier3=ci)
            self.assertTrue(m.record(w)['endpoint']);m.check(w);a.verify(s)
            print('AUTHORED_ONLY_UNRESERVED_FIXTURE '+json.dumps(dict(arm=arm,seed=74999,trace=trace,final=w),sort_keys=True))
if __name__=='__main__':unittest.main()
