import copy,unittest
from experiments.digital_admission_roles24 import ordinary_exploration,reactive_reachability,prepared_records

class AdmissionRoles(unittest.TestCase):
    def test_ordinary_exploration_still_requires_cold_both_ports_and_outcomes(self):
        r=dict(pre_outcomes=[0,1],pre_ports=[0,1],alive_through_change=True,post_actions=17,post_successes=16,fresh_packets=16)
        self.assertTrue(ordinary_exploration(r))
        self.assertFalse(ordinary_exploration(dict(r,pre_ports=[0],pre_outcomes=[1])))

    def test_reactive_reachability_does_not_force_an_unnecessary_cold_failure(self):
        self.assertTrue(reactive_reachability(prepared_records()[0]['record']))

    def test_all_counterexamples_are_refused(self):
        for r in prepared_records()[1:]:
            with self.subTest(r['name']):self.assertFalse(reactive_reachability(r['record']))

    def test_initial_and_empty_values_do_not_add_actual_experience(self):
        r=copy.deepcopy(prepared_records()[0]['record']);r['reads'].insert(0,dict(tick=1,actor=0,origin='initial',source_tick=None,value=0))
        self.assertTrue(reactive_reachability(r))
        r['reads'][0]['origin']='own_actual_attempt';r['reads'][0]['source_tick']=0
        self.assertFalse(reactive_reachability(r))

    def test_true_counts_and_same_tick_actions_cannot_alias_real_evidence(self):
        r=copy.deepcopy(prepared_records()[0]['record']);r['actions'][0]['attempt']['success']=False
        self.assertFalse(reactive_reachability(r))
        r=copy.deepcopy(prepared_records()[0]['record']);r['reads'][0]['tick']=65
        self.assertFalse(reactive_reachability(r))
