import unittest
from experiments.digital_clocked16 import program
from experiments.digital_clocked16_audit import expected_program
from experiments.digital_contingency15_endpoint import endpoint

class ClockedFixtures(unittest.TestCase):
    def test_complete_formation_and_fixed_clock(self):
        code = program()
        self.assertEqual(code, expected_program())
        self.assertEqual(len(code),32)
        self.assertEqual(128-(3*len(code)+16),16)
        self.assertTrue(all(0<=x<32 for triple in code for x in triple))
        self.assertEqual(code[19],[6,0,0])
        self.assertEqual(code[31],[7,0,19])
        self.assertFalse(any(t[0] in (0,1,9,10,12,13,14,15,16) for t in code))
    def test_same_typed_endpoint_witness_and_impossible(self):
        row=dict(verified=True,post_food=12,fresh_attempts=16,ticks=300)
        self.assertTrue(endpoint(row,12))
        self.assertFalse(endpoint(dict(row,fresh_attempts=15),12))
        self.assertFalse(endpoint(dict(row,ticks=271),12))
        self.assertFalse(endpoint(dict(row,post_food=True),1))
        self.assertFalse(endpoint(row,True))
