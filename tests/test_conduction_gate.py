import unittest
from fractions import Fraction as F
from experiments import conduction_gate as producer, conduction_audit as independent


class ConductionTests(unittest.TestCase):
    def test_entire_registered_panel_agrees_and_no_segmentation_advantage(self):
        rows=producer.panel();self.assertEqual(rows,independent.panel());self.assertEqual(len(rows),972)
        for row in rows:
            a,b=row['segmented'],row['continuous']
            self.assertEqual(a['fundable'],b['fundable'])
            if a['fundable']:
                self.assertEqual(F(a['whole_net'])-F(b['whole_net']),-2*row['b'])
                self.assertEqual(a['post_net'],b['post_net'])

    def test_heat_is_not_exported_work_and_endowment_is_not_double_counted(self):
        a=producer.arm(1,0,0,0,2,6)
        self.assertTrue(a['fundable']);self.assertEqual(F(a['source_used']),F(57,2))
        self.assertEqual(F(a['resistive_heat']),F(57,4))
        self.assertEqual(F(a['reserve']),F(53,4));self.assertEqual(F(a['whole_net']),F(37,4))
        self.assertEqual((a['live_material'],a['virgin_material'],a['scrap_material']),(4,0,1))

    def test_an_unfundable_upkeep_certificate_stops_before_damage(self):
        a=producer.arm(1,0,1,0,8,6)
        self.assertFalse(a['fundable']);self.assertEqual(a['failure'],'maintenance-pre-1')
        self.assertIsNone(a['whole_net']);self.assertEqual(a['source_used'],'6')
        self.assertEqual((a['live_material'],a['virgin_material'],a['scrap_material']),(4,1,0))
