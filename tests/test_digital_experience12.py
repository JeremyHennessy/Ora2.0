import copy,unittest
from experiments.digital_experience12 import history
from experiments.digital_experience12_audit import audit,experience_endpoint
from experiments.digital_release07_audit import h
class Experience12(unittest.TestCase):
    def test_same_endpoint_positive_impossible(self):
        p=dict(outcomes=[0,1],reads_between_real_actions=4,post_change_actions=4,post_change_successes=1)
        self.assertTrue(experience_endpoint([p]));self.assertFalse(experience_endpoint([dict(p,reads_between_real_actions=0)]));self.assertFalse(experience_endpoint([dict(p,post_change_successes=0)]))
    def test_actual_full_baseline_and_rehashed_feedback_forgery(self):
        r=history(26090,'ancestor');m=audit(r);self.assertEqual(m['successful_food'],32);self.assertFalse(m['experience_reachable'])
        bad=copy.deepcopy(r);e=next(e for e in bad['history']['final']['events'] if 'attempt' in e);e['attempt']['success']=1-e['attempt']['success'];bad['history']['hash']=h(bad['history']['final'])
        with self.assertRaises(AssertionError):audit(bad)
