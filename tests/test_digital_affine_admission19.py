import copy, unittest
from experiments.digital_affine_admission19_audit import endpoint, PROGRAMS
from experiments.digital_affine_source18 import compile_program

class AffineAdmission19(unittest.TestCase):
    def test_route_blind_endpoint_accepts_feasible_exposure_refuses_missing_fresh_and_aliases(self):
        r=dict(pre_outcomes=[0,1],pre_ports=[0,1],alive_through_change=True,post_actions=32,post_successes=16,fresh_packets=16)
        self.assertTrue(endpoint(r))
        for key,value in [('fresh_packets',15),('post_actions',True),('alive_through_change',1),('pre_outcomes',[False,True]),('post_successes',0)]:
            bad=copy.deepcopy(r);bad[key]=value;self.assertFalse(endpoint(bad))
        self.assertFalse(endpoint({}))
    def test_exact_supplied_fixed_source_is_not_a_feedback_learner(self):
        self.assertEqual(PROGRAMS['affine3'],compile_program(3))
        self.assertFalse(any(r[0] in (1,9,10,12,14,15,16) for r in PROGRAMS['affine3']))
