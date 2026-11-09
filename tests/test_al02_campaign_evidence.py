import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from unittest import TestCase

from experiments.al02_one_pair import CONTEXT, CONTEXT_SHA256, SEED
from tools.al02_campaign_evidence import analyze_committed_panel, next_unclaimed, verify_attempt
from tools.al02_natural_b_analysis import contexts


class CampaignEvidenceTests(TestCase):
    def verify_historical(self, directory, **changes):
        source = Path('D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3')
        pending = json.loads((source/'00-pending.json').read_bytes())
        command = pending['command']
        if directory != source:
            # Tamper fixtures still exercise the trusted original receipt chain.
            command = [*command[:5], str(directory/'00-pending.json'), command[6]]
        args = dict(command=command, pins=pending['pins'], identities=pending['release_identities'],
            terminal_pin='62ea61cca38024ccc1a499c9eaa329dfd8e4c1d6fe2dccd1599ac42213772241')
        args.update(changes)
        return verify_attempt(directory,dict(index=0,context=CONTEXT,context_sha256=CONTEXT_SHA256,
                                            seed=SEED,attempt='attempt-v3'),**args)

    def test_actual_v3_joins_original_evidence(self):
        source = Path('D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3')
        result = self.verify_historical(source)
        self.assertEqual(result['result']['contrast'],0)
        self.assertFalse(result['result']['authenticated_execution'])
        self.assertEqual(result['result']['branches']['accessible']['b_meals'],0)
        with self.assertRaisesRegex(ValueError,'Terminal pin differs'):
            self.verify_historical(source,terminal_pin='0'*64)
        with self.assertRaisesRegex(ValueError,'Pending admission differs'):
            self.verify_historical(source,pins={})

    def test_receipt_tamper_and_path_binding(self):
        source = Path('D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3')
        with TemporaryDirectory() as temp:
            copy = Path(temp)/source.name
            shutil.copytree(source,copy)
            with self.assertRaisesRegex(ValueError,'Pending admission differs'):
                self.verify_historical(copy)
            receipt = copy/'03-transport.json'
            receipt.write_bytes(receipt.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'Receipt digest differs'):
                self.verify_historical(copy)

    def test_restart_requires_reviewed_contiguous_claims(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            stop=root/'STOP'
            self.assertEqual(next_unclaimed(root,contexts(),[],stop=stop)['index'],0)
            (root/'attempt-000').mkdir()
            with self.assertRaisesRegex(ValueError,'Unreconciled'):
                next_unclaimed(root,contexts(),[],stop=stop)
            self.assertEqual(next_unclaimed(root,contexts(),[0],stop=stop)['index'],1)
            stop.touch()
            self.assertIsNone(next_unclaimed(root,contexts(),[0],stop=stop))

    def test_panel_never_imputes_unclaimed_or_unreviewed_rows(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            rows = contexts()
            (root/'attempt-000').mkdir()
            result = analyze_committed_panel(root, rows, {})
            self.assertIsNone(result['summary']['all_context_mean'])
            self.assertEqual(result['summary']['counts']['missing'], 1)
            self.assertEqual(result['summary']['counts']['not_run'], 127)
            (root/'attempt-000'/'04-terminal.json').touch()
            with self.assertRaisesRegex(ValueError,'lacks independent admission'):
                analyze_committed_panel(root, rows, {})
            with self.assertRaisesRegex(ValueError,'Duplicate evidence ownership'):
                analyze_committed_panel(root, rows, {0:dict(terminal_pin='a'),1:dict(terminal_pin='a')})

    def test_rejects_uncommitted_mapping(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            rows = contexts()
            rows[0]['seed'] = rows[1]['seed']
            with self.assertRaisesRegex(ValueError, '^Frozen context mapping differs$'):
                analyze_committed_panel(root, rows, {0: {}})
