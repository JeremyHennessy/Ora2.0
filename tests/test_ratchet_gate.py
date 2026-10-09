import copy
import unittest
from experiments import ratchet_gate as p
from experiments import ratchet_audit as a


class RatchetAccounting(unittest.TestCase):
    def test_whole_cost_certificate(self):
        w = p.certificate()
        self.assertEqual(a.inspect_witness(w,'candidate'),(2,0,17,1))
        self.assertEqual(w['snapshots'][-1], [2,0,17,1,113])
        self.assertEqual(sum(t['state']=='F' for t in w['tokens']),2)
        self.assertEqual(w['objects'][-1]['parent'],0)

    def test_reverse_fuel_is_available(self):
        s = (15,1,10,0)
        edges = dict(p.edges(s,'candidate'))
        self.assertEqual(edges[(0,-1)],(16,0,10,0))
        self.assertEqual(dict(a.proposals(s,'candidate')),edges)

    def test_unfunded_replacement(self):
        self.assertNotIn((5,1),dict(p.edges((16,0,6,0),'candidate')))
        self.assertNotIn((5,1),dict(a.proposals((16,0,6,0),'candidate')))

    def test_equilibrium_endpoint_impossible(self):
        # With F16 and bound2, work+heat+conformation=46<17+32.
        self.assertLess(144-96-2,17+32)
        self.assertFalse(any(c in (0,4) for (c,d),s in p.edges(p.START,'equilibrium')))

    def test_ledger_and_ancestry_refused(self):
        for key in ('heat','ancestry'):
            w = copy.deepcopy(p.certificate())
            if key == 'heat':
                w['snapshots'][-1][-1] += 1
            else:
                w['objects'][-1]['parent'] = None
            with self.assertRaises(ValueError):
                a.inspect_witness(w,'candidate')

    def test_isotropic_half_prefactor(self):
        edge = dict(p.edges(p.START,'isotropic'))[(0,1)]
        n,e = p.rate(p.START,(0,1),edge,'candidate',(0,0,0))
        m,f = p.rate(p.START,(0,1),edge,'isotropic',(0,0,0))
        self.assertEqual((m,f),(n,e+1))


if __name__ == '__main__':
    unittest.main()
