import copy,unittest
from experiments.digital_exploration13 import history
from experiments.digital_exploration13_audit import audit,endpoint

class Exploration13(unittest.TestCase):
    def test_same_endpoint_refuses_missing_paid_opportunity(self):
        r=dict(pre_outcomes=[0,1],pre_ports=[0,1],alive_through_change=True,post_actions=4,post_successes=4)
        self.assertTrue(endpoint(r))
        for key,value in [('pre_outcomes',[1]),('pre_ports',[0]),('alive_through_change',False),('post_actions',3),('post_successes',3)]:
            bad=dict(r);bad[key]=value;self.assertFalse(endpoint(bad))

    def test_forged_own_feedback_outcome_is_rejected(self):
        row=history(26191,'fixed0');self.assertFalse(audit(row)['ordinary_admitted'])
        bad=copy.deepcopy(row)
        attempt=next(e['attempt'] for e in bad['history']['final']['events'] if 'attempt' in e)
        attempt['success']=1-attempt['success']
        with self.assertRaises(AssertionError):audit(bad)
