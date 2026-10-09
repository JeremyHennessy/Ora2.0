import unittest
from experiments import condense_gate as p
from experiments import condense_audit as a


class CondenseAccounting(unittest.TestCase):
    def test_raw_capital(self):
        for arm in p.ARMS:
            for pos in range(8):
                s=(4,0,0,pos,0,0)
                self.assertEqual(p.heat(s,arm),8)
                self.assertEqual(a.heat(a.convert(s),arm),8)

    def test_binding_and_whole_loss_cost(self):
        s=(2,7,1,0,3,0)
        for arm in p.ARMS:
            targets=dict(p.edges(s,arm));fresh=targets[(4,0,1)]
            self.assertEqual(p.heat(fresh,arm)-p.heat(s,arm),3-p.affinity(arm))
            self.assertEqual(dict((act,a.encode(t)) for act,t in a.proposals(a.convert(s),arm)),targets)

    def test_hidden_forward_only_drive(self):
        proof=a.hidden_drive()
        self.assertTrue(proof['refused'])
        self.assertEqual(proof['unaccounted_ratio_multiplier'],8)

    def test_complex_translation_retains_bonds(self):
        s=(2,7,3,0,3,0)
        moved=dict(p.edges(s,'candidate'))[(3,0,1)]
        self.assertEqual(moved[3],7)
        self.assertEqual(moved[2],3)
        self.assertEqual(p.heat(s,'candidate'),p.heat(moved,'candidate'))

    def test_positive_material_potential(self):
        for mask in range(8):
            active={i for i in range(3) if mask>>i&1}
            for bonds in range(8):
                if all(set(pair)<=active for j,pair in enumerate(p.PAIRS) if bonds>>j&1):
                    self.assertGreaterEqual(2*len(active)-bonds.bit_count(),0)


if __name__=='__main__':unittest.main()
