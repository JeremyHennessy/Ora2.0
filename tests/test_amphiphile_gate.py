import unittest
from experiments import amphiphile_gate as g,amphiphile_audit as a

class Accounting(unittest.TestCase):
    def test_every_reaction_balances_hydrogen_oxygen_sulfur_and_moieties(self):
        for left,right in a.RULES:self.assertEqual(a.total(left),a.total(right))
        self.assertNotEqual(a.total({'L':2,'F':1}),a.total({'B':1,'Q':1}))
    def test_minimal_replacement_and_paid_regeneration(self):
        self.assertTrue(g.case(3,1,1)[5]);self.assertTrue(g.case(3,2,0)[5])
        self.assertFalse(g.case(2,4,4)[5]);self.assertFalse(g.case(8,1,0)[5]);self.assertFalse(g.case(8,0,4)[5])
        self.assertEqual(g.case(3,1,1)[8:],[1,3])
        for t,b,f in ((3,1,1),(3,2,0),(8,4,4),(0,0,0)):self.assertEqual(g.case(t,b,f),a.enumerate_case(t,b,f))
    def test_cycle_keeps_head_but_consumes_tail_and_peroxide(self):
        net=tuple(sum(d[i] for d in g.STEPS) for i in range(7))
        self.assertEqual(net,(-2,0,0,0,1,-1,2))
        self.assertEqual(g.inventory(net),(0,0,0,0,0))
