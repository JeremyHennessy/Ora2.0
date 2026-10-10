import copy
import unittest
from experiments import thermal_gate as producer
from experiments import thermal_audit as independent


class ThermalGateTests(unittest.TestCase):
    def test_costs_pay_whole_and_post_damage_bills(self):
        for c,n in ((3,10),(4,11),(5,12)):
            r=producer.record(c,'candidate');self.assertEqual(r['witness']['net_cycles'],n)
            self.assertGreater(r['witness']['whole_surplus'],0)
            self.assertEqual(r['witness']['post_damage_surplus'],1)
            self.assertTrue(independent.check_record(r))

    def test_impossible_cost_stops_candidate_but_not_independent_fluctuation(self):
        self.assertFalse(producer.record(6,'candidate')['possible'])
        r=producer.record(12,'independent');self.assertTrue(independent.check_record(r))
        self.assertEqual(r['witness']['net_cycles'],26)

    def test_shuffle_contains_a_working_positive_null(self):
        self.assertTrue(independent.check_record(producer.record(3,'shuffled-working')))
        self.assertFalse(independent.check_record(producer.record(3,'shuffled-reversed')))

    def test_free_payment_and_retained_identity_are_refused(self):
        original=producer.record(3,'candidate')
        for field in ('energy','identity','rate'):
            r=copy.deepcopy(original)
            if field=='energy':r['witness']['states'][-1][2]+=1
            elif field=='identity':r['witness']['bodies'][-1]['parent']=None
            else:r['physical']['rate_signatures']+=1
            with self.assertRaises(ValueError):independent.check_record(r)
