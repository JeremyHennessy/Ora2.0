import copy
import unittest
from experiments.maintain_world import world
from experiments.maintain_panel_audit import interpret

class History(unittest.TestCase):
    def test_fixture_accounting_and_genealogy(self):
        for arm in ('candidate','independent','annealed'):
            r=world(0,arm,'fixture',128,64)
            self.assertEqual(interpret(r,'fixture'),r['score'])
            forged=copy.deepcopy(r);forged['score']['whole_surplus']+=1
            with self.assertRaises(AssertionError):interpret(forged,'fixture')

    def test_rejected_draws_and_identity_mutations_detected(self):
        r=world(1,'candidate','fixture',128,64)
        self.assertEqual(r,world(1,'candidate','fixture',128,64))
        for key in ('draw_sha256','random_sha256'):
            forged=copy.deepcopy(r);forged[key]='forged'
            with self.assertRaises(AssertionError):interpret(forged,'fixture')
        forged=copy.deepcopy(r);forged['events'][0][4]=forged['events'][0][3]
        with self.assertRaises(AssertionError):interpret(forged,'fixture')
if __name__=='__main__':unittest.main()
