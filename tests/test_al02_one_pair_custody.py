"""Real inert Windows workers only. No scientific module is invoked."""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

from experiments import al02_one_pair_custody as custody
from experiments import al02_one_pair_job as job


class CustodyTests(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.out = self.root / 'one-use'
        self.worker = self.root / 'worker.py'
        self.worker.write_text('print("inert")\n', encoding='ascii')
        python = getattr(sys, '_base_executable', sys.executable)
        self.command = [python, '-I', '-S', '-B', str(self.worker)]
        self.pins = {str(p): custody.digest(p) for p in
                     (python, self.worker, custody.__file__, job.__file__,
                      Path(job.__file__).with_name('process_limits.py'))}
        self.seen = []

    def run_once(self, check=lambda: True):
        def referee(data):
            self.assertTrue((self.out / '03-transport.json').is_file())
            self.seen.append(data)
            return {'fixture': True}
        return custody.transaction(self.out, command=self.command, cwd=self.root,
                                   pins=self.pins, expected_account=custody.account(),
                                   context='INERT', referee=referee, admission_check=check)

    def test_order_success_and_duplicate(self):
        def check():
            self.assertTrue((self.out / '00-pending.json').is_file())
            self.assertFalse((self.out / '02-release-intent.json').exists())
            return True
        self.assertEqual(self.run_once(check), {'fixture': True})
        self.assertEqual(self.seen, [b'inert\r\n'])
        self.assertTrue((self.out / '04-terminal.json').is_file())
        with self.assertRaises(FileExistsError):
            self.run_once()

    def test_source_and_argument_substitution(self):
        self.command[1] = '-E'
        with self.assertRaisesRegex(ValueError, 'startup arguments'):
            self.run_once()
        self.command[1] = '-I'
        self.worker.write_text('raise RuntimeError("altered")\n')
        with self.assertRaisesRegex(ValueError, 'Identity mismatch'):
            self.run_once()
        self.assertFalse(self.out.exists())

    def test_pre_go_source_swap_is_rejected(self):
        def swap():
            self.worker.write_text('print("substituted")')
            return True
        with self.assertRaisesRegex(ValueError, 'Identity mismatch'):
            self.run_once(swap)
        self.assertFalse((self.out / '02-release-intent.json').exists())
        self.assertEqual((self.out / 'raw.bin').read_bytes(), b'')

    def test_false_admission_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'did not affirm'):
            self.run_once(lambda: False)
        self.assertFalse((self.out / '02-release-intent.json').exists())

    def test_denied_pre_go(self):
        def reject():
            raise ValueError('Denied by fixture admission')
        with self.assertRaisesRegex(ValueError, 'Denied'):
            self.run_once(reject)
        self.assertFalse((self.out / '02-release-intent.json').exists())
        self.assertTrue((self.out / '99-failed.json').is_file())
        self.assertEqual((self.out / 'raw.bin').read_bytes(), b'')
        self.assertEqual(self.seen, [])

    def test_post_go_failure_and_overflow(self):
        for name, code, expected_size in [
            ('failure', 'print("partial", flush=True)\nraise SystemExit(7)', 9),
            ('overflow', 'import sys,time\nsys.stdout.buffer.write(b"x"*1200000)\n'
                         'sys.stdout.flush()\ntime.sleep(30)', job.OUTPUT_LIMIT),
        ]:
            with self.subTest(name=name):
                self.out = self.root / name
                self.worker.write_text(code, encoding='ascii')
                self.pins[str(self.worker)] = custody.digest(self.worker)
                with self.assertRaisesRegex(ValueError, 'Transport rejected'):
                    self.run_once()
                self.assertTrue((self.out / '02-release-intent.json').is_file())
                self.assertTrue((self.out / '99-failed.json').is_file())
                self.assertEqual((self.out / 'raw.bin').stat().st_size, expected_size)
        self.assertEqual(self.seen, [])
