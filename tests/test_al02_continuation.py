"""No-dispatch tests for the frozen continuation policy."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from experiments import al02_campaign_admission as gate
from tools import run_al02_campaign as campaign
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

    def test_run_next_refuses_index_16_without_prior_batch_review(self):
        ordered = gate.inventory()
        binding = gate.continuation_binding()
        authority = 'test-authorization'
        # Supply accepted evidence at the verification boundary without running science.
        report = {'rows': [
            {'index': i, 'status': 'accepted',
             'job_accounting': {'cpu_ticks': 0, 'wall_seconds': 0}}
            for i in range(8, 16)
        ]}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            checkout = root / 'checkout'
            source = checkout / 'experiments/al02_campaign_admission.py'
            status = root / 'automation/ora-codex/status.json'
            status.parent.mkdir(parents=True)
            status.write_text('{"status": "parked"}', encoding='utf-8')
            for row in ordered[8:16]:
                (root / row['attempt']).mkdir()

            custody = Mock(FREE_MIN=0)
            custody.pinned_path.side_effect = [root, checkout]
            custody.digest.return_value = campaign.ADMISSION_SHA256
            custody.transaction.side_effect = AssertionError('Custody dispatch attempted')
            with (
                patch.multiple(gate, ROOT=root, STOP=root / 'STOP', CHECKOUT=checkout,
                               CONTINUATION_DESTINATION=root, __file__=str(source),
                               CONTINUATION_AUTHORIZATION_SHA256=authority),
                patch.object(gate, 'continuation_binding', return_value=binding),
                patch.object(gate, 'admitted'),
                patch.object(campaign, 'custody', custody),
                patch.object(campaign.subprocess, 'check_output',
                             return_value=binding['production_head']),
                patch.object(campaign, 'pilot_admissions', return_value={}),
                patch.object(campaign, 'analyze_committed_panel', return_value=report),
                patch.object(campaign.shutil, 'disk_usage', return_value=Mock(free=2**31)),
                patch.object(campaign, 'next_unclaimed', wraps=next_unclaimed) as select,
            ):
                with self.assertRaisesRegex(ValueError, '^Independent batch review absent$'):
                    run_next(continuation=True)
                select.assert_called_once_with(root, ordered, list(range(8, 16)),
                                               stop=root / 'STOP', start=8)

            custody.transaction.assert_not_called()
            self.assertFalse((root / 'batch-008-review.json').exists())
            self.assertFalse((root / ordered[16]['attempt']).exists())

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
