import copy, unittest
from experiments.digital_affine_source18 import compile_program, manifest, probe
from experiments.digital_affine_source18_audit import audit, endpoint

class AffineSource18(unittest.TestCase):
    def test_same_endpoint_accepts_complete_source_and_refuses_impossible_bank(self):
        record=manifest(); self.assertTrue(audit(record)['verified'])
        bad=copy.deepcopy(record)
        for row in bad['bank']:
            for p in row['probes']: p['port']=0
        self.assertFalse(endpoint(bad['bank']))
        for path in ('identity','port'):
            bad=copy.deepcopy(record)
            if path=='identity': bad['bank'][1]['identity']=True
            else: bad['bank'][1]['probes'][0]['port']=True
            self.assertFalse(endpoint(bad['bank']))
            with self.assertRaises(AssertionError): audit(bad)

    def test_source_domain_missing_output_and_forged_trace_refused(self):
        for value in (-1,8,True):
            with self.assertRaises(AssertionError): compile_program(value)
        with self.assertRaises(AssertionError): probe([[18,0,0] for _ in range(13)],0,0)
        bad=manifest(); bad['bank'][0]['probes'][0]['trace'][0]['registers'][0]=1
        with self.assertRaises(AssertionError): audit(bad)
