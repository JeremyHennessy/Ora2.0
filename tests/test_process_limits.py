import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments import process_limits as resource

FIXTURE = Path(__file__).with_name('resource_worker.py')
PYTHON = getattr(sys, '_base_executable', sys.executable)


class ConfigTests(unittest.TestCase):
    def test_invalid_caps_and_commands_fail_before_start(self):
        for values in ({'cpu_seconds': math.inf}, {'wall_seconds': math.nan},
                       {'cpu_seconds': 0}, {'wall_seconds': -1}, {'memory_bytes': 1},
                       {'memory_bytes': True}, {'processes': 1}, {'processes': 2.5},
                       {'cpu_seconds': True}, {'cpu_seconds': 1e30}):
            with self.subTest(values=values), patch.object(resource, 'Job') as job:
                with self.assertRaises(ValueError):
                    resource.run(['unused'], resource.Limits(**values))
                job.assert_not_called()
        for command in ([], 'echo unsafe', [''], [None], ['nul\x00bad']):
            with self.subTest(command=command), patch.object(resource, 'Job') as job:
                with self.assertRaises(ValueError):
                    resource.run(command)
                job.assert_not_called()

    @unittest.skipIf(os.name == 'nt', 'Non-Windows refusal only')
    def test_no_nonwindows_fallback(self):
        with self.assertRaises(OSError):
            resource.run([sys.executable, '-c', 'raise SystemExit(99)'])


@unittest.skipUnless(os.name == 'nt', 'Windows Job Object fixtures require Windows')
class WindowsCapsTests(unittest.TestCase):
    def invoke(self, kind, **overrides):
        result = resource.run([PYTHON, str(FIXTURE), kind], resource.Limits(**overrides))
        self.assertLessEqual(result['usage']['peak_job_memory_bytes'], result['limits']['memory_bytes'])
        self.assertLessEqual(result['retained_bytes'], resource.OUTPUT_LIMIT)
        self.assertFalse(result['isolation_verified'])
        return result

    def test_finite_success(self):
        result = self.invoke('success')
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('finite-success', result['output'])
        self.assertFalse(result['timed_out'])

    def test_cpu_terminates_before_wall(self):
        result = self.invoke('cpu', cpu_seconds=0.2)
        self.assertNotEqual(result['exit_code'], 0)
        self.assertFalse(result['timed_out'])
        self.assertLess(result['elapsed_seconds'], 5)
        self.assertGreaterEqual(result['usage']['user_cpu_seconds'], 0.15)

    def test_aggregate_memory_denies_allocation(self):
        result = self.invoke('memory')
        self.assertEqual(result['exit_code'], 42)
        self.assertIn('memory-denied', result['output'])
        self.assertNotIn('allocation-succeeded', result['output'])
        self.assertFalse(result['timed_out'])

    def assert_child_gone(self, result):
        rows = [json.loads(line) for line in result['output'].splitlines()]
        pid = rows[0]['child_pid']
        self.assertTrue(resource.process_exited(pid))
        return rows

    def test_process_slots_deny_fourth_and_clean_child(self):
        result = self.invoke('process')
        self.assertEqual(result['exit_code'], 0)
        rows = self.assert_child_gone(result)
        self.assertTrue(rows[1]['fourth_denied'])
        self.assertLessEqual(result['usage']['started_processes'], 3)

    def test_timeout_kills_tree(self):
        result = self.invoke('timeout', wall_seconds=0.5)
        self.assertTrue(result['timed_out'])
        self.assertLess(result['elapsed_seconds'], 5)
        self.assertNotEqual(result['exit_code'], 0)
        self.assert_child_gone(result)

    def test_normal_exit_kills_orphan(self):
        result = self.invoke('orphan')
        self.assertEqual(result['exit_code'], 0)
        self.assertFalse(result['timed_out'])
        self.assert_child_gone(result)

    def test_output_bound_drains_without_blocking(self):
        result = self.invoke('output')
        self.assertEqual(result['exit_code'], 0)
        self.assertTrue(result['output_truncated'])
        self.assertEqual(result['retained_bytes'], resource.OUTPUT_LIMIT)
        self.assertEqual(result['output_bytes'], 2 * resource.OUTPUT_LIMIT)

    def test_assignment_refusal_prevents_target_and_cleans_bootstrap(self):
        pids = []
        def refuse(job, process):
            pids.append(process.pid)
            raise OSError('Injected assignment refusal')
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / 'must-not-exist'
            with patch.object(resource.Job, 'assign', refuse):
                with self.assertRaisesRegex(OSError, 'Injected assignment'):
                    resource.run([PYTHON, str(FIXTURE), 'marker', str(marker)])
            self.assertFalse(marker.exists())
            self.assertEqual(len(pids), 1)
            self.assertTrue(resource.process_exited(pids[0]))


if __name__ == '__main__':
    unittest.main()
