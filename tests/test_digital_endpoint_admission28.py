import unittest
from experiments.digital_endpoint_admission28 import compare,summarize

class EndpointTests(unittest.TestCase):
    def metric(self,alive=True):
        return dict(ticks=512 if alive else 100,paid_instructions=512 if alive else 100,food=32,fresh=16,fresh_attempted=16,alive_at_horizon=alive,death_tick=None if alive else 100,all_fresh_acquired_tick=90)
    def test_death_is_not_cheaper_successful_survival(self):
        m=compare(self.metric(False),self.metric())
        self.assertTrue(m['lower_instruction_count_is_censored']);self.assertEqual(m['survival_delta'],-1)
        self.assertFalse(m['learning_inference'])
    def test_fixed_ceiling_has_no_positive_count_headroom(self):
        m=compare(self.metric(),self.metric())
        self.assertTrue(m['fixed_fresh_ceiling']);self.assertEqual(m['fresh_delta'],0)
        self.assertTrue(m['fixed_food_ceiling']);self.assertTrue(m['fixed_horizon_ceiling'])
    def test_missing_exposure_is_preserved(self):
        c=self.metric(False);c.update(food=17,fresh=1,fresh_attempted=3,all_fresh_acquired_tick=None)
        m=compare(c,self.metric());self.assertFalse(m['full_fresh_exposure_both']);self.assertFalse(m['shared_fresh_completion_endpoint'])
    def test_impossible_success_counts_and_boolean_counts_refused(self):
        for update in (dict(fresh=17),dict(food=33),dict(ticks=True),dict(death_tick=100)):
            m=self.metric();m.update(update)
            with self.assertRaises(AssertionError):compare(m,self.metric())
    def test_duplicate_acquisition_is_not_two_food(self):
        ev=[dict(tick=i,actor=0,decoded=[6,0,0],attempt=dict(success=1,packet=16),control=dict(mode='intact',rewrites=[])) for i in (1,2)]
        with self.assertRaises(AssertionError):summarize(dict(final=dict(events=ev)))
