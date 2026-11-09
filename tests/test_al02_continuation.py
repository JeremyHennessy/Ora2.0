"""No-dispatch tests for the frozen continuation policy."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from experiments import al02_campaign_admission as gate
from tools.al02_campaign_evidence import next_unclaimed
from tools.run_al02_campaign import run_next


class ContinuationPolicyTests(unittest.TestCase):
    def test_exact_artifacts_and_inactive_entry(self):
        binding = gate.continuation_binding()
        self.assertEqual(binding['budget']['pairs'],120)
        self.assertEqual(gate.continuation_spec()['batches'],
                         [list(range(i,i+8)) for i in range(8,128,8)])
        with self.assertRaisesRegex(ValueError,'scientific authorization absent'):
            run_next(continuation=True)

    def test_order_completion_stop_and_unresolved_claim(self):
        rows = gate.inventory()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            stop = root/'STOP'
            for i in range(8,128):
                self.assertEqual(next_unclaimed(root,rows,list(range(8,i)),
                                                stop=stop,start=8),rows[i])
                (root/rows[i]['attempt']).mkdir()
                with self.assertRaisesRegex(ValueError,'Unreconciled attempt claim'):
                    next_unclaimed(root,rows,list(range(8,i)),stop=stop,start=8)
            self.assertIsNone(next_unclaimed(root,rows,list(range(8,128)),
                                             stop=stop,start=8))
            stop.touch()
            self.assertIsNone(next_unclaimed(root,rows,[],stop=stop,start=8))
