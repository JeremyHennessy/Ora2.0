import unittest
from fractions import Fraction
from experiments import mineral_gate as g,mineral_audit as a
class Mineral(unittest.TestCase):
    def test_lost_thiol_and_charge_are_not_free(self):
        for l,r in g.REACTIONS:self.assertTrue(g.balanced(l,r));a.check_atoms(l,r)
        l=dict(g.REACTIONS[1][0]);l['CH3SH']=1
        self.assertFalse(g.balanced(l,g.REACTIONS[1][1]))
        with self.assertRaises(AssertionError):a.check_atoms(l,g.REACTIONS[1][1])
    def test_fresh_pre_and_post_use_requires_paid_preparation_and_repair(self):
        self.assertEqual(a.ledger(2,4,8,8),[2,4,8,8,2,1])
        self.assertEqual(a.ledger(2,4,8,6),[2,4,8,6,0,0])
        for e in range(13):self.assertEqual(g.nickel(4,8,12,e),a.ledger(4,8,12,e))
        self.assertEqual(a.methanol(4,11),[4,11,3])
    def test_voltage_reference_shift_is_not_cell_work(self):
        shift=Fraction('0.198');w,c,q=Fraction('-0.6'),Fraction('0.4'),Fraction(2)
        self.assertEqual(g.cell_work(w,c,q),g.cell_work(w+shift,c+shift,q))
        self.assertEqual(g.cell_work(w,c,q),2)
        self.assertIsNone(g.cell_work(w,None,q));self.assertIsNone(g.cell_work(w,c,None))
if __name__=='__main__':unittest.main()
