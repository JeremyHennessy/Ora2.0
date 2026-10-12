import copy
import unittest
from experiments.digital_function56 import edge_reason,diagnose


class Function56Tests(unittest.TestCase):
    def fixture(self):
        return ({'parent':1,'child':2,'tick':20,'parent_site1_before_birth':[10],
                 'eligible_parent':True,'transmitted_function_association':True},
                {'1':{'birth_words':[1,2],'site1_success_ticks':[10]},
                 '2':{'birth_words':[1,2],'site1_success_ticks':[30]}})

    def test_association(self):
        e,a=self.fixture();self.assertEqual(edge_reason(e,a),'registered_association')

    def test_late_parent_function(self):
        e,a=self.fixture();a['1']['site1_success_ticks']=[21];e.update(parent_site1_before_birth=[],eligible_parent=False,transmitted_function_association=False)
        self.assertEqual(edge_reason(e,a),'no_qualified_parent_function_before_birth')

    def test_changed_child(self):
        e,a=self.fixture();a['2']['birth_words']=[1,3];e.update(eligible_parent=False,transmitted_function_association=False)
        self.assertEqual(edge_reason(e,a),'changed_child_program')

    def test_unstable_parent(self):
        e,a=self.fixture();e.update(eligible_parent=False,transmitted_function_association=False)
        self.assertEqual(edge_reason(e,a),'parent_unstable_at_division')

    def test_child_no_qualified_success(self):
        e,a=self.fixture();a['2']['site1_success_ticks']=[];e['transmitted_function_association']=False
        self.assertEqual(edge_reason(e,a),'exact_child_without_qualified_function')

    def test_parent_timing_mismatch_refused(self):
        e,a=self.fixture();e['parent_site1_before_birth']=[]
        with self.assertRaises(AssertionError):edge_reason(e,a)

    def test_changed_child_false_eligibility_refused(self):
        e,a=self.fixture();a['2']['birth_words']=[1,3]
        with self.assertRaises(AssertionError):edge_reason(e,a)

    def test_empty_history_energy_bookkeeping(self):
        person=dict(parent=None,generation=0,birth_words=[0]*27,site1_success_ticks=[],alive=True,food_by_site=[0]*4,births=0,instructions=0)
        row=dict(seed=55000,mode='faithful',final=dict(events=[],free=list(range(469))))
        proof=dict(lineage=dict(actors={0:person},edges=[]),summary=dict(unused_food=64,births=0,successful_food=0))
        result=diagnose(row,proof);self.assertEqual(result['actors']['0']['endpoint_energy'],12)
        bad=copy.deepcopy(proof);bad['lineage']['actors'][0]['food_by_site'][0]=1
        with self.assertRaises(AssertionError):diagnose(row,bad)
