import copy,unittest
from experiments.digital_branch_source30 import candidate,manifest
from experiments.digital_branch_source30_audit import audit

class BranchSourceTests(unittest.TestCase):
    def test_complete_independent_catalogue_and_branch_denominator(self):
        a=audit(manifest());self.assertEqual(a['branch_target_counts'],{0:28,1:21,5:7});self.assertEqual(a['branch_register_counts'],{0:42,1:14})
    def test_identity_types_and_range_refused(self):
        for i in (True,False,-1,56,1.0,'1'):
            with self.assertRaises(ValueError):candidate(i)
    def test_returned_programs_do_not_modify_ancestor_or_other_candidates(self):
        a=candidate(0);old=copy.deepcopy(candidate(1));a['program'][0][0]=31;self.assertEqual(candidate(1),old);self.assertEqual(candidate(0)['program'][0][0],4)
    def test_omitted_candidate_and_false_ancestry_refused(self):
        data=manifest();data['candidates'].pop()
        with self.assertRaises(AssertionError):audit(data)
        data=manifest();data['candidates'][0]['intermediate_program_sha256']='0'*64
        with self.assertRaises(AssertionError):audit(data)
        data=manifest();data['source25_replaced']=True
        with self.assertRaises(AssertionError):audit(data)
    def test_operand_tuning_and_primary_promotion_refused(self):
        for field in ('operand','promotion'):
            data=manifest()
            if field=='operand':data['candidates'][0]['program'][6][2]=7
            else:data['candidates'][0]['primary_admitted']=True
            with self.assertRaises(AssertionError):audit(data)
