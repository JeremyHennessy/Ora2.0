import copy, unittest
from experiments.assemble_world import trajectory
from experiments import window_gate, window_audit

class WindowTests(unittest.TestCase):
    def test_inventory_charge_and_independent_certificate(self):
        # Authored old-law witness is a fixture, not a panel or science sample.
        r=trajectory(0,'candidate',True)
        self.assertEqual(window_gate.measure(r),window_audit.inspect(r))
        self.assertEqual(len(window_gate.measure(r)['untouched_tokens']),6)

    def test_charge_fate_tampering_differs(self):
        r=trajectory(0,'candidate',True);result=window_gate.measure(r)
        self.assertEqual(result['fresh_charges'][0]['outcome'],'fresh_load')
        altered=copy.deepcopy(result);altered['fresh_charges'][0]['outcome']='reverse_drive'
        self.assertNotEqual(altered,window_audit.inspect(r))
