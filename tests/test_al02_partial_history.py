"""Inert failure evidence. No World or scientific context evaluation."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase

from experiments.al02_one_pair import observe_events


class PartialHistoryTests(TestCase):
    def test_observer_records_original_event_before_failure(self):
        world = SimpleNamespace(events=[dict(event_id=0)])
        def emit(kind):
            world.events.append(dict(event_id=1, kind=kind))
            return 1
        world.emit = emit
        records = []
        observe_events(world, 'prefix', lambda phase, event: records.append((phase, event.copy())))
        self.assertEqual(world.emit('FAULT'), 1)
        self.assertEqual(records, [('prefix', {'event_id': 0}),
                                   ('prefix', {'event_id': 1, 'kind': 'FAULT'})])

    def test_abrupt_exit_leaves_complete_bounded_record(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / 'partial.jsonl'
            code = """
import os, sys
from pathlib import Path
from types import SimpleNamespace
from experiments.al02_one_pair_worker import produce_bound_pair
def fake(*args, save_event):
    save_event('prefix', {'event_id': 0, 'kind': 'fixture'})
    os._exit(7)
pair = SimpleNamespace(CONTEXT='', CONTEXT_SHA256='', SEED=0, MAX_OUTPUT=1024, produce=fake)
loader = SimpleNamespace(sources={'experiments.executed_heredity': (None, b'')})
produce_bound_pair(pair, loader, Path(sys.argv[1]))
"""
            run = subprocess.run([sys.executable, '-B', '-S', '-c', code, str(path)],
                                 capture_output=True, timeout=10)
            self.assertEqual(run.returncode, 7, run.stderr)
            self.assertEqual(run.stdout, b'')
            self.assertEqual([json.loads(line) for line in path.read_bytes().splitlines()],
                             [{'phase': 'prefix', 'event': {'event_id': 0, 'kind': 'fixture'}}])
