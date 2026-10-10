import copy,unittest
from fractions import Fraction as F
from experiments.transmission_gate import ledger,panel,decision
from experiments.transmission_audit import audit

class TransmissionTests(unittest.TestCase):
    def test_full_denominator_and_simple_control(self):
        rows=panel();result=audit(rows)
        self.assertEqual(result['lever_strictly_dominates'],32)
        self.assertTrue(all(n>0 for n in decision(rows)['positive_bound_by_arm'].values()))
    def test_energy_creation_and_double_payment_rejected(self):
        for field in ('gross','replacement'):
            rows=copy.deepcopy(panel());rows[0]['arms']['gear'][field]='999'
            with self.assertRaises(AssertionError):audit(rows)
    def test_torque_gain_does_not_create_work(self):
        low=ledger(F(1),F(1,8),F(1,64),F(1,4),'gear')
        self.assertEqual(low['pulse_work'],'1')
        self.assertEqual(low['unused_potential'],'0')
        blocked=ledger(F(1),F(1,8),F(1,64),F(1,4),'direct')
        self.assertEqual(blocked['pulse_work'],'0')
