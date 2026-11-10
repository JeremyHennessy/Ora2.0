"""Frozen continuation policy tests with an isolated inert Windows handoff."""
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch, sentinel

from experiments import al02_campaign_admission as gate
from experiments import al02_one_pair as pair
from tools import run_al02_campaign as campaign
from tools.al02_campaign_evidence import next_unclaimed, verify_attempt
from tools.run_al02_campaign import run_next


class ContinuationPolicyTests(unittest.TestCase):
    def test_exact_artifacts_and_inactive_entry(self):
        binding = gate.continuation_binding()
        self.assertEqual(binding['budget']['pairs'],120)
        self.assertEqual(gate.continuation_spec()['batches'],
                         [list(range(i,i+8)) for i in range(8,128,8)])
        with self.assertRaisesRegex(ValueError,'scientific authorization absent'):
            run_next(continuation=True)

    @contextmanager
    def _continuation_fixture(self, *, with_attempts=True, with_admissions=False,
                              with_accepted_evidence=True, next_index=16):
        ordered = gate.inventory()
        binding = gate.continuation_binding()
        authority = 'test-authorization'
        # Supply accepted evidence at the verification boundary without running science.
        report = {'rows': [
            {'index': i,
             'status': 'accepted' if with_accepted_evidence and 8 <= i < next_index else 'not_run',
             'job_accounting': {'cpu_ticks': 0, 'wall_seconds': 0}}
            for i in range(128)
        ]}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            checkout = root / 'checkout'
            source = checkout / 'experiments/al02_campaign_admission.py'
            status = root / 'automation/ora-codex/status.json'
            status.parent.mkdir(parents=True)
            status.write_text('{"status": "parked"}', encoding='utf-8')
            if with_attempts:
                for row in ordered[8:next_index]:
                    (root / row['attempt']).mkdir()

            pins = dict(binding['pins'], **{str(source): campaign.ADMISSION_SHA256})
            admissions = {}
            if with_admissions:
                for row in ordered[8:next_index]:
                    admissions[row['index']] = {
                        'command': [binding['python'], '-I', '-S', '-B', binding['worker'],
                                    str(root / row['attempt'] / '00-pending.json'), gate.TOKEN],
                        'pins': pins,
                        'identities': {
                            'binding_sha256': gate.CONTINUATION_BINDING_SHA256,
                            'package_sha256': gate.CONTINUATION_PACKAGE_SHA256,
                            'contexts_sha256': gate.CONTEXTS_SHA256,
                            'authorization_sha256': authority,
                        },
                        'terminal_pin': f"{row['index']:064x}",
                    }

            custody = Mock(FREE_MIN=0)
            custody.pinned_path.side_effect = [root, checkout]
            custody.digest.return_value = campaign.ADMISSION_SHA256
            custody.transaction.side_effect = AssertionError('Custody dispatch attempted')
            with (
                patch.multiple(gate, ROOT=root, STOP=root / 'STOP', CHECKOUT=checkout,
                               CONTINUATION_DESTINATION=root, __file__=str(source),
                               CONTINUATION_AUTHORIZATION_SHA256=authority),
                patch.object(gate, 'continuation_binding', return_value=binding),
                patch.object(gate, 'admitted') as admitted,
                patch.object(campaign, 'custody', custody),
                patch.object(campaign.subprocess, 'check_output',
                             return_value=binding['production_head']),
                patch.object(campaign, 'pilot_admissions', return_value=admissions),
                patch.object(campaign, 'analyze_committed_panel', return_value=report),
                patch.object(campaign.shutil, 'disk_usage', return_value=Mock(free=2**31)),
            ):
                yield root, ordered, admissions, admitted, custody

    def test_run_next_stops_before_claiming_or_dispatching(self):
        with (
            self._continuation_fixture(with_attempts=False) as (root, ordered, _, _, custody),
            patch.object(campaign, 'next_unclaimed', wraps=next_unclaimed) as select,
        ):
            (root / 'STOP').touch()

            self.assertIsNone(run_next(continuation=True))

            select.assert_not_called()
            custody.transaction.assert_not_called()
            for row in ordered[8:]:
                self.assertFalse((root / row['attempt']).exists(), row['attempt'])

    def test_run_next_refuses_insufficient_archive_space_before_claim_or_custody(self):
        with self._continuation_fixture(with_attempts=False, with_accepted_evidence=False) as (
            root, ordered, _, admitted, custody
        ):
            budget = gate.continuation_binding()['budget']
            custody.FREE_MIN = 1024
            required = budget['pairs'] * budget['archive_bytes_per_pair'] + custody.FREE_MIN
            with patch.object(campaign.shutil, 'disk_usage',
                              return_value=Mock(free=required - 1)) as disk_usage:
                with self.assertRaises(ValueError) as error:
                    run_next(continuation=True)

            self.assertEqual(str(error.exception), 'Campaign archive or disk reservation exhausted')
            disk_usage.assert_called_once_with(root)
            admitted.assert_not_called()
            custody.transaction.assert_not_called()
            for row in ordered[8:]:
                self.assertFalse((root / row['attempt']).exists(), row['attempt'])

    def test_run_next_hands_off_index_8_without_continuation_claims(self):
        binding = gate.continuation_binding()
        with self._continuation_fixture(with_attempts=False, with_accepted_evidence=False) as (
            root, ordered, _, _, custody
        ):
            checkout = root / 'checkout'
            source = checkout / 'experiments/al02_campaign_admission.py'
            pins = dict(binding['pins'], **{str(source): campaign.ADMISSION_SHA256})
            row = ordered[8]
            directory = root / row['attempt']
            command = [binding['python'], '-I', '-S', '-B', binding['worker'],
                       str(directory / '00-pending.json'), gate.TOKEN]
            custody.transaction.side_effect = None
            custody.transaction.return_value = sentinel.custody_result

            self.assertIs(run_next(continuation=True), sentinel.custody_result)

            custody.transaction.assert_called_once_with(
                directory, command=command, cwd=checkout, pins=pins,
                expected_account=gate.OWNER, context=row['context_sha256'],
                referee=None, consent=gate.TOKEN,
            )
            for row in ordered[8:]:
                self.assertFalse((root / row['attempt']).exists(), row['attempt'])

    @unittest.skipUnless(sys.platform == 'win32', 'Requires a real Windows Job')
    def test_inert_continuation_index_8(self):
        binding = gate.continuation_binding()
        row = gate.inventory()[8]
        self.assertEqual(row['index'], 8)
        self.assertNotEqual(row['seed'], pair.SEED)
        self.assertNotEqual(row['context_sha256'], pair.CONTEXT_SHA256)
        custody = campaign.custody
        job = custody.transport
        real_transaction, real_run, real_admit = custody.transaction, job.run, gate.admitted
        real_transaction = Mock(wraps=real_transaction)
        production = (gate.CHECKOUT, gate.CONTINUATION_DESTINATION)
        source = Path(gate.__file__).resolve()
        worker = source.with_name('al02_one_pair_worker.py')
        template = (Path(__file__).parent / 'al02_release_rehearsal/inert-worker.py').read_bytes()
        self.assertEqual(sha256(template.replace(b'\r\n', b'\n')).hexdigest(),
                         'ff7edeeba200f9366aaf04e9034c72a34173326c03f49a6b249fb984f245cd93')
        shim_bytes = template.replace(b'ORA-PHASE6-INERT', gate.TOKEN.encode('ascii'))
        python = getattr(sys, '_base_executable', sys.executable)
        self.assertEqual(python, binding['python'])
        owner = gate.OWNER

        with TemporaryDirectory(prefix='ora-inert-continuation-') as temp:
            root = Path(temp).resolve()
            checkout = root / 'checkout'
            local_source = checkout / 'experiments' / source.name
            local_source.parent.mkdir(parents=True)
            local_worker = local_source.with_name(worker.name)
            shutil.copyfile(source, local_source)
            shutil.copyfile(worker, local_worker)
            status = root / 'automation/ora-codex/status.json'
            status.parent.mkdir(parents=True)
            status.write_text('{"status":"parked"}', encoding='ascii')
            shim = root / 'inert.py'
            shim.write_bytes(shim_bytes)
            lawful = root / 'lawful.bin'
            # Same retained payload used by the controller rehearsal.
            shutil.copyfile(
                'D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3/raw.bin',
                lawful,
            )
            frozen_identity = dict(binding_sha256=gate.CONTINUATION_BINDING_SHA256,
                                   package_sha256=gate.CONTINUATION_PACKAGE_SHA256,
                                   contexts_sha256=gate.CONTEXTS_SHA256)
            authority = root / 'continuation-authority.json'
            authority.write_text(json.dumps(dict(
                schema='al02-continuation-one-claim-per-index-v1', owner=owner,
                **frozen_identity)), encoding='ascii')
            authority_pin = custody.digest(authority)
            committed_identity = dict(frozen_identity, authorization_sha256=authority_pin,
                                      context_index=8, seed=row['seed'])
            fixture_identity = dict(
                committed_identity, inert_execution=True, committed_seed=row['seed'],
                committed_context_sha256=row['context_sha256'], seed=pair.SEED,
                fixture_context_sha256=pair.CONTEXT_SHA256,
            )
            referee_source = str(Path(pair.__file__).resolve())
            pins = {str(path): custody.digest(path) for path in (
                Path(custody.__file__).resolve(), Path(job.__file__).resolve(),
                worker.with_name('process_limits.py'), referee_source,
            )}
            local_referee = local_source.with_name('al02_one_pair.py')
            shutil.copyfile(referee_source, local_referee)
            pins.update({
                str(local_referee): pins[referee_source],
                python: binding['pins'][python],
                str(shim): sha256(shim_bytes).hexdigest(),
                str(local_worker): binding['pins'][binding['worker']],
                str(lawful): 'e136d0e1a10895b2e500766026957ed987f0a9cd4365776f589797eac9a416d7',
                str(local_source): campaign.ADMISSION_SHA256,
            })
            directory = root / row['attempt']
            pending = directory / '00-pending.json'
            command = (python, '-I', '-S', '-B', str(shim), str(pending), gate.TOKEN)
            proposed = (*command[:4], binding['worker'], *command[5:])

            def require_inert(target, cwd, argv):
                if (tuple(argv) != command or Path(cwd) != checkout or target != directory
                        or command[4] == binding['worker']
                        or any(not path.resolve().is_relative_to(root)
                               or any(path.resolve().is_relative_to(base) for base in production)
                               for path in (Path(cwd), target, Path(argv[4]), Path(argv[5])))
                        or any(custody.digest(path) != pins[path] for path in (python, str(shim)))):
                    raise AssertionError('Inert continuation launch barrier refused')

            def admit(target, cwd, argv, account, context, limits, actual_pins):
                if context == pair.CONTEXT_SHA256:
                    require_inert(target, cwd, argv)
                    self.assertEqual(actual_pins, pins)
                    self.assertEqual(account, owner)
                    self.assertEqual(limits, gate.LIMITS)
                    return dict(fixture_identity)
                identity = real_admit(target, cwd, argv, account, context, limits, actual_pins)
                self.assertEqual(identity, committed_identity)
                return identity

            def guarded_transaction(target, **kwargs):
                self.assertEqual(kwargs, dict(command=list(proposed), cwd=checkout, pins=pins,
                                             expected_account=owner, context=row['context_sha256'],
                                             referee=None, consent=gate.TOKEN))
                physical = dict(kwargs, command=command, context=pair.CONTEXT_SHA256)
                require_inert(target, physical['cwd'], physical['command'])
                self.assertFalse(target.exists())
                return real_transaction(target, **physical)

            def guarded_job(argv, cwd, **kwargs):
                require_inert(directory, cwd, argv)
                self.assertIs(kwargs['relay'], True)
                return real_run(argv, cwd, **kwargs)

            with (
                patch.multiple(gate, ROOT=root, STOP=root / 'STOP', CHECKOUT=checkout,
                               CONTINUATION_DESTINATION=root, __file__=str(local_source),
                               CONTINUATION_AUTHORIZATION_SHA256=authority_pin),
                patch.object(gate, 'continuation_binding', return_value=dict(binding, pins=pins)),
                patch.object(gate, 'admitted', side_effect=admit) as admission,
                patch.object(campaign.subprocess, 'check_output',
                             return_value=binding['production_head']),
                patch.object(custody, 'transaction', side_effect=guarded_transaction) as handoff,
                patch.object(job, 'run', side_effect=guarded_job) as launch,
            ):
                original_command = command
                try:
                    command = (*command[:4], binding['worker'], *command[5:])
                    with self.subTest(inert_continuation='substituted command'):
                        with self.assertRaisesRegex(
                                AssertionError, '^Inert continuation launch barrier refused$'):
                            run_next(continuation=True)
                        handoff.assert_called_once()
                        real_transaction.assert_not_called()
                        launch.assert_not_called()
                        self.assertEqual(list(root.glob('attempt-*')), [])
                finally:
                    command = original_command

                handoff.reset_mock()
                admission.reset_mock()
                try:
                    shim.write_bytes(shim_bytes + b'\n# changed inert fixture bytes\n')
                    with self.subTest(inert_continuation='changed shim bytes'):
                        with self.assertRaisesRegex(
                                AssertionError, '^Inert continuation launch barrier refused$'):
                            run_next(continuation=True)
                        handoff.assert_called_once()
                        real_transaction.assert_not_called()
                        launch.assert_not_called()
                        self.assertEqual(list(root.glob('attempt-*')), [])
                        self.assertEqual(pins[str(shim)], sha256(shim_bytes).hexdigest())
                finally:
                    shim.write_bytes(shim_bytes)

                handoff.reset_mock()
                admission.reset_mock()
                result = run_next(continuation=True)
                real_transaction.assert_called_once()

                handoff.assert_called_once()
                launch.assert_called_once()
                self.assertEqual(admission.call_args_list[0].args[4], row['context_sha256'])
                self.assertEqual(list(root.glob('attempt-*')), [directory])
                terminal = directory / '04-terminal.json'
                identities = dict(fixture_identity, referee_entry='experiments.al02_one_pair.verify_context',
                                  referee_sha256=pins[referee_source])
                terminal_bytes = terminal.read_bytes()
                record = json.loads(terminal_bytes)
                self.assertEqual(record['release_identities'], identities)
                self.assertEqual(record['result'], result)
                terminal_pin = custody.digest(terminal)
                # Local readback pin for the synthetic fixture, with no independent review.
                verified = verify_attempt(
                    directory, dict(index=row['index'], attempt=row['attempt'], context=pair.CONTEXT,
                                    context_sha256=pair.CONTEXT_SHA256, seed=pair.SEED),
                    command=list(command), pins=pins, identities=identities,
                    terminal_pin=terminal_pin,
                )
                self.assertEqual((verified['index'], verified['status']), (8, 'accepted'))
                self.assertEqual(verified['raw_sha256'], pins[str(lawful)])
                self.assertEqual(verified['result']['contrast'], 0)
                self.assertIs(verified['result']['authenticated_execution'], False)
                partial = directory / 'partial.jsonl'
                partial_bytes = partial.read_bytes()
                with self.assertRaisesRegex(ValueError, '^Release identity differs$'):
                    run_next(continuation=True)

                handoff.assert_called_once()
                launch.assert_called_once()
                self.assertEqual(list(root.glob('attempt-*')), [directory])
                self.assertEqual(terminal.read_bytes(), terminal_bytes)
                self.assertEqual(partial.read_bytes(), partial_bytes)

                raw = directory / 'raw.bin'
                raw_bytes = raw.read_bytes()
                offset = next(i for i, byte in enumerate(partial_bytes)
                              if byte not in (10, 13))
                replacement = b'!' if partial_bytes[offset] != ord('!') else b'?'
                tampered = partial_bytes[:offset] + replacement + partial_bytes[offset + 1:]
                self.assertEqual(len(tampered), len(partial_bytes))
                self.assertNotEqual(tampered, partial_bytes)
                try:
                    partial.write_bytes(tampered)
                    with self.assertRaisesRegex(ValueError, '^Journal differs$'):
                        verify_attempt(
                            directory, dict(index=row['index'], attempt=row['attempt'],
                                            context=pair.CONTEXT,
                                            context_sha256=pair.CONTEXT_SHA256, seed=pair.SEED),
                            command=list(command), pins=pins, identities=identities,
                            terminal_pin=terminal_pin,
                        )
                    self.assertEqual(terminal.read_bytes(), terminal_bytes)
                    self.assertEqual(raw.read_bytes(), raw_bytes)
                    handoff.assert_called_once()
                    launch.assert_called_once()
                finally:
                    partial.write_bytes(partial_bytes)
                    restored = verify_attempt(
                        directory, dict(index=row['index'], attempt=row['attempt'],
                                        context=pair.CONTEXT,
                                        context_sha256=pair.CONTEXT_SHA256, seed=pair.SEED),
                        command=list(command), pins=pins, identities=identities,
                        terminal_pin=terminal_pin,
                    )
                    self.assertEqual(restored, verified)
                    self.assertEqual(partial.read_bytes(), partial_bytes)
                    self.assertEqual(terminal.read_bytes(), terminal_bytes)
                    self.assertEqual(raw.read_bytes(), raw_bytes)
                    handoff.assert_called_once()
                    launch.assert_called_once()

    @unittest.skipUnless(sys.platform == 'win32', 'Requires a real Windows Job')
    def test_inert_continuation_reviewed_multi_index(self):
        binding = gate.continuation_binding()
        row = gate.inventory()[8]
        self.assertEqual(row['index'], 8)
        self.assertNotEqual(row['seed'], pair.SEED)
        self.assertNotEqual(row['context_sha256'], pair.CONTEXT_SHA256)
        custody = campaign.custody
        job = custody.transport
        real_transaction, real_run, real_admit = custody.transaction, job.run, gate.admitted
        real_transaction = Mock(wraps=real_transaction)
        production = (gate.CHECKOUT, gate.CONTINUATION_DESTINATION)
        source = Path(gate.__file__).resolve()
        worker = source.with_name('al02_one_pair_worker.py')
        template = (Path(__file__).parent / 'al02_release_rehearsal/inert-worker.py').read_bytes()
        self.assertEqual(sha256(template.replace(b'\r\n', b'\n')).hexdigest(),
                         'ff7edeeba200f9366aaf04e9034c72a34173326c03f49a6b249fb984f245cd93')
        shim_bytes = template.replace(b'ORA-PHASE6-INERT', gate.TOKEN.encode('ascii'))
        python = getattr(sys, '_base_executable', sys.executable)
        self.assertEqual(python, binding['python'])
        owner = gate.OWNER

        with TemporaryDirectory(prefix='ora-inert-continuation-') as temp:
            root = Path(temp).resolve()
            checkout = root / 'checkout'
            local_source = checkout / 'experiments' / source.name
            local_source.parent.mkdir(parents=True)
            local_worker = local_source.with_name(worker.name)
            shutil.copyfile(source, local_source)
            shutil.copyfile(worker, local_worker)
            status = root / 'automation/ora-codex/status.json'
            status.parent.mkdir(parents=True)
            status.write_text('{"status":"parked"}', encoding='ascii')
            shim = root / 'inert.py'
            shim.write_bytes(shim_bytes)
            lawful = root / 'lawful.bin'
            # Same retained payload used by the controller rehearsal.
            shutil.copyfile(
                'D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3/raw.bin',
                lawful,
            )
            frozen_identity = dict(binding_sha256=gate.CONTINUATION_BINDING_SHA256,
                                   package_sha256=gate.CONTINUATION_PACKAGE_SHA256,
                                   contexts_sha256=gate.CONTEXTS_SHA256)
            authority = root / 'continuation-authority.json'
            authority.write_text(json.dumps(dict(
                schema='al02-continuation-one-claim-per-index-v1', owner=owner,
                **frozen_identity)), encoding='ascii')
            authority_pin = custody.digest(authority)
            committed_identity = dict(frozen_identity, authorization_sha256=authority_pin,
                                      context_index=8, seed=row['seed'])
            fixture_identity = dict(
                committed_identity, inert_execution=True, committed_seed=row['seed'],
                committed_context_sha256=row['context_sha256'], seed=pair.SEED,
                fixture_context_sha256=pair.CONTEXT_SHA256,
            )
            referee_source = str(Path(pair.__file__).resolve())
            pins = {str(path): custody.digest(path) for path in (
                Path(custody.__file__).resolve(), Path(job.__file__).resolve(),
                worker.with_name('process_limits.py'), referee_source,
            )}
            local_referee = local_source.with_name('al02_one_pair.py')
            shutil.copyfile(referee_source, local_referee)
            pins.update({
                str(local_referee): pins[referee_source],
                python: binding['pins'][python],
                str(shim): sha256(shim_bytes).hexdigest(),
                str(local_worker): binding['pins'][binding['worker']],
                str(lawful): 'e136d0e1a10895b2e500766026957ed987f0a9cd4365776f589797eac9a416d7',
                str(local_source): campaign.ADMISSION_SHA256,
            })
            directory = root / row['attempt']
            pending = directory / '00-pending.json'
            command = (python, '-I', '-S', '-B', str(shim), str(pending), gate.TOKEN)
            proposed = (*command[:4], binding['worker'], *command[5:])

            def require_inert(target, cwd, argv):
                if (tuple(argv) != command or Path(cwd) != checkout or target != directory
                        or command[4] == binding['worker']
                        or any(not path.resolve().is_relative_to(root)
                               or any(path.resolve().is_relative_to(base) for base in production)
                               for path in (Path(cwd), target, Path(argv[4]), Path(argv[5])))
                        or any(custody.digest(path) != pins[path] for path in (python, str(shim)))):
                    raise AssertionError('Inert continuation launch barrier refused')

            def admit(target, cwd, argv, account, context, limits, actual_pins):
                if context == pair.CONTEXT_SHA256:
                    require_inert(target, cwd, argv)
                    self.assertEqual(actual_pins, pins)
                    self.assertEqual(account, owner)
                    self.assertEqual(limits, gate.LIMITS)
                    return dict(fixture_identity)
                identity = real_admit(target, cwd, argv, account, context, limits, actual_pins)
                self.assertEqual(identity, committed_identity)
                return identity

            def guarded_transaction(target, **kwargs):
                self.assertEqual(kwargs, dict(command=list(proposed), cwd=checkout, pins=pins,
                                             expected_account=owner, context=row['context_sha256'],
                                             referee=None, consent=gate.TOKEN))
                physical = dict(kwargs, command=command, context=pair.CONTEXT_SHA256)
                require_inert(target, physical['cwd'], physical['command'])
                self.assertFalse(target.exists())
                # Retain launch inputs before custody writes any receipts.
                launch_inputs[row['index']] = json.loads(json.dumps(dict(
                    command=list(command), pins=pins, identities=dict(
                        fixture_identity, referee_entry='experiments.al02_one_pair.verify_context',
                        referee_sha256=pins[referee_source]))))
                (review_inputs / f'{row["index"]:03d}-launch.json').write_text(
                    json.dumps(launch_inputs[row['index']]), encoding='ascii')
                result = real_transaction(target, **physical)
                terminal = target / '04-terminal.json'
                terminal_pins[row['index']] = custody.digest(terminal)
                (review_inputs / f'{row["index"]:03d}-terminal.sha256').write_text(
                    terminal_pins[row['index']], encoding='ascii')
                retained_bytes[row['index']] = {
                    path.name: path.read_bytes() for path in target.iterdir() if path.is_file()}
                return result

            def guarded_job(argv, cwd, **kwargs):
                require_inert(directory, cwd, argv)
                self.assertIs(kwargs['relay'], True)
                return real_run(argv, cwd, **kwargs)

            review_inputs = root / 'retained-inert-review-inputs'
            review_inputs.mkdir()
            launch_inputs, terminal_pins, retained_bytes = {}, {}, {}
            real_analysis = campaign.analyze_committed_panel
            verification_passes = []

            def reverify():
                verified = {}
                for index, original_inputs in launch_inputs.items():
                    inputs = json.loads((review_inputs / f'{index:03d}-launch.json').read_bytes())
                    original_pin = (review_inputs / f'{index:03d}-terminal.sha256').read_text(encoding='ascii')
                    self.assertEqual(inputs, original_inputs)
                    self.assertEqual(original_pin, terminal_pins[index])
                    item = gate.inventory()[index]
                    verified[index] = verify_attempt(
                        root / item['attempt'], dict(index=index, attempt=item['attempt'],
                            context=pair.CONTEXT, context_sha256=pair.CONTEXT_SHA256,
                            seed=pair.SEED), terminal_pin=original_pin, **inputs)
                    self.assertEqual(verified[index]['status'], 'accepted')
                    self.assertIs(verified[index]['result']['authenticated_execution'], False)
                    self.assertTrue(inputs['identities']['inert_execution'])
                    self.assertEqual(inputs['identities']['committed_seed'], item['seed'])
                    self.assertEqual(inputs['identities']['seed'], pair.SEED)
                    self.assertEqual(inputs['identities']['context_index'], index)
                verification_passes.append(tuple(verified))
                return verified

            def fixture_admissions(*args, **kwargs):
                verified = reverify()
                # Controller-facing commands describe the committed proposal only.
                # Physical launch inputs above remain separate and explicitly inert.
                return {index: dict(
                    command=[python, '-I', '-S', '-B', binding['worker'],
                             str(root / gate.inventory()[index]['attempt'] / '00-pending.json'),
                             gate.TOKEN], pins=pins,
                    identities=dict(launch_inputs[index]['identities']),
                    terminal_pin=terminal_pins[index]) for index in verified}

            def fixture_progress(actual_root, ordered, admissions):
                self.assertEqual(actual_root, root)
                verified = reverify()
                self.assertEqual(set(admissions), set(verified))
                # This adapter is scheduling evidence, never scientific analysis.
                return dict(inert_execution=True, rows=[dict(
                    index=item['index'],
                    status=verified[item['index']]['status'] if item['index'] in verified else 'not_run',
                    job_accounting=verified[item['index']]['job_accounting']
                        if item['index'] in verified else dict(cpu_ticks=0, wall_seconds=0),
                    inert_execution=True) for item in ordered])

            with (
                patch.multiple(gate, ROOT=root, STOP=root / 'STOP', CHECKOUT=checkout,
                               CONTINUATION_DESTINATION=root, __file__=str(local_source),
                               CONTINUATION_AUTHORIZATION_SHA256=authority_pin),
                patch.object(gate, 'continuation_binding', return_value=dict(binding, pins=pins)),
                patch.object(gate, 'admitted', side_effect=admit) as admission,
                patch.object(campaign.subprocess, 'check_output',
                             return_value=binding['production_head']),
                patch.object(campaign, 'pilot_admissions', side_effect=fixture_admissions),
                patch.object(campaign, 'analyze_committed_panel', side_effect=fixture_progress),
                patch.object(custody, 'transaction', side_effect=guarded_transaction) as handoff,
                patch.object(job, 'run', side_effect=guarded_job) as launch,
            ):
                # Both barriers fire before real custody, claim, or Job execution.
                original_command = command
                for corruption in ('scientific command', 'shim bytes'):
                    try:
                        if corruption == 'scientific command':
                            command = (*command[:4], binding['worker'], *command[5:])
                        else:
                            shim.write_bytes(shim_bytes + b'\n# changed\n')
                        with self.assertRaisesRegex(AssertionError, 'launch barrier refused'):
                            run_next(continuation=True)
                        real_transaction.assert_not_called()
                        launch.assert_not_called()
                        self.assertEqual(list(root.glob('attempt-*')), [])
                    finally:
                        command = original_command
                        shim.write_bytes(shim_bytes)
                handoff.reset_mock()
                admission.reset_mock()

                for index in range(8, 17):
                    row = gate.inventory()[index]
                    directory = root / row['attempt']
                    command = (python, '-I', '-S', '-B', str(shim),
                               str(directory / '00-pending.json'), gate.TOKEN)
                    proposed = (*command[:4], binding['worker'], *command[5:])
                    committed_identity = dict(frozen_identity, authorization_sha256=authority_pin,
                                              context_index=index, seed=row['seed'])
                    fixture_identity = dict(committed_identity, inert_execution=True,
                        committed_seed=row['seed'], committed_context_sha256=row['context_sha256'],
                        seed=pair.SEED, fixture_context_sha256=pair.CONTEXT_SHA256)
                    if index == 16:
                        # Missing retained launch inputs cannot be replaced by terminal self-report.
                        retained_input = review_inputs / '008-launch.json'
                        saved_input = retained_input.read_bytes()
                        try:
                            retained_input.unlink()
                            with self.assertRaises(FileNotFoundError):
                                run_next(continuation=True)
                            self.assertFalse(directory.exists())
                            self.assertEqual(launch.call_count, 8)
                        finally:
                            retained_input.write_bytes(saved_input)
                        # Reverification must use the original terminal pin, not a fresh digest.
                        terminal = root / gate.inventory()[8]['attempt'] / '04-terminal.json'
                        original_terminal = terminal.read_bytes()
                        try:
                            terminal.write_bytes(original_terminal + b' ')
                            with self.assertRaisesRegex(ValueError, '^Terminal pin differs$'):
                                run_next(continuation=True)
                            self.assertFalse(directory.exists())
                            self.assertEqual(launch.call_count, 8)
                        finally:
                            terminal.write_bytes(original_terminal)
                        for inconsistent in (False, True):
                            if inconsistent:
                                bad = campaign.batch_review(fixture_admissions(), 8)
                                bad['evidence'][0]['terminal_sha256'] = '0' * 64
                                (root / 'batch-008-review.json').write_text(json.dumps(bad))
                            with self.assertRaisesRegex(ValueError,
                                    'Independent batch review evidence differs' if inconsistent
                                    else 'Independent batch review absent'):
                                run_next(continuation=True)
                            self.assertFalse(directory.exists())
                            self.assertEqual(real_transaction.call_count, 8)
                            self.assertEqual(launch.call_count, 8)
                        verified = reverify()
                        self.assertEqual(set(verified), set(range(8, 16)))
                        admissions = fixture_admissions()
                        with self.assertRaisesRegex(ValueError, 'Campaign scientific identity differs'):
                            real_analysis(root, gate.inventory(), admissions)
                        review = campaign.batch_review(admissions, 8)
                        self.assertTrue(all(item['inert_execution'] for item in review['evidence']))
                        (root / 'batch-008-review.json').write_text(json.dumps(review))
                    run_next(continuation=True)
                    self.assertEqual(real_transaction.call_count, index - 7)
                    self.assertEqual(launch.call_count, index - 7)
                    self.assertEqual(set(reverify()), set(range(8, index + 1)))
                    # Restarting the same physical claim must refuse without a Job.
                    with self.assertRaises(FileExistsError):
                        real_transaction._mock_wraps(directory, command=command, cwd=checkout, pins=pins,
                            expected_account=owner, context=pair.CONTEXT_SHA256,
                            referee=None, consent=gate.TOKEN)
                    self.assertEqual(launch.call_count, index - 7)

                calls = handoff.call_count, launch.call_count, admission.call_count
                (root / 'STOP').touch()
                self.assertIsNone(run_next(continuation=True))
                (root / 'STOP').unlink()
                with patch.object(campaign.shutil, 'disk_usage', return_value=Mock(free=0)):
                    with self.assertRaisesRegex(ValueError, 'archive or disk reservation exhausted'):
                        run_next(continuation=True)
                self.assertEqual((handoff.call_count, launch.call_count, admission.call_count), calls)
                self.assertFalse((root / gate.inventory()[17]['attempt']).exists())
                self.assertEqual(set(launch_inputs), set(range(8, 17)))
                self.assertIn(tuple(range(8, 16)), verification_passes)
                for index, files in retained_bytes.items():
                    target = root / gate.inventory()[index]['attempt']
                    self.assertEqual({path.name: path.read_bytes() for path in target.iterdir()
                                      if path.is_file()}, files)

    def test_run_next_refuses_index_16_without_prior_batch_review(self):
        with (
            self._continuation_fixture() as (root, ordered, _, _, custody),
            patch.object(campaign, 'next_unclaimed', wraps=next_unclaimed) as select,
        ):
            with self.assertRaisesRegex(ValueError, '^Independent batch review absent$'):
                run_next(continuation=True)
            select.assert_called_once_with(root, ordered, list(range(8, 16)),
                                           stop=root / 'STOP', start=8)

            custody.transaction.assert_not_called()
            self.assertFalse((root / 'batch-008-review.json').exists())
            self.assertFalse((root / ordered[16]['attempt']).exists())

    def test_run_next_refuses_index_16_with_inconsistent_prior_batch_review(self):
        selected = []

        def record_selection(*args, **kwargs):
            row = next_unclaimed(*args, **kwargs)
            selected.append(row)
            return row

        with (
            self._continuation_fixture(with_admissions=True) as (
                root, ordered, admissions, admitted, custody
            ),
            patch.object(campaign, 'next_unclaimed', wraps=record_selection),
        ):
            review = campaign.batch_review(admissions, 8)
            review['start'] = 9
            (root / 'batch-008-review.json').write_text(json.dumps(review), encoding='utf-8')

            with self.assertRaises(ValueError) as error:
                run_next(continuation=True)

            self.assertEqual(str(error.exception), 'Independent batch review evidence differs')
            self.assertEqual(selected, [ordered[16]])
            admitted.assert_not_called()
            custody.transaction.assert_not_called()
            self.assertFalse((root / ordered[16]['attempt']).exists())

    def test_every_reviewed_boundary_advances_or_completes_without_a_real_claim(self):
        for index in range(16, 129, 8):
            with self.subTest(index=index), self._continuation_fixture(
                with_admissions=True, next_index=index
            ) as (root, ordered, admissions, admitted, custody):
                for start in range(8, index - 8, 8):
                    (root / f'batch-{start:03d}-review.json').write_text(
                        json.dumps(campaign.batch_review(admissions, start)), encoding='utf-8')

                with self.assertRaisesRegex(ValueError, '^Independent batch review absent$'):
                    run_next(continuation=True)
                admitted.assert_not_called()
                custody.transaction.assert_not_called()

                start = index - 8
                (root / f'batch-{start:03d}-review.json').write_text(
                    json.dumps(campaign.batch_review(admissions, start)), encoding='utf-8')
                with patch.object(custody, 'pinned_path', side_effect=[root, root / 'checkout']):
                    if index == 128:
                        self.assertIsNone(run_next(continuation=True))
                        custody.transaction.assert_not_called()
                    else:
                        custody.transaction.side_effect = None
                        custody.transaction.return_value = sentinel.custody_result
                        self.assertIs(run_next(continuation=True), sentinel.custody_result)
                        self.assertEqual(custody.transaction.call_args.args[0],
                                         root / ordered[index]['attempt'])
                        self.assertFalse((root / ordered[index]['attempt']).exists())

    def test_order_completion_stop_and_unresolved_claim(self):
        rows = gate.inventory()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            stop = root/'STOP'
            for i in range(8,128):
                self.assertEqual(next_unclaimed(root,rows,list(range(8,i)),
                                                stop=stop,start=8),rows[i])
                (root/rows[i]['attempt']).mkdir()
                with self.assertRaisesRegex(ValueError,'Unreconciled attempt claim'):
                    next_unclaimed(root,rows,list(range(8,i)),stop=stop,start=8)
            self.assertIsNone(next_unclaimed(root,rows,list(range(8,128)),
                                             stop=stop,start=8))
            stop.touch()
            self.assertIsNone(next_unclaimed(root,rows,[],stop=stop,start=8))
