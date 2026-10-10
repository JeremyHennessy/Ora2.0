import copy
import unittest
from experiments import export_gate as gate, export_audit as independent

class ExportGateTests(unittest.TestCase):
    def test_paid_reconstruction_and_spatial_export_in_every_arm(self):
        for arm in gate.ARMS:
            result=gate.certificate(arm)
            score=independent.verify_certificate(result)
            self.assertEqual(score['linked_surplus'],2)
            self.assertEqual(score['post_linked_surplus'],2)
            self.assertEqual(score['whole_stored_work'],14)
            self.assertTrue(all(site==1 for site,loaded in zip(result['load_sites'],result['loaded']) if loaded))

    def test_loaded_export_is_not_one_way(self):
        state=(5,1,0,7,0,0,3)
        self.assertIsNone(gate.transition(state,('load',1,-1),'candidate'))
        moved,_,_=gate.transition(state,('lhop',3,1),'candidate')
        self.assertIsNotNone(gate.transition(moved,('load',0,-1),'candidate'))
        self.assertEqual(gate.transition(moved,('lhop',2,1),'candidate')[0],state)
        self.assertIsNotNone(gate.transition(state,('load',1,-1),'bulk-diagnostic'))

    def test_forged_output_or_transport_rejected(self):
        for field in ('score','position'):
            record=copy.deepcopy(gate.certificate('candidate'))
            if field=='score':
                record['score']['linked_surplus']+=1
            else:
                record['rows'][3]['after'][3]-=1
            with self.assertRaises(AssertionError):
                independent.verify_certificate(record)

if __name__=='__main__':
    unittest.main()
