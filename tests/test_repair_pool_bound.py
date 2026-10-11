import copy
from fractions import Fraction
import unittest
from experiments.repair_pool_bound import case,census
from experiments.repair_pool_bound_audit import audit


class RepairPoolBoundTests(unittest.TestCase):
    def test_reserve_handicap_and_unused_work(self):
        row=case(6,3,4,1)
        self.assertEqual(row['covered_losses'],2)
        self.assertEqual(row['allocation'],[3,3,0,0])
        self.assertEqual(row['independent_output'],[8,1])
        # Uniform one-unit reserves at each site cover no loss; this stronger
        # control covers two, and retains all unspent work in its output.
        self.assertEqual(row['extra_cost_frontier'],[1,1])
        row=case(12,3,4,1)
        self.assertEqual(row['extra_cost_frontier'],[-1,1])

    def test_funding_and_strict_frontier(self):
        row=case(3,3,4,1)
        self.assertFalse(row['pool_funded'])
        self.assertTrue(row['positive_frontier'])
        row=case(4,3,4,1)
        cap=Fraction(*row['extra_cost_frontier'])
        independent=Fraction(*row['independent_output'])
        self.assertEqual(row['pool_output_before_extra_cost']-cap,independent)
        for values in ((True,3,4,1),(4,0,4,1),(4,3,4,0)):
            with self.assertRaises(ValueError):case(*values)

    def test_full_census_and_evidence_refusals(self):
        payload=census();result=audit(payload)
        self.assertEqual(result['cases'],1728)
        self.assertEqual(sum(result[x] for x in ('funded_positive_frontier',
                         'funded_nonpositive_frontier','unfunded_pool')),1728)
        for mutation in ('admission','output','witness','duplicate','missing','float'):
            broken=copy.deepcopy(payload)
            if mutation=='admission':broken['mechanism_admitted']=True
            elif mutation=='output':broken['cases'][0]['independent_output']=[0,1]
            elif mutation=='witness':broken['cases'][0]['allocation']=[2,0,0,0]
            elif mutation=='duplicate':broken['cases'][1]=broken['cases'][0]
            elif mutation=='missing':broken['cases'].pop()
            elif mutation=='float':broken['cases'][0]['stock']=1.0
            with self.assertRaises(ValueError):audit(broken)


if __name__=='__main__':unittest.main()
