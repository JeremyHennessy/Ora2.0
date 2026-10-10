from fractions import Fraction as F
import unittest
from experiments import buffer_gate as producer,buffer_audit as independent


def value(encoded):
    return F(int(encoded['numerator_hex'],16),int(encoded['denominator_hex'],16)) if isinstance(encoded,dict) else F(encoded)


class BufferTests(unittest.TestCase):
    def test_all_frozen_cases_match_independent_accounting(self):
        rows=producer.panel();self.assertEqual(rows,independent.panel())
        self.assertEqual(len(rows),128)
    def test_no_output_can_repay_high_upkeep_candidate(self):
        for row in independent.panel():
            if row['m']=='1/8':
                c=row['arms']['connected'];self.assertEqual(value(c['output']),0)
                self.assertLess(value(c['whole']),0)
    def test_rebuilt_contact_output_requires_paid_virgin_material(self):
        for row in independent.panel():
            for arm in row['arms'].values():
                if value(arm['fresh_output'])>0:
                    self.assertEqual(value(arm['repair']),F(3,4))
                    self.assertIsNotNone(arm['repair_tick'])
                    self.assertEqual(arm['scrap'],1)
                self.assertEqual(arm['raw']+arm['live']+arm['scrap'],10)

    def test_large_ratio_roundtrip_keeps_decimal_guard(self):
        import sys
        before=sys.get_int_max_str_digits()
        exact=F((1<<15000)+1,(1<<14900)+3)
        self.assertEqual(value(producer.ratio(exact)),exact)
        self.assertEqual(value(independent.ratio(exact)),exact)
        self.assertEqual(sys.get_int_max_str_digits(),before)
