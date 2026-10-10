import copy
from pathlib import Path
import shutil
import tempfile
import unittest
from experiments import heartbeat_world as world
from experiments import lost_work, lost_work_audit

REVISION = 'a'*40


class LostWorkTests(unittest.TestCase):
    def test_observed_acknowledgement_and_stale_restore_are_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            world.run(root/'original', 'loss-fixture', REVISION, pause_after=7)
            shutil.copytree(root/'original', root/'backup')
            world.run(root/'original', 'loss-fixture', REVISION, resume=True, pause_after=13)
            receipt = lost_work.measure(root/'original', root/'backup', REVISION, 13)
            self.assertEqual(receipt['missing_acknowledged_transitions'], 6)
            self.assertEqual(lost_work_audit.audit(root/'original', root/'backup', receipt,
                                                 REVISION)['missing_ticks'], list(range(8, 14)))
            current = lost_work.measure(root/'original', root/'original', REVISION, 13)
            self.assertEqual(current['missing_acknowledged_transitions'], 0)
            lost_work_audit.audit(root/'original', root/'original', current, REVISION)
            with self.assertRaises(ValueError):
                lost_work.measure(root/'original', root/'backup', REVISION, 32)
            forged = copy.deepcopy(receipt)
            forged['missing_acknowledged_transitions'] = 0
            with self.assertRaises(ValueError):
                lost_work_audit.audit(root/'original', root/'backup', forged, REVISION)

    def test_equal_tick_different_world_is_not_a_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('one', 'other'):
                world.run(root/name, name, REVISION, pause_after=7)
            with self.assertRaises(ValueError):
                lost_work.measure(root/'one', root/'other', REVISION, 7)
            with self.assertRaises(ValueError):
                lost_work_audit.audit(root/'one', root/'other', {}, REVISION)
