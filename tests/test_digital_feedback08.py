import unittest
from experiments.digital_feedback08 import study,probe
from experiments.digital_feedback08_audit import audit

class FeedbackPreflight(unittest.TestCase):
    def test_complete_neighborhood_and_counterfactual_refusal(self):
        data=study();self.assertEqual(audit(data)['variants'],558)
        data['variants'][0]['probes'][0]['port']=99
        with self.assertRaises(AssertionError): audit(data)
        data=study();data['variants'][0]['address']=False
        with self.assertRaises(AssertionError): audit(data)

    def test_typed_inputs_and_bounded_no_action(self):
        with self.assertRaises(AssertionError): probe([7,0,0],True,0,0)
        self.assertEqual(probe([7,0,0],0,0,0)['status'],'bounded_no_action')
