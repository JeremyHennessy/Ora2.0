"""Authored physical possibility and adversarial checks, never panel founders."""
import copy
import hashlib
import io
import json
import unittest
from experiments import carrier as m
from experiments import carrier_audit as a


class CarrierTests(unittest.TestCase):
    def test_all_arm_rng_and_independent_dynamics(self):
        for arm in m.ARMS:
            w=m.new(73000,arm);s=a.genesis(73000,arm);self.assertEqual(w,s)
            for t in range(1,560):
                d=[m.draw(w) for _ in range(8)];self.assertEqual(d,[a.token(s) for _ in range(8)])
                self.assertEqual(m.tick(w,t,d),a.advance(s,t,d));self.assertEqual(w,s)

    def test_baseline_has_no_false_catalyst_donation(self):
        w=m.new(73000,'supplied');c=w['objects'][0];ci=m.lane(c['kind'])
        w['carriers'][ci]['pos']=c['pos']
        d=[2,ci,0,1,c['atoms'][0],0,0,255]
        m.tick(w,1,d)
        self.assertTrue(w['carriers'][ci]['charged']);self.assertIsNone(w['carriers'][ci]['charge']['donor'])

    def test_private_carrier_removes_cross_funding_without_refund(self):
        w=m.new(73000,'private');c=w['carriers'][0]
        w['photons'][c['pos']]-=4;w['heat']+=1
        c.update(charged=True,charge=dict(step=1,donor=0,kind=0,atoms=[0,1],assisted=False))
        self.assertTrue(m.usable(w,0,[0,1]));self.assertFalse(m.usable(w,0,[2,3]));m.check(w)

    def test_full_damage_and_natural_energy_removal(self):
        w=m.new(73000,'supplied');before=sum(c['alive'] and c['pos']<4 for c in w['objects'])
        m.tick(w,512,[5,0,0,1,23,0,255,255]);self.assertEqual(w['stats']['damage'],before)
        photons=sum(w['photons']);m.tick(w,1536,[5,0,0,1,23,0,255,255])
        self.assertEqual(w['removed'],photons);self.assertEqual(sum(w['photons']),0);m.check(w)

    def test_authored_paid_cross_funded_reconstruction_return_path(self):
        w=m.new(73000,'candidate')
        # Position only raw precursor material/carriers, paying all ring transport.
        def position(obj,target):
            cost=min((target-obj['pos'])%8,(obj['pos']-target)%8)
            w['thermal']-=cost;w['heat']+=cost;w['stats']['motion']+=cost;obj['pos']=target
        for i in (0,1):position(w['atoms'][i],0)
        for i in (6,7,8,9):position(w['atoms'][i],4)
        cx=m.lane(0);cy=4+m.lane(5)
        position(w['carriers'][cx],0);position(w['carriers'][cy],4)
        s=copy.deepcopy(w);trace=[]
        def act(t,op,ci,i,j,anchor,value=255):
            d=[op,ci,i,j,anchor,0,value,255]
            e=m.tick(w,t,d);f=a.advance(s,t,d);self.assertEqual(e,f);self.assertEqual(w,s)
            self.assertTrue(e);trace.append(dict(step=t,events=copy.deepcopy(e),energy=640))
        def carry(ci,target):
            # Each displacement is charged, never free successful interaction.
            for state in (w,s):
                obj=state['carriers'][ci];cost=min((target-obj['pos'])%8,(obj['pos']-target)%8)
                state['thermal']-=cost;state['heat']+=cost;state['stats']['motion']+=cost;obj['pos']=target
        act(1,2,cx,0,1,23,0);act(2,3,cx,0,1,23)
        act(3,2,cx,0,1,0,8);carry(cx,4);act(4,3,cx,6,7,23)
        act(512,5,cx,0,1,23)
        self.assertEqual(w['lost'],[0])
        act(513,2,cy,0,1,6,8);carry(cy,0);act(514,4,cy,0,1,23)
        carry(cy,4);act(515,2,cy,0,1,6,8);carry(cy,0);act(516,3,cy,0,1,23)
        carry(cx,0);act(517,2,cx,0,1,0,8);carry(cx,4);act(518,3,cx,8,9,23)
        self.assertTrue(w['endpoint']);self.assertNotEqual(w['objects'][0]['id'],w['objects'][2]['id'])
        m.check(w);a.conservation(s)
        print('AUTHORED_ONLY_CARRIER_FIXTURE '+json.dumps(dict(trace=trace,final=w),sort_keys=True))


if __name__=='__main__':unittest.main()
