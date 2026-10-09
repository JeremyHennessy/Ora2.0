import copy
import unittest
from experiments.condense_dynamics import world
from experiments.condense_dynamics_audit import audit_record


class CondenseDynamics(unittest.TestCase):
    def test_disjoint_authored_arms(self):
        for arm in ('candidate','affinity-ghost','catalysis-ghost','passive'):
            record=world(79999,0,arm)
            self.assertEqual(audit_record(record)['arm'],arm)
            state=record['final']['states'][-1]
            self.assertEqual(state[4],4-state[0])

    def test_forged_ancestry_and_noise(self):
        for field in ('ancestry','noise'):
            r=copy.deepcopy(world(79999,0,'candidate'))
            if field=='ancestry':r['final']['objects'][0]['parent']=99999
            else:r['draw_sha256']='0'*64
            with self.assertRaises(ValueError):audit_record(r)


if __name__=='__main__':unittest.main()
