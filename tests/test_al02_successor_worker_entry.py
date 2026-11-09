"""Exercise the successor worker main and live release reader without dispatch."""
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

from experiments import al02_one_pair_consent as gate, al02_one_pair_job as job


class SuccessorWorkerEntryTests(TestCase):
    def test_real_worker_entry_refuses_disposable_scientific_scope(self):
        binding = json.loads((gate.V3_DRAFT/'installed-binding-v3.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'authorization absent'):
            gate.require_bound_worker(binding['installed_file_pins'], binding['proposed_command'],
                                      binding['proposed_relay_argv'])
        root = Path(__file__).resolve().parents[1]
        source = root/'experiments/al02_one_pair_worker.py'
        self.assertEqual(sha256(source.read_bytes()).hexdigest(), gate.V3_WORKER)
        with TemporaryDirectory() as temp:
            stage = Path(temp).resolve()
            replica = stage/'checkout'
            pins = {}
            for target, expected in binding['installed_file_pins'].items():
                path = Path(target)
                if path.is_relative_to(gate.WORKTREE):
                    relative = path.relative_to(gate.WORKTREE)
                    path = replica/relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((root/relative).read_bytes())
                self.assertEqual(sha256(path.read_bytes()).hexdigest(), expected)
                pins[str(path)] = expected
            source = replica/'experiments/al02_one_pair_worker.py'
            shim = source.with_name('guard.py')
            shim.write_text(
                'import importlib.util, sys\n'
                'from hashlib import sha256\n'
                'from pathlib import Path\n'
                f'path = Path({str(source)!r})\n'
                f'assert sha256(path.read_bytes()).hexdigest() == {gate.V3_WORKER!r}\n'
                'spec = importlib.util.spec_from_file_location("guarded_worker", path)\n'
                'worker = importlib.util.module_from_spec(spec)\n'
                'spec.loader.exec_module(worker)\n'
                'def blocked(*args, **kwargs):\n'
                '    raise AssertionError("NO WORLD: scientific dispatch blocked")\n'
                'worker.produce_bound_pair = blocked\n'
                'worker.__file__ = __file__\n'
                'try:\n'
                '    worker.main()\n'
                'except PermissionError as error:\n'
                '    if str(error) != "Scientific release outside fixed scope or STOP present":\n'
                '        raise\n'
                '    print("LIVE FRAME VALID; DISPOSABLE SCIENTIFIC SCOPE REFUSED")\n'
                'else:\n'
                '    raise AssertionError("Expected fixed scope refusal")\n', encoding='ascii')
            pins[str(shim)] = sha256(shim.read_bytes()).hexdigest()
            pending = stage/'00-pending.json'
            python = getattr(sys,'_base_executable',sys.executable)
            cmd = [python,'-I','-S','-B',str(shim),str(pending),gate.SUCCESSOR]
            environment = dict(os.environ)
            raw = json.dumps(dict(command=cmd, cwd=str(replica), pins=pins,
                consent=gate.SUCCESSOR, evidence_tier=gate.TIER, context=gate.CONTEXT,
                owner=gate.OWNER, environment_sha256=sha256(
                    json.dumps(environment,sort_keys=True).encode()).hexdigest())).encode()
            pending.write_bytes(raw)

            def admit(executable, argv, process, usage):
                self.assertEqual(executable,python)
                self.assertEqual(argv,tuple(job.relay_argv(python,cmd)))
                self.assertEqual(usage['started_processes'],1)
                verified = json.dumps(dict(pending_sha256=sha256(raw).hexdigest(),
                                           bootstrap_pid=process.pid)).encode()
                (stage/'01-verified.json').write_bytes(verified)
                intent = json.dumps(dict(verified_sha256=sha256(verified).hexdigest())).encode()
                (stage/'02-release-intent.json').write_bytes(intent)
                return sha256(intent).hexdigest()

            output, receipt = job.run(cmd,replica,before_go=admit,environment=environment,relay=True)
            self.assertTrue(receipt['accepted'],(output,receipt))
            self.assertIn(b'LIVE FRAME VALID; DISPOSABLE SCIENTIFIC SCOPE REFUSED',output)
            self.assertEqual(receipt['final']['started_processes'],2)
            self.assertFalse((stage/'partial.jsonl').exists())
            self.assertFalse(gate.SUCCESSOR_ATTEMPT.exists())
            print(json.dumps(dict(worker_sha256=gate.V3_WORKER, receipt=receipt,
                                  scientific_dispatch=False)),flush=True)
