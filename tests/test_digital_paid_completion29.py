import unittest
from experiments.digital_paid_completion29 import improvement,REFERENCE_ROLES

class PaidCompletionTests(unittest.TestCase):
    def score(self,tick=300,formation=55):
        return dict(completed=tick is not None,completion_tick=tick,paid_work_to_completion=None if tick is None else formation+tick,formation_cost=formation,successful_food=0 if tick is None else 32,fresh_successes=0 if tick is None else 16)
    def refs(self):return {r:self.score() for r in REFERENCE_ROLES}
    def test_failure_never_wins_by_lower_bill(self):self.assertFalse(improvement(self.score(None,19),self.refs()))
    def test_faster_but_more_construction_is_not_paid_improvement(self):self.assertFalse(improvement(self.score(280,90),self.refs()))
    def test_cheaper_but_slower_is_not_latency_improvement(self):self.assertFalse(improvement(self.score(310,19),self.refs()))
    def test_exact_reference_envelope_and_strict_gains(self):
        self.assertFalse(improvement(self.score(),self.refs()));self.assertTrue(improvement(self.score(280,55),self.refs()))
        refs=self.refs();refs['affine7']=self.score(270)
        self.assertFalse(improvement(self.score(280),refs))
    def test_partial_completion_and_boolean_tick_refused(self):
        for k,v in (('successful_food',31),('fresh_successes',15),('completion_tick',True)):
            c=self.score();c[k]=v
            with self.assertRaises(AssertionError):improvement(c,self.refs())
    def test_omitted_reactive_reference_refused(self):
        refs=self.refs();del refs['affine7']
        with self.assertRaises(AssertionError):improvement(self.score(200),refs)
