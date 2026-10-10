import copy
import unittest
from experiments.export_world import trajectory,ALPHABET
from experiments.export_panel_audit import audit_world

class ExportWorldTests(unittest.TestCase):
    def test_independent_full_cursor_and_identity_replay(self):
        self.assertEqual(len(ALPHABET),96)
        for arm in ('candidate','independent','shuffled','bulk-diagnostic'):
            record=trajectory(0,arm)
            self.assertEqual(audit_world(record),record['score'])

    def test_forged_ancestry_and_rejected_draw_detected(self):
        record=trajectory(1,'candidate')
        for field in ('objects','draw_sha256'):
            forged=copy.deepcopy(record)
            if field=='objects':forged['objects'][0]['parent']=0
            else:forged[field]='forged'
            with self.assertRaises(AssertionError):audit_world(forged)

if __name__=='__main__':unittest.main()
