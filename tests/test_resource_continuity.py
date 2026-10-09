import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import resource_continuity as driver
from experiments import resource_continuity_audit as audit

REVISION = 'a'*40


class PortableContinuityTests(unittest.TestCase):
    def test_exact_revision_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'absent'
            for revision in ('main', 'z'*40, 'a'*39):
                with self.assertRaises(ValueError):
                    driver.run_panel(output, revision)
                self.assertFalse(output.exists())

    def test_duplicate_keys_and_incomplete_panel_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)
            evidence = output/'evidence.json'
            evidence.write_text('{"schema":"a","schema":"b"}')
            with self.assertRaisesRegex(ValueError, 'Duplicate evidence key'):
                audit.audit(output, REVISION, driver.ROOT)
            evidence.write_text(json.dumps(dict(schema='resource02-panel-v1', revision=REVISION,
                                  source_sha256=audit.source_hashes(driver.ROOT), records=[])))
            with self.assertRaisesRegex(ValueError, 'Complete ordered panel'):
                audit.audit(output, REVISION, driver.ROOT)

    def test_auditor_imports_no_driver_worker_or_supervisor(self):
        import ast
        tree = ast.parse(Path(audit.__file__).read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertNotIn('experiments.resource_continuity', imports)
        self.assertNotIn('experiments.process_limits', imports)
        self.assertNotIn('experiments.heartbeat_template', imports)

    def test_nonwindows_has_no_execution_fallback(self):
        with tempfile.TemporaryDirectory() as t, patch.object(driver.os, 'name', 'posix'):
            with self.assertRaisesRegex(OSError, 'real Windows'):
                driver.run_panel(Path(t)/'absent', REVISION)


@unittest.skipUnless(os.name == 'nt', 'Real Windows caps/recovery composition requires Windows')
class WindowsContinuityTests(unittest.TestCase):
    def test_complete_pressure_controls_recovery_and_independent_rejections(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'panel'
            original = driver.run_panel(output, REVISION)
            evidence = output/'evidence.json'
            before = evidence.read_bytes()
            result = audit.audit(output, REVISION, driver.ROOT)
            self.assertEqual(result['canonical_sequences'], 12)
            self.assertEqual(result['independent_os_child_exit_checks'], 12)
            self.assertEqual(evidence.read_bytes(), before)
            for mutation, message in (('cpu-success', 'CPU pressure'), ('caps', 'Frozen caps'),
                                      ('identity', 'Source revision mismatch')):
                if mutation == 'identity':
                    manifest = output/'0-cpu/world/manifest.json'
                    saved = manifest.read_bytes()
                    changed = json.loads(saved)
                    changed['identity']['source_revision'] = 'b'*40
                    changed['identity']['run_id'] = audit.heartbeat.digest(
                        {k: v for k, v in changed['identity'].items() if k != 'run_id'})
                    manifest.write_text(json.dumps(changed))
                else:
                    changed = copy.deepcopy(original)
                    if mutation == 'cpu-success':
                        changed['records'][0]['interrupted']['exit_code'] = 0
                    else:
                        changed['records'][0]['interrupted']['limits']['cpu_seconds'] = 10
                    evidence.write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, message):
                    audit.audit(output, REVISION, driver.ROOT)
                evidence.write_bytes(before)
                if mutation == 'identity':
                    manifest.write_bytes(saved)


if __name__ == '__main__':
    unittest.main()
