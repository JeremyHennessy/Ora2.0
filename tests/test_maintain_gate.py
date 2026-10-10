import copy
import unittest
from experiments import maintain_gate as g, maintain_audit as a

class Admission(unittest.TestCase):
    def test_paid_path_independently_interpreted(self):
        self.assertEqual(a.path(g.certificate())['post_surplus'],1)
        forged=copy.deepcopy(g.certificate());forged['score']['whole_surplus']+=1
        with self.assertRaises(AssertionError):a.path(forged)

    def test_all_catalogue_reverse_contexts_and_annealed_mean(self):
        self.assertEqual(g.contexts(),a.context_check())

    def test_every_small_transition_matches_independent_stoichiometry(self):
        for bits in range(8):
            for work in range(10):
                s=(2,1,1,bits,work)
                for k,i,d in g.ACTIONS:
                    self.assertEqual(g.move(s,(k,i,d)),a.successor(s,k,i,d))
        self.assertIsNone(g.move((4,3,3,0,0),('activate',0,1)))
if __name__=='__main__':unittest.main()
