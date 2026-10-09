import ast
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import isolation_world as driver
from experiments import isolation_world_audit as audit


class IsolationWorldTests(unittest.TestCase):
    def test_recorded_observation_clock_and_read_only_world(self):
        from experiments.heartbeat_template import run
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            world=Path(folder)/'world'
            run(world,'observation-fixture','0'*40,max_ticks=1)
            before=driver.tree(world)
            observed=driver.observe(world,'0'*40)
            self.assertEqual(driver.tree(world),before)
            self.assertTrue(observed['recorded'])
            self.assertEqual(observed['report']['heartbeat_age_seconds'],0)
            self.assertEqual(observed['report']['reported_status'],'stopped')
            self.assertEqual(observed['report']['process_health'],'unverified')

    def test_non_windows_refuses_before_output(self):
        with patch.object(driver.gate.os,'name','posix'):
            with self.assertRaisesRegex(OSError,'no command started'):
                driver.run_panel('unused', '0'*40)

    def test_independent_auditor_cannot_import_launcher(self):
        tree=ast.parse(Path(audit.__file__).read_text())
        imports=[node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        self.assertFalse(any(name and ('isolation_capability' in name or 'isolation_world' in name) for name in imports))
        self.assertFalse(any(isinstance(node,ast.Import) and any('isolation' in item.name for item in node.names) for node in ast.walk(tree)))
