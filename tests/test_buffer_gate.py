from fractions import Fraction as F
import unittest
from experiments import buffer_gate as producer,buffer_audit as independent


class BufferTests(unittest.TestCase):
    def test_all_frozen_cases_match_independent_accounting(self):
        rows=producer.panel();self.assertEqual(rows,independent.panel())
        self.assertEqual(len(rows),128)
    def test_no_output_can_repay_high_upkeep_candidate(self):
        for row in independent.panel():
            if row['m']=='1/8':
                c=row['arms']['connected'];self.assertEqual(F(c['output']),0)
                self.assertLess(F(c['whole']),0)
    def test_rebuilt_contact_output_requires_paid_virgin_material(self):
        for row in independent.panel():
            for arm in row['arms'].values():
                if F(arm['fresh_output'])>0:
                    self.assertEqual(F(arm['repair']),F(3,4))
                    self.assertIsNotNone(arm['repair_tick'])
                    self.assertEqual(arm['scrap'],1)
                self.assertEqual(arm['raw']+arm['live']+arm['scrap'],10)
