from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

from experiments.al02_one_pair_job import relay_argv, run


class LiveReleaseTests(TestCase):
    def test_assigned_relay_delivers_bound_frame(self):
        root = Path(__file__).resolve().parents[1]
        module = root / 'experiments/al02_one_pair_worker.py'
        with TemporaryDirectory() as temp:
            fake = Path(temp) / 'fake.py'
            fake.write_text(
                'import importlib.util, io, json, os, sys, time\n'
                f's=importlib.util.spec_from_file_location("release", {str(module)!r})\n'
                'm=importlib.util.module_from_spec(s); s.loader.exec_module(m)\n'
                'if len(sys.argv) > 1:\n'
                '    stream = sys.stdin\n'
                '    frame = stream.buffer.read()\n'
                '    if sys.argv[1] == "duplicate": frame += frame\n'
                '    elif sys.argv[1] == "expired":\n'
                '        parsed = json.loads(frame); parsed["expires"] = time.monotonic() - 1\n'
                '        frame = json.dumps(parsed).encode("ascii")\n'
                '    elif sys.argv[1] == "missing": frame = b""\n'
                '    class FixtureInput:\n'
                '        buffer = io.BytesIO(frame)\n'
                '        fileno = stream.fileno\n'
                '    sys.stdin = FixtureInput()\n'
                'm.read_release("a"*64, os.getppid())\n'
                'print("INERT RELEASE ACCEPTED")\n', encoding='ascii')
            command = [sys.executable, '-I', '-S', '-B', str(fake)]
            def admit(python, argv, _process, usage):
                self.assertEqual(argv[:6], tuple(relay_argv(python, command)[:6]))
                self.assertEqual(usage['started_processes'], 1)
                self.assertEqual(usage['active_before_close'], 1)
                return 'a' * 64
            raw, receipt = run(command, root, before_go=admit, relay=True)
            self.assertTrue(receipt['accepted'], (raw, receipt))
            self.assertEqual(receipt['final']['started_processes'], 2)
            self.assertEqual(raw.strip(), b'INERT RELEASE ACCEPTED')
            raw, receipt = run(command, root, before_go=lambda *args: 'b'*64, relay=True)
            self.assertFalse(receipt['accepted'])
            self.assertIn(b'Incorrect, duplicate or expired release frame', raw)
            for mode, error in [('duplicate', b'Incorrect, duplicate or expired'),
                                ('expired', b'Incorrect, duplicate or expired'),
                                ('missing', b'Missing or oversized')]:
                with self.subTest(mode=mode):
                    raw, receipt = run(command + [mode], root, before_go=admit, relay=True)
                    self.assertFalse(receipt['accepted'])
                    self.assertIn(error, raw)
            with self.assertRaisesRegex(ValueError, 'Invalid pre-go'):
                run(command, root, before_go=lambda *args: None, relay=True)
