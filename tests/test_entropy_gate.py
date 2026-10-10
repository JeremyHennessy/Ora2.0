import copy,unittest
from experiments import entropy_gate as g,entropy_audit as a
class Entropy(unittest.TestCase):
    def test_full_priced_path_and_reverse_leak(self):
        self.assertEqual(a.path(g.certificate())['post_gain'],1)
        r=copy.deepcopy(g.certificate());r['score']['formation']-=1
        with self.assertRaises(AssertionError):a.path(r)
    def test_all_energy_bounded_rates_against_independent_law(self):
        for n in range(11):
            for b in (0,1):
                for w in range(21-2*b):
                    s=(n,b,w)
                    for k,d in g.ACTIONS:
                        self.assertEqual(g.move(s,(k,d)),a.transition(s,k,d))
                        for arm in g.ARMS:self.assertEqual(g.probability(s,(k,d),arm),a.rate(s,k,d,arm))
    def test_yoked_phase_and_function_flag(self):
        self.assertEqual(g.repair_max(5,2),a.maximum_after_loss(5,2))
        self.assertEqual(g.repair_max(5,18),18)
        self.assertEqual(g.next_flag((5,1,2),(4,1,3),0,('work',1)),1)
        self.assertEqual(a.evidence_flag((5,1,2),'form',-1,1),0)
if __name__=='__main__':unittest.main()
