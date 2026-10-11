import copy
import unittest
from experiments.correlation_capacity import census
from experiments.correlation_capacity_audit import audit


class CorrelationCapacityTests(unittest.TestCase):
    def test_exact_ensemble_and_source_limits(self):
        result=audit(census())
        self.assertEqual(result['words_examined'],21760)
        self.assertEqual(result['zero_input_capacity'],6)
        self.assertFalse(result['actual_control_profitability_verified'])

    def test_refuse_omitted_costs_fake_work_and_mismatched_shuffle(self):
        for fault in ('cost','work','shuffle','entropy','rows','admission'):
            data=copy.deepcopy(census())
            if fault=='cost':data['rows'][0]['unknown_costs']=[]
            elif fault=='work':data['rows'][0]['measured_work']=data['rows'][0]['work_ceiling']
            elif fault=='shuffle':data['full_input_shuffle_equal_resource_control']=True
            elif fault=='entropy':data['rows'][0]['joint_entropy']+=0.01
            elif fault=='rows':data['rows'].pop()
            elif fault=='admission':data['rows'][0]['mechanism_admitted']=True
            with self.subTest(fault=fault),self.assertRaises(AssertionError):audit(data)
