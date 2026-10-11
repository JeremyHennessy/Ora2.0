import copy,unittest
from experiments.digital_variation11_audit import transmission_endpoint,audit
from experiments.digital_variation11 import history
from experiments.digital_singlecopy09 import h

class Variation11(unittest.TestCase):
    def test_transmission_measurement_positive_impossible_same_endpoint(self):
        self.assertTrue(transmission_endpoint(1,1,1,True,True))
        self.assertFalse(transmission_endpoint(1,1,1,False,True))
        self.assertFalse(transmission_endpoint(1,1,0,True,True))
        self.assertFalse(transmission_endpoint(1,1,1,True,False))

    def test_complete_ordinary_ancestry_and_rehashed_forgery(self):
        record=history(25900,'faithful');metrics=audit(record)
        self.assertTrue(metrics['ordinary_endpoint']);self.assertEqual(metrics['lineages']['qualified_pairs'],[])
        self.assertEqual(metrics['lineages']['born_entities'],metrics['births'])
        bad=copy.deepcopy(record);e=next(e for e in bad['history']['final']['events'] if 'birth' in e)
        e['birth']['child']['parent']=99;bad['history']['hash']=h(bad['history']['final'])
        with self.assertRaises(AssertionError):audit(bad)
