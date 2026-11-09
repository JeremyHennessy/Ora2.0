"""No-dispatch tests for the frozen continuation policy."""
from contextlib import contextmanager
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch, sentinel

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

    @contextmanager
    def _continuation_fixture(self, *, with_attempts=True, with_admissions=False,
                              with_accepted_evidence=True):
        ordered = gate.inventory()
        binding = gate.continuation_binding()
        authority = 'test-authorization'
        # Supply accepted evidence at the verification boundary without running science.
        report = {'rows': [
            {'index': i, 'status': 'accepted',
             'job_accounting': {'cpu_ticks': 0, 'wall_seconds': 0}}
            for i in range(8, 16)
        ] if with_accepted_evidence else []}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            checkout = root / 'checkout'
            source = checkout / 'experiments/al02_campaign_admission.py'
            status = root / 'automation/ora-codex/status.json'
            status.parent.mkdir(parents=True)
            status.write_text('{"status": "parked"}', encoding='utf-8')
            if with_attempts:
                for row in ordered[8:16]:
                    (root / row['attempt']).mkdir()

            pins = dict(binding['pins'], **{str(source): campaign.ADMISSION_SHA256})
            admissions = {}
            if with_admissions:
                for row in ordered[8:16]:
                    admissions[row['index']] = {
                        'command': [binding['python'], '-I', '-S', '-B', binding['worker'],
                                    str(root / row['attempt'] / '00-pending.json'), gate.TOKEN],
                        'pins': pins,
                        'identities': {
                            'binding_sha256': gate.CONTINUATION_BINDING_SHA256,
                            'package_sha256': gate.CONTINUATION_PACKAGE_SHA256,
                            'contexts_sha256': gate.CONTEXTS_SHA256,
                            'authorization_sha256': authority,
                        },
                        'terminal_pin': f"{row['index']:064x}",
                    }

            custody = Mock(FREE_MIN=0)
            custody.pinned_path.side_effect = [root, checkout]
            custody.digest.return_value = campaign.ADMISSION_SHA256
            custody.transaction.side_effect = AssertionError('Custody dispatch attempted')
            with (
                patch.multiple(gate, ROOT=root, STOP=root / 'STOP', CHECKOUT=checkout,
                               CONTINUATION_DESTINATION=root, __file__=str(source),
                               CONTINUATION_AUTHORIZATION_SHA256=authority),
                patch.object(gate, 'continuation_binding', return_value=binding),
                patch.object(gate, 'admitted') as admitted,
                patch.object(campaign, 'custody', custody),
                patch.object(campaign.subprocess, 'check_output',
                             return_value=binding['production_head']),
                patch.object(campaign, 'pilot_admissions', return_value=admissions),
                patch.object(campaign, 'analyze_committed_panel', return_value=report),
                patch.object(campaign.shutil, 'disk_usage', return_value=Mock(free=2**31)),
            ):
                yield root, ordered, admissions, admitted, custody

    def test_run_next_stops_before_claiming_or_dispatching(self):
        with (
            self._continuation_fixture(with_attempts=False) as (root, ordered, _, _, custody),
            patch.object(campaign, 'next_unclaimed', wraps=next_unclaimed) as select,
        ):
            (root / 'STOP').touch()

            self.assertIsNone(run_next(continuation=True))

            select.assert_not_called()
            custody.transaction.assert_not_called()
            for row in ordered[8:]:
                self.assertFalse((root / row['attempt']).exists(), row['attempt'])

    def test_run_next_hands_off_index_8_without_continuation_claims(self):
        binding = gate.continuation_binding()
        with self._continuation_fixture(with_attempts=False, with_accepted_evidence=False) as (
            root, ordered, _, _, custody
        ):
            checkout = root / 'checkout'
            source = checkout / 'experiments/al02_campaign_admission.py'
            pins = dict(binding['pins'], **{str(source): campaign.ADMISSION_SHA256})
            row = ordered[8]
            directory = root / row['attempt']
            command = [binding['python'], '-I', '-S', '-B', binding['worker'],
                       str(directory / '00-pending.json'), gate.TOKEN]
            custody.transaction.side_effect = None
            custody.transaction.return_value = sentinel.custody_result

            self.assertIs(run_next(continuation=True), sentinel.custody_result)

            custody.transaction.assert_called_once_with(
                directory, command=command, cwd=checkout, pins=pins,
                expected_account=gate.OWNER, context=row['context_sha256'],
                referee=None, consent=gate.TOKEN,
            )
            for row in ordered[8:]:
                self.assertFalse((root / row['attempt']).exists(), row['attempt'])

    def test_run_next_refuses_index_16_without_prior_batch_review(self):
        with (
            self._continuation_fixture() as (root, ordered, _, _, custody),
            patch.object(campaign, 'next_unclaimed', wraps=next_unclaimed) as select,
        ):
            with self.assertRaisesRegex(ValueError, '^Independent batch review absent$'):
                run_next(continuation=True)
            select.assert_called_once_with(root, ordered, list(range(8, 16)),
                                           stop=root / 'STOP', start=8)

            custody.transaction.assert_not_called()
            self.assertFalse((root / 'batch-008-review.json').exists())
            self.assertFalse((root / ordered[16]['attempt']).exists())

    def test_run_next_refuses_index_16_with_inconsistent_prior_batch_review(self):
        selected = []

        def record_selection(*args, **kwargs):
            row = next_unclaimed(*args, **kwargs)
            selected.append(row)
            return row

        with (
            self._continuation_fixture(with_admissions=True) as (
                root, ordered, admissions, admitted, custody
            ),
            patch.object(campaign, 'next_unclaimed', wraps=record_selection),
        ):
            review = campaign.batch_review(admissions, 8)
            review['start'] = 9
            (root / 'batch-008-review.json').write_text(json.dumps(review), encoding='utf-8')

            with self.assertRaises(ValueError) as error:
                run_next(continuation=True)

            self.assertEqual(str(error.exception), 'Independent batch review evidence differs')
            self.assertEqual(selected, [ordered[16]])
            admitted.assert_not_called()
            custody.transaction.assert_not_called()
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
