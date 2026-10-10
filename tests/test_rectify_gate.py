from fractions import Fraction as F
import unittest
from experiments import rectify_gate as producer,rectify_audit as auditor


class RectifyTests(unittest.TestCase):
    def test_all_registered_cases_agree_and_conserve_resources(self):
        rows=producer.panel();self.assertEqual(rows,auditor.panel());self.assertEqual(len(rows),384)
        for row in rows:
            for arm in row['arms'].values():
                self.assertEqual(arm['live']+arm['raw']+arm['spare']+arm['scrap'],5)
                self.assertEqual(arm['allowance']+F(arm['source']),arm['returned']+arm['capital']+F(arm['heat'])+F(arm['upkeep'])+F(arm['patch'])+F(arm['reserve']))

    def test_unbuilt_damage_does_not_force_independent_repair(self):
        a=producer.arm(1,1,F(1,32),4,2,F(1,4),3,1)
        self.assertEqual(a['patch'],'0');self.assertEqual(a['spare'],1);self.assertEqual(a['raw'],3)

    def test_failed_upkeep_is_not_reported_as_positive_surplus(self):
        a=producer.arm(1,0,F(100),1,2,F(1,4),0,0)
        self.assertFalse(a['fundable']);self.assertIsNone(a['whole']);self.assertIsNone(a['post'])
