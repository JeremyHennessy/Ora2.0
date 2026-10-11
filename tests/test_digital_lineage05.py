import copy,unittest
from experiments.digital_lineage05_audit import endpoint,ANCESTOR,audit
from experiments.digital_lineage05 import history

class Lineage05(unittest.TestCase):
    def test_same_endpoint_positive_and_impossible_transmission(self):
        genome=ANCESTOR[:];genome[0]=1
        witness=[dict(id=0,parent=None,genome=ANCESTOR,successes=[],children=[1]),
                 dict(id=1,parent=0,genome=genome,successes=[(1,0),(1,0),(2,1),(2,1)],children=[2]),
                 dict(id=2,parent=1,genome=genome,successes=[(1,0),(1,0),(2,1),(2,1)],children=[3]),
                 dict(id=3,parent=2,genome=genome,successes=[],children=[])]
        self.assertEqual(len(endpoint(witness)),1)
        for failure in ('ordinary','copy','capacity','single_port'):
            bad=copy.deepcopy(witness)
            if failure=='ordinary':bad[1]['genome']=ANCESTOR
            if failure=='copy':bad[2]['genome']=ANCESTOR
            if failure=='capacity':bad[2]['children']=[]
            if failure=='single_port':bad[1]['successes']=[(1,0)]*4
            self.assertEqual(endpoint(bad),[])

    def test_full_interpreter_precedes_endpoint(self):
        # Historical ordinary software fixture; no primary/reserve execution.
        row=history(25190);result=audit(row)
        self.assertGreater(result['descendant_births'],0)
        self.assertEqual(result['qualified_pairs'],0)
        bad=copy.deepcopy(row);bad['final']['formation'][0]['energy']=True
        with self.assertRaises(AssertionError):audit(bad)

if __name__=='__main__':unittest.main()
