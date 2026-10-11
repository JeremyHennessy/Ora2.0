import copy,unittest
from experiments.digital_ordinary_admission10 import history
from experiments.digital_ordinary_admission10_audit import audit,endpoint
from experiments.digital_singlecopy09 import h

class OrdinaryAdmission10(unittest.TestCase):
    def test_paid_positive_and_impossible_same_endpoint(self):
        positive=audit(history(25890,'matched_double'))
        impossible=audit(history(25890,'disabled_double'))
        simpler=audit(history(25890,'actual_ordinary'))
        self.assertTrue(endpoint(positive));self.assertFalse(endpoint(impossible));self.assertTrue(endpoint(simpler))
        self.assertEqual(impossible['births'],0)
        self.assertEqual(positive['formation_cost'],42);self.assertEqual(simpler['formation_cost'],34)

    def test_rehashed_ancestry_and_configuration_forgery_refused(self):
        row=history(25890,'matched_double');bad=copy.deepcopy(row)
        event=next(e for e in bad['history']['final']['events'] if 'writes' in e)
        event['writes'][0]['source_value']^=1;bad['history']['hash']=h(bad['history']['final'])
        with self.assertRaises(AssertionError):audit(bad)
        bad=copy.deepcopy(row);bad['configuration']='actual_ordinary'
        with self.assertRaises(AssertionError):audit(bad)
        with self.assertRaises(AssertionError):history(True,'matched_double')
