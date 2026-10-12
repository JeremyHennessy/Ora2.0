import unittest
from experiments.digital_neutral_catalogue25 import candidate,PARENT

class NeutralCatalogue(unittest.TestCase):
    def test_exhaustive_single_change_and_order(self):
        baseline=sum((list(t) for t in PARENT),[]);pairs=[]
        for i in range(744):
            row=candidate(i);flat=sum(row['program'],[]);changes=[(n,v) for n,v in enumerate(flat) if v!=baseline[n]]
            self.assertEqual(len(changes),1);self.assertEqual(row['program'][:5],[list(t) for t in PARENT[:5]]);pairs.extend(changes)
        self.assertEqual(pairs,sorted((n,v) for n in range(15,39) for v in range(32) if v!=baseline[n]))

    def test_aliased_or_out_of_range_identity_refused(self):
        for x in (True,False,-1,744,0.0,'0',None):
            with self.subTest(x=x):
                with self.assertRaises(ValueError):candidate(x)

    def test_parent_and_sibling_cannot_be_changed_by_caller(self):
        first=candidate(0);original=candidate(0);sibling=candidate(1)
        first['program'][0][0]=31;first['mutation']['old']=31
        self.assertEqual(candidate(0),original);self.assertEqual(candidate(1),sibling);self.assertEqual(PARENT[0],(4,1,1))
