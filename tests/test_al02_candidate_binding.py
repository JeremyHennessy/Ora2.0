import json
from pathlib import Path
from unittest import TestCase, mock
from experiments import al02_one_pair_consent as gate

class CandidateBindingTests(TestCase):
    def test_immutable_candidate_is_not_authority(self):
        root = Path('D:/OraLab/drafts/ora-al02-production-installation')
        binding = json.loads((root / 'installed-binding-v1.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'Candidate scientific authorization absent'):
            gate.require_bound_worker(binding['installed_file_pins'],
                                      binding['proposed_command'], binding['proposed_relay_argv'])

    def test_altered_runtime_inputs_fail_closed(self):
        binding = json.loads((gate.RELEASE_DRAFT / 'installed-binding-v1.json').read_bytes())
        pins = binding['installed_file_pins']
        cmd = binding['proposed_command']
        relay = binding['proposed_relay_argv']
        for args in [(dict(pins, **{str(gate.WORKER): '0'*64}), cmd, relay),
                     (pins, cmd[:-1] + ['wrong'], relay),
                     (pins, cmd, relay + ['wrong']),
                     ({key: value for key, value in pins.items() if key != cmd[0]}, cmd, relay)]:
            with self.subTest(args=len(args[0])), self.assertRaises(ValueError):
                gate.require_bound_worker(*args)

    def test_artifact_digest_and_stop(self):
        binding = json.loads((gate.RELEASE_DRAFT / 'installed-binding-v1.json').read_bytes())
        args = (binding['installed_file_pins'], binding['proposed_command'],
                binding['proposed_relay_argv'])
        for name in ('CANDIDATE_BINDING', 'CANDIDATE_PACKAGE'):
            with mock.patch.object(gate, name, '0'*64):
                with self.assertRaisesRegex(ValueError, 'artifact identity differs'):
                    gate.require_bound_worker(*args)
        with mock.patch.object(gate, 'STOP', Path(__file__)):
            with self.assertRaisesRegex(ValueError, 'STOP present'):
                gate.require_bound_worker(*args)

    def test_inert_authorization_scope_and_revision(self):
        import hashlib
        from tempfile import TemporaryDirectory

        binding = json.loads((gate.RELEASE_DRAFT / 'installed-binding-v1.json').read_bytes())
        args = (binding['installed_file_pins'], binding['proposed_command'],
                binding['proposed_relay_argv'])
        record = dict(schema='AL02-CANDIDATE-ONE-ATTEMPT-v1',
                      worker_sha256=gate.CANDIDATE_WORKER, binding_sha256=gate.CANDIDATE_BINDING,
                      package_sha256=gate.CANDIDATE_PACKAGE, seed=str(gate.SEED),
                      attempt=str(gate.ATTEMPT), owner=gate.OWNER)
        with TemporaryDirectory() as temp, mock.patch.object(gate, 'BINDING', Path(temp) / 'unused'):
            path = Path(temp) / 'candidate-scientific-authorization.json'
            for raw, error in [(b'{', 'Expecting'),
                               (json.dumps(dict(record, seed='0')).encode(), 'scope differs'),
                               (json.dumps(record).encode(), 'HEAD differs')]:
                path.write_bytes(raw)
                with mock.patch.object(gate, 'CANDIDATE_AUTHORIZATION_SHA256', hashlib.sha256(raw).hexdigest()):
                    with mock.patch('subprocess.check_output', return_value='wrong'):
                        with self.assertRaisesRegex(ValueError, error):
                            gate.require_bound_worker(*args)
