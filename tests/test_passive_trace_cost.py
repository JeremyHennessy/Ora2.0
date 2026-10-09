"""Authored component price checks; no behavioral samples or controller."""
import copy
import json
import unittest
from experiments.passive_trace_cost import Cell, schedule
from experiments.passive_trace_cost_audit import initial, transition


class PassiveTraceCosts(unittest.TestCase):
    def test_atomic_operator_exhaustion(self):
        cell=Cell('memory-disabled')
        for t in range(64):cell.step(('write',0),t)
        before=copy.deepcopy(cell.state())
        self.assertEqual(cell.step(('write',0),64),dict(kind='unaffordable',operation='write'))
        self.assertEqual(cell.state(),before)
        self.assertEqual(len(cell.fuel),128)
        self.assertEqual(cell.heat,192)

    def test_reconstruction_has_new_paid_identity(self):
        cell=Cell('candidate');first=cell.step(('write',4),0)
        cell.step(('erase',4),1);second=cell.step(('write',4),2)
        self.assertEqual((first['trace'],second['trace']),(0,1))
        self.assertEqual(cell.traces[1]['parents'],dict(fuel=[2,3],pulse=[1]))
        self.assertEqual(cell.traces[0]['atoms'],cell.traces[1]['atoms'])
        self.assertEqual(len(cell.fuel)+len(cell.operator)+len(cell.active)+cell.heat,320)

    def test_unpaid_refresh_erases_state_and_read_is_null(self):
        cell=Cell('candidate')
        for t,i in enumerate(range(0,16,2)):cell.step(('write',i),t)
        for t in range(240):self.assertEqual(cell.step(('clock',None),8+t)['kind'],'clock')
        self.assertEqual(len(cell.active),8)
        failed=cell.step(('clock',None),248)
        self.assertEqual(failed['lost'],list(range(8)))
        self.assertFalse(cell.active)
        self.assertIsNone(cell.step(('read',0),249)['output'])
        self.assertEqual(cell.heat+len(cell.operator),320)

    def test_shuffled_assistance_is_paid_and_fixed_readout_immutable(self):
        cell=Cell('shuffled-history');event=cell.step(('write',14),0)
        self.assertEqual((event['target'],event['pulse']),(15,[0,1]))
        self.assertEqual((len(cell.operator),cell.heat),(62,3))
        fixed=Cell('fixed-reactive');bits=copy.copy(fixed.fixed)
        for t in range(16):
            fixed.step(('write',t),2*t)
            self.assertEqual(fixed.step(('read',t),2*t+1)['output'],bits[t])
        self.assertEqual(fixed.fixed,bits);self.assertFalse(fixed.active)

    def test_independent_transition_and_invalid_request(self):
        cell=Cell('candidate');before=copy.deepcopy(cell.state())
        for request in (('write',True),('read',16),('clock',0),('reward',0)):
            with self.assertRaises(ValueError):cell.step(request,0)
            self.assertEqual(cell.state(),before)
        expected,_=initial('candidate')
        for t,request in enumerate(schedule(0)):
            self.assertEqual(cell.step(request,t),transition(expected,request,t))
            self.assertEqual(json.loads(json.dumps(cell.state())),json.loads(json.dumps(expected)))


if __name__=='__main__':unittest.main()
