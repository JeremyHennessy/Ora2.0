from pathlib import Path
import json
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from experiments import al02_one_pair_consent as gate


class FinalV2Tests(TestCase):
    def test_exact_artifacts_require_separate_authority(self):
        binding = json.loads((gate.V2_DRAFT/'installed-binding-v2.json').read_bytes())
        args = (binding['installed_file_pins'], binding['proposed_command'],
                binding['proposed_relay_argv'])
        with self.assertRaisesRegex(ValueError, 'authorization absent'):
            gate.require_bound_worker(*args)
        with patch.object(gate, 'V2_BINDING', '0'*64):
            with self.assertRaisesRegex(ValueError, 'artifact identity differs'):
                gate.require_bound_worker(*args)
        with TemporaryDirectory() as temp, patch.object(gate, 'V2_DRAFT', Path(temp)):
            with self.assertRaises(FileNotFoundError):
                gate.require_bound_worker(*args)

    def test_exact_artifacts_with_temporary_authority_gate_only(self):
        import hashlib
        binding = json.loads((gate.V2_DRAFT/'installed-binding-v2.json').read_bytes())
        record = dict(schema='AL02-CANDIDATE-ONE-ATTEMPT-v2', worker_sha256=gate.CANDIDATE_WORKER,
                      binding_sha256=gate.V2_BINDING, package_sha256=gate.V2_PACKAGE,
                      seed=str(gate.SEED), attempt=str(gate.ATTEMPT), owner=gate.OWNER)
        raw = json.dumps(record).encode()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'candidate-scientific-authorization-v2.json').write_bytes(raw)
            with patch.object(gate, 'BINDING', root/'unused'), patch.object(
                    gate, 'V2_AUTHORIZATION_SHA256', hashlib.sha256(raw).hexdigest()):
                verified = gate.require_bound_worker(binding['installed_file_pins'],
                    binding['proposed_command'], binding['proposed_relay_argv'])
                self.assertEqual(verified['binding_sha256'],gate.V2_BINDING)
        self.assertFalse(gate.ATTEMPT.exists())


    def test_tampered_frozen_artifacts_refused_without_repinning(self):
        import shutil
        original = gate.V2_DRAFT
        binding = json.loads((original/'installed-binding-v2.json').read_bytes())
        args = (binding['installed_file_pins'], binding['proposed_command'],
                binding['proposed_relay_argv'])
        names = ('installed-binding-v2.json', 'human-release-package-v2.json',
                 'source-pins-v2.json')
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for name in names:
                shutil.copyfile(original/name, root/name)
            with patch.object(gate, 'V2_DRAFT', root):
                for name in names:
                    with self.subTest(name=name):
                        path = root/name
                        pristine = path.read_bytes()
                        path.write_bytes(pristine + b' ')
                        try:
                            with self.assertRaisesRegex(ValueError, 'artifact identity differs: ' + name):
                                gate.require_bound_worker(*args)
                        finally:
                            path.write_bytes(pristine)
