import copy,unittest
from experiments.digital_memorysource14 import compile_program,probe,manifest
from experiments.digital_memorysource14_audit import endpoint

class MemorySource14(unittest.TestCase):
    def test_truth_endpoint_accepts_complete_bank_refuses_impossible_outputs(self):
        bank=manifest()['bank'];self.assertTrue(endpoint(bank))
        impossible=copy.deepcopy(bank)
        for row in impossible:
            for p in row['probes']:p['port']=0
        self.assertFalse(endpoint(impossible))
    def test_neutral_source_domain_and_missing_output_are_not_silently_repaired(self):
        for value in (-1,256,True):
            with self.assertRaises(AssertionError):compile_program(value)
        code=[[7,0,5] for _ in range(32)]
        with self.assertRaises(AssertionError):probe(code,0,0,0)
