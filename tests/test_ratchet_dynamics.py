import copy
import unittest
from experiments.ratchet_dynamics import world
from experiments.ratchet_dynamics_audit import audit_record


class RatchetDynamics(unittest.TestCase):
    def test_disjoint_authored_all_arms(self):
        for arm in ('candidate','uncoupled','isotropic','equilibrium'):
            record=world(78999,arm,(1,1,1))
            row=audit_record(record)
            self.assertEqual(row['arm'],arm)
            self.assertEqual(record['attempts'],4096)

    def test_forged_noise_refused(self):
        record=world(78999,'candidate',(1,1,1))
        record['draw_sha256']='0'*64
        with self.assertRaises(ValueError):audit_record(record)

    def test_forged_ancestry_refused(self):
        record=copy.deepcopy(world(78999,'equilibrium',(1,1,1)))
        record['final']['objects'][0]['construction_work']=0
        with self.assertRaises(ValueError):audit_record(record)


if __name__=='__main__':unittest.main()
