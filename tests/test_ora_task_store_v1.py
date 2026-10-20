"""New durable queue checks, including actual killed SQLite owner processes."""
import json
from contextlib import closing
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.ora_task_store_v1 import Store, serve, MAX_MEMORIES, MAX_RECEIPTS


class DurableStream(unittest.TestCase):
    def test_memory_and_receipts_are_bounded_over_many_tasks_and_restarts(self):
        with tempfile.TemporaryDirectory() as folder:
            for batch in range(4):
                with Store(folder) as s:
                    for i in range(batch * 200 + 1, (batch + 1) * 200 + 1):
                        s.submit(i, 'remember', f'key-{i}', 'v' * 4096)
                        s.complete(s.claim())
                    status = s.status()
                    self.assertLessEqual(status['memories'], MAX_MEMORIES)
                    self.assertLessEqual(status['receipts'], MAX_RECEIPTS)
                    self.assertLessEqual(status['database_bytes'], status['database_limit_bytes'])
            with Store(folder) as s:
                self.assertEqual(s.submit(1, 'remember', 'key-1', 'v' * 4096), 'expired-receipt')
                s.submit(801, 'recall', 'key-800')
                self.assertEqual(s.complete(s.claim()), 'v' * 4096)
                s.submit(802, 'recall', 'key-1')
                self.assertIsNone(s.complete(s.claim()))
                s.submit(803, 'forget', 'key-800')
                s.complete(s.claim())
                s.submit(804, 'recall', 'key-800')
                self.assertIsNone(s.complete(s.claim()))

    def test_crash_rolls_back_memory_and_reclaims_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            with Store(folder) as s:
                s.submit(1, 'remember', 'name', 'Ora')
            code = '''
import os, sys
from experiments.ora_task_store_v1 import Store
s=Store(sys.argv[1]); t=s.claim()
s.db.execute('BEGIN IMMEDIATE')
s.db.execute('INSERT INTO memories VALUES(?,?,?)', ('uncommitted','bad',1))
os._exit(78)
'''
            child = subprocess.run([sys.executable, '-B', '-c', code, folder], cwd=ROOT, timeout=10)
            self.assertEqual(child.returncode, 78)
            with Store(folder) as s:
                self.assertEqual(s.status()['memories'], 0)
                self.assertEqual(s.status()['pending'], 1)
                self.assertEqual(s.complete(s.claim()), 'remembered')
                s.submit(2, 'recall', 'name')
                self.assertEqual(s.complete(s.claim()), 'Ora')
            with Store(folder) as s:
                self.assertEqual(s.status()['pending'], 0)
                self.assertEqual(s.submit(1, 'remember', 'name', 'Ora'), 'already-submitted')

    def test_second_owner_refused_and_lock_released_on_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            with Store(folder):
                result = subprocess.run([sys.executable, '-B', '-c',
                    'from experiments.ora_task_store_v1 import Store; import sys; Store(sys.argv[1])', folder],
                    cwd=ROOT, capture_output=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
            with Store(folder) as s:
                self.assertEqual(s.status()['submitted'], 0)

    def test_backpressure_input_rejection_and_idempotence(self):
        with tempfile.TemporaryDirectory() as folder, Store(folder) as s:
            for i in range(1, 129):
                s.submit(i, 'remember', str(i), 'value')
            with self.assertRaises(ValueError):
                s.submit(129, 'remember', 'overflow', 'value')
            self.assertEqual(s.status()['submitted'], 128)
            with self.assertRaises(ValueError):
                s.submit(1, 'remember', 'different', 'value')
            with self.assertRaises(ValueError):
                s.submit(129, 'shell', 'key')
            with self.assertRaises(ValueError):
                s.submit(129, 'remember', 'key', 'v' * 4097)

    def test_operator_stop_and_idle_deadline(self):
        with tempfile.TemporaryDirectory() as folder, Store(folder) as s:
            stop = Path(folder) / 'STOP'
            stop.touch()
            self.assertEqual(serve(s, stop, .1)['reason'], 'operator-stop')
            stop.unlink()
            self.assertEqual(serve(s, stop, .1), dict(reason='slice-bound', completed=0))

    def test_live_mailbox_stop_then_restart_recall(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            worker = subprocess.Popen([sys.executable, '-B', '-m', 'experiments.ora_task_store_v1',
                                       folder, '--seconds', '15'], cwd=ROOT,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            def publish(seq, kind, key, value=''):
                temporary = root / 'inbox.next'
                temporary.write_text(json.dumps([dict(sequence=seq, kind=kind, key=key, value=value)]))
                os.replace(temporary, root / 'inbox.json')
            def wait_done(seq):
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if worker.poll() is not None:
                        self.fail('Service exited before processing task')
                    try:
                        with closing(sqlite3.connect(root / 'memory.sqlite3', timeout=.1)) as db:
                            row = db.execute('SELECT state FROM tasks WHERE id=?', (seq,)).fetchone()
                            if row == ('done',):
                                return
                    except sqlite3.OperationalError:
                        pass
                    time.sleep(.02)
                self.fail('Task deadline exceeded')
            try:
                publish(1, 'remember', 'name', 'Ora')
                wait_done(1)
                publish(2, 'remember', 'colour', 'blue')
                wait_done(2)
                (root / 'STOP').touch()
                out, err = worker.communicate(timeout=5)
                self.assertEqual(worker.returncode, 0, err)
                self.assertEqual(json.loads(out)['run'], dict(reason='operator-stop', completed=2))
            finally:
                if worker.poll() is None:
                    worker.kill(); worker.communicate(timeout=5)
            (root / 'STOP').unlink()
            publish(3, 'recall', 'name')
            resumed = subprocess.run([sys.executable, '-B', '-m', 'experiments.ora_task_store_v1',
                                      folder, '--seconds', '5', '--max-tasks', '1'],
                                     cwd=ROOT, capture_output=True, text=True, timeout=10)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            with Store(folder) as s:
                self.assertEqual(s.db.execute('SELECT result FROM tasks WHERE id=3').fetchone(), ('Ora',))


if __name__ == '__main__':
    unittest.main()
