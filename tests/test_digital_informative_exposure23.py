import unittest
from experiments.digital_informative_exposure23_audit import endpoint,PROGRAMS
from experiments.digital_affine_admission20_audit import cold_prefix

class ExposureFixtures(unittest.TestCase):
    def test_unchanged_endpoint_needs_personal_opportunities(self):
        row=dict(pre_outcomes=[0,1],pre_ports=[0,1],alive_through_change=True,post_actions=4,post_successes=4,fresh_packets=16)
        self.assertTrue(endpoint(row))
        for key,value in [('pre_outcomes',[1]),('pre_ports',[0]),('alive_through_change',False),('fresh_packets',15),('post_actions',True)]:self.assertFalse(endpoint(dict(row,**{key:value})))

    def test_exact_supplied_fixed_cold_prefix_is_not_learning(self):
        self.assertEqual(cold_prefix(PROGRAMS['affine3']),([(2,0),(4,1)],1))
        self.assertEqual(len(PROGRAMS['affine3']),13)
        self.assertNotIn(1,[r[0] for r in PROGRAMS['affine3']])
