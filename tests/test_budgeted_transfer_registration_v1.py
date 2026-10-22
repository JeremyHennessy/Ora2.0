"""Registration/falsifier arithmetic only; never imports a VM or executes source."""
import json
from pathlib import Path
import tempfile
import unittest
from fractions import Fraction
from experiments.digital_budgeted_transfer_registration_v1 import (
    ROOT,MANIFEST,verify,canonical,sign_probability,primary_authority)

class Registration(unittest.TestCase):
    def setUp(self):self.raw=(ROOT/MANIFEST).read_bytes()

    def test_exact_seal_and_disclosed_non_discovery(self):
        r=verify(self.raw)
        self.assertEqual(r['candidate']['prior_candidate_executions'],0)
        self.assertEqual(r['primary_plan']['arms'],8)
        self.assertEqual(r['primary_plan']['contrasts'],7)
        self.assertEqual(len(r['channel_audit']),9)
        self.assertIn('authored',r['candidate']['origin'])

    def test_resealed_candidate_or_status_or_threshold_tampering_rejected(self):
        for field in ['candidate','status','statistics']:
            r=json.loads(self.raw)
            if field=='candidate':r['candidate']['code'][3]=[4,0,1]
            elif field=='status':r['execution_gate']['primary_admitted']=True
            else:r['primary_plan']['independent_units']=63
            with self.assertRaises(ValueError):verify(canonical(r)+b'\n')

    def test_changed_dependency_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises((ValueError,FileNotFoundError)):verify(self.raw,Path(folder))

    def test_primary_cannot_be_started_by_enrollment_or_a_token(self):
        for token in [None,{'approved':True},'NEW-INTERFACE-FIXTURES-ONLY']:
            with self.assertRaises(RuntimeError):primary_authority(token)

    def test_sign_test_ties_not_positive_evidence_and_effect_uses_all_units(self):
        r=sign_probability([1]*8+[0]*56)
        self.assertEqual(r['p'],Fraction(1,256))
        self.assertEqual(r['mean'],Fraction(1,8));self.assertFalse(r['passes'])
        self.assertTrue(sign_probability([1]*64)['passes'])
        self.assertEqual(sign_probability([0]*64)['p'],1)
        self.assertFalse(sign_probability([-1]*64)['passes'])

    def test_no_missing_boolean_or_out_of_range_unit(self):
        for data in [[1]*63,[True]*64,[5]*64,[None]*64]:
            with self.assertRaises(ValueError):sign_probability(data)

if __name__=='__main__':unittest.main()
