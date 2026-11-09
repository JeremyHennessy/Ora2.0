import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from unittest import TestCase

from experiments import al02_campaign_admission as gate

ROOT=Path(__file__).resolve().parents[1]
PROBE=ROOT/'tests/al02_release_rehearsal/campaign-controller-probe.py'


class ControllerProcessTests(TestCase):
    def stage(self):
        tmp=TemporaryDirectory(prefix='ora-controller-probe-')
        self.addCleanup(tmp.cleanup)
        root=Path(tmp.name).resolve()
        (root/'inert.py').write_bytes(b'raise AssertionError("Controller crash probe must not launch")\n')
        (root/'campaign-authority.json').write_text(json.dumps(dict(
            schema='al02-campaign-one-claim-per-index-v1',owner=gate.OWNER,
            binding_sha256=gate.BINDING_SHA256,package_sha256=gate.PACKAGE_SHA256,
            contexts_sha256=gate.CONTEXTS_SHA256)))
        return root

    def argv(self,root,mode):
        return [sys.executable,'-I','-B','-S',str(PROBE),str(root),mode]

    def invoke(self,root,mode):
        return subprocess.run(self.argv(root,mode),cwd=ROOT,capture_output=True,text=True,timeout=15)

    def test_actual_controller_race(self):
        root=self.stage()
        with subprocess.Popen(self.argv(root,'hold'),cwd=ROOT,stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,text=True) as first:
            try:
                deadline=time.monotonic()+8
                while not (root/'holding').exists():
                    self.assertIsNone(first.poll(),first.communicate() if first.poll() is not None else '')
                    self.assertLess(time.monotonic(),deadline)
                    time.sleep(.01)
                second=self.invoke(root,'restart')
                self.assertEqual(second.returncode,10,second)
                self.assertIn('Campaign ownership lock unavailable',second.stdout)
                self.assertFalse((root/'attempt-000').exists())
            finally:
                (root/'continue').touch()
            stdout,stderr=first.communicate(timeout=15)
        self.assertEqual(first.returncode,42,(stdout,stderr))
        self.assertEqual(list((root/'attempt-000').iterdir()),[])
        self.assertFalse((root/'attempt-001').exists())
        restart=self.invoke(root,'restart')
        self.assertIn('Unreconciled attempt claim',restart.stdout)
        print(json.dumps(dict(race_loser=second.stdout.strip(),winner_exit=first.returncode,
                              restart=restart.stdout.strip())))

    def test_actual_controller_crashes_and_stop(self):
        for mode,code,claimed,pending in [('before-lock',40,False,False),
                                           ('before-claim',41,False,False),
                                           ('after-claim',42,True,False),
                                           ('after-pending',43,True,True)]:
            with self.subTest(mode=mode):
                root=self.stage()
                result=self.invoke(root,mode)
                self.assertEqual(result.returncode,code,result)
                attempt=root/'attempt-000'
                self.assertEqual(attempt.exists(),claimed)
                self.assertEqual((attempt/'00-pending.json').exists(),pending)
                self.assertFalse((attempt/'02-release-intent.json').exists())
                restart=self.invoke(root,'restart' if claimed else 'before-claim')
                if claimed:
                    self.assertEqual(restart.returncode,10,restart)
                    self.assertIn('Unreconciled attempt claim',restart.stdout)
                else:
                    self.assertEqual(restart.returncode,41,restart)
                self.assertFalse((root/'attempt-001').exists())
                print(json.dumps(dict(crash=mode,exit=code,claimed=claimed,pending=pending,
                                      restart_exit=restart.returncode)))
        root=self.stage()
        (root/'STOP').touch()
        result=self.invoke(root,'restart')
        self.assertEqual(result.returncode,0,result)
        self.assertEqual(result.stdout.strip(),'STOP')
        self.assertFalse((root/'attempt-000').exists())


    def live_fixture(self, root):
        import shutil
        template=(ROOT/'tests/al02_release_rehearsal/inert-worker.py').read_text()
        (root/'inert.py').write_text(template.replace('ORA-PHASE6-INERT',gate.TOKEN),encoding='ascii')
        historical=Path('D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3/raw.bin')
        shutil.copyfile(historical,root/'lawful.bin')

    def test_two_controller_owned_inert_transitions(self):
        from tools.al02_campaign_evidence import verify_attempt
        from experiments import al02_one_pair as pair
        import shutil
        import os
        root=self.stage()
        self.live_fixture(root)
        reviewed={}
        for index in range(2):
            result=self.invoke(root,'live')
            self.assertEqual(result.returncode,0,result)
            attempt=root/f'attempt-{index:03d}'
            pending=json.loads((attempt/'00-pending.json').read_bytes())
            terminal=attempt/'04-terminal.json'
            from hashlib import sha256
            admission=dict(command=pending['command'],pins=pending['pins'],
                           identities=pending['release_identities'],
                           terminal_pin=sha256(terminal.read_bytes()).hexdigest())
            identity=admission['identities']
            self.assertTrue(identity['inert_execution'])
            self.assertEqual(identity['context_index'],index)
            self.assertEqual(identity['committed_seed'],gate.inventory()[index]['seed'])
            verified=verify_attempt(attempt,dict(index=index,attempt=attempt.name,
                 context=pair.CONTEXT,context_sha256=pair.CONTEXT_SHA256,seed=pair.SEED),**admission)
            self.assertEqual(verified['result']['contrast'],0)
            reviewed[str(index)]=admission
            (root/'reviewed-admissions.json').write_text(json.dumps(reviewed))
            print(json.dumps(dict(index=index,terminal_sha256=admission['terminal_pin'],
                                  committed_seed=identity['committed_seed'],inert_seed=identity['seed'])))
        self.assertFalse((root/'attempt-002').exists())
        out=os.environ.get('AL02_CAMPAIGN_TEST_EVIDENCE')
        if out:
            shutil.copytree(root,Path(out)/'controller-transitions')

    def test_actual_controller_release_and_terminal_crashes(self):
        for mode,code,terminal in [('after-intent',44,False),('after-terminal',45,True)]:
            with self.subTest(mode=mode):
                root=self.stage()
                self.live_fixture(root)
                result=self.invoke(root,mode)
                self.assertEqual(result.returncode,code,result)
                attempt=root/'attempt-000'
                self.assertTrue((attempt/'02-release-intent.json').exists())
                self.assertEqual((attempt/'04-terminal.json').exists(),terminal)
                self.assertEqual((attempt/'partial.jsonl').exists(),terminal)
                # Restart only reads/reconciles. Install the no-launch shim
                # expected by the restart probe, outside the claimed directory.
                (root/'inert.py').write_bytes(b'raise AssertionError("Controller crash probe must not launch")\n')
                restart=self.invoke(root,'restart')
                self.assertEqual(restart.returncode,10,restart)
                expected='Terminal receipt lacks independent admission' if terminal else 'Unreconciled attempt claim'
                self.assertIn(expected,restart.stdout)
                self.assertFalse((root/'attempt-001').exists())
                print(json.dumps(dict(crash=mode,exit=code,terminal=terminal,restart=restart.stdout.strip())))

    def test_pending_write_failure_and_capacity_refusal(self):
        root=self.stage()
        result=self.invoke(root,'capacity')
        self.assertIn('Campaign archive or disk reservation exhausted',result.stdout)
        self.assertFalse((root/'attempt-000').exists())
        result=self.invoke(root,'pending-fail')
        self.assertIn('Injected pending write failure',result.stdout)
        failure=json.loads((root/'attempt-000/99-failed.json').read_bytes())
        self.assertFalse(failure['release_intent'])
        self.assertIn('Unreconciled attempt claim',self.invoke(root,'restart').stdout)


    def test_controller_positive_uptake_fixture(self):
        from hashlib import sha256
        import os
        import shutil
        from tools.al02_natural_b_analysis import analyze_pair
        root=self.stage()
        self.live_fixture(root)
        path=Path('D:/OraLab/drafts/ora-phase6-admission/lawful.bin')
        data=path.read_bytes()
        self.assertEqual(sha256(data).hexdigest(),
                         '1c6332c61c101402c5b16cebafa8a0bb3df70e411ef6e0f49619d129bbb1059d')
        (root/'lawful.bin').write_bytes(data)
        result=self.invoke(root,'positive')
        self.assertEqual(result.returncode,0,result)
        attempt=root/'attempt-000'
        self.assertEqual((attempt/'raw.bin').read_bytes(),data)
        terminal=json.loads((attempt/'04-terminal.json').read_bytes())
        self.assertTrue(terminal['release_identities']['inert_execution'])
        self.assertEqual(terminal['result']['contrast'],3)
        payload=json.loads(data)
        analysis=analyze_pair(42,payload['checkpoint'].encode(),payload['checkpoint_sha256'],
                              payload['branches'])
        self.assertEqual(analysis['result'],terminal['result'])
        active=analysis['branches']['accessible']
        self.assertEqual(analysis['result']['branches']['accessible']['b_meals'],10)
        self.assertTrue(active['origins'])
        self.assertTrue(any(row['slots'] and row['same_program_children']
                            for row in active['actors'].values()))
        print(result.stdout.strip())
        out=os.environ.get('AL02_CAMPAIGN_TEST_EVIDENCE')
        if out:
            shutil.copytree(root,Path(out)/'controller-positive-uptake')

    def test_controller_terminated_during_inert_worker(self):
        from experiments.process_limits import process_exited
        import json
        root=self.stage()
        self.live_fixture(root)
        shim=root/'inert.py'
        source=shim.read_text().replace(
            "        if attempt.name == 'interrupt':",
            "        (attempt.parent / 'worker-ready').write_text(str(os.getpid()))\n"
            "        import time\n"
            "        time.sleep(5)\n"
            "        if attempt.name == 'interrupt':")
        shim.write_text(source,encoding='ascii')
        with subprocess.Popen(self.argv(root,'during-worker'),cwd=ROOT,stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,text=True) as parent:
            try:
                deadline=time.monotonic()+6
                marker=root/'worker-ready'
                while not marker.exists() or not marker.stat().st_size:
                    self.assertIsNone(parent.poll())
                    self.assertLess(time.monotonic(),deadline)
                    time.sleep(.01)
                worker=int(marker.read_text())
                attempt=root/'attempt-000'
                relay=json.loads((attempt/'01-verified.json').read_bytes())['bootstrap_pid']
            finally:
                parent.terminate()
                parent.communicate(timeout=10)
        deadline=time.monotonic()+6
        while not all(process_exited(pid) for pid in (worker,relay)):
            self.assertLess(time.monotonic(),deadline)
            time.sleep(.01)
        self.assertGreater((attempt/'partial.jsonl').stat().st_size,0)
        self.assertFalse((attempt/'04-terminal.json').exists())
        shim.write_bytes(b'raise AssertionError("Controller crash probe must not launch")\n')
        self.assertIn('Unreconciled attempt claim',self.invoke(root,'restart').stdout)
        print(json.dumps(dict(crash='during-worker',worker=worker,relay=relay,closed=True,
                              partial_bytes=(attempt/'partial.jsonl').stat().st_size)))


    def test_supervised_pilot_advances_only_after_evidence_recheck(self):
        import os
        import shutil
        root=self.stage()
        self.live_fixture(root)
        (root/'pilot-authority.json').write_text(json.dumps(dict(
            schema='al02-supervised-eight-one-claim-per-index-v1',owner=gate.OWNER,
            pilot_binding_sha256=gate.PILOT_BINDING_SHA256)))
        for index in range(2):
            result=self.invoke(root,'pilot-live')
            self.assertEqual(result.returncode,0,result)
            attempt=root/f'attempt-{index:03d}'
            terminal=json.loads((attempt/'04-terminal.json').read_bytes())
            self.assertEqual(terminal['release_identities']['pilot_binding_sha256'],gate.PILOT_BINDING_SHA256)
            self.assertEqual(terminal['release_identities']['context_index'],index)
            self.assertTrue(terminal['release_identities']['inert_execution'])
        self.assertFalse((root/'reviewed-admissions.json').exists())
        (root/'STOP').touch()
        review=self.invoke(root,'pilot-review')
        self.assertEqual(review.returncode,0,review)
        summary=json.loads(review.stdout)
        self.assertEqual((summary['accepted'],summary['committed'],summary['distribution']),
                         (2,8,[0,0]))
        self.assertIsNone(summary['all_context_mean'])
        (root/'STOP').unlink()
        out=os.environ.get('AL02_CAMPAIGN_TEST_EVIDENCE')
        if out:
            shutil.copytree(root,Path(out)/'supervised-eight-transitions')
        journal=root/'attempt-000/partial.jsonl'
        journal.write_bytes(journal.read_bytes()+b' ')
        failure=self.invoke(root,'pilot-live')
        self.assertEqual(failure.returncode,10,failure)
        self.assertIn('Journal differs',failure.stdout)
        self.assertFalse((root/'attempt-002').exists())

    def test_supervised_pilot_exact_inactive_scope(self):
        from tools.run_al02_campaign import run_next
        binding=gate.pilot_binding()
        self.assertEqual(binding['budget']['pairs'],8)
        with self.assertRaisesRegex(ValueError,'authorization absent'):
            run_next(pilot=True)
        for row in gate.inventory():
            target=gate.PILOT_DESTINATION/row['attempt']
            command=[binding['python'],'-I','-S','-B',binding['worker'],
                     str(target/'00-pending.json'),gate.TOKEN]
            message='authorization absent' if row['index']<8 else 'destination differs'
            with self.assertRaisesRegex(ValueError,message):
                gate.admitted(target,gate.CHECKOUT,command,gate.OWNER,row['context_sha256'],
                              gate.LIMITS,binding['pins'])
        self.assertFalse(gate.PILOT_DESTINATION.exists())


    def test_pilot_controller_stop_capacity_and_consumed_claim(self):
        root=self.stage()
        (root/'pilot-authority.json').write_text(json.dumps(dict(
            schema='al02-supervised-eight-one-claim-per-index-v1',owner=gate.OWNER,
            pilot_binding_sha256=gate.PILOT_BINDING_SHA256)))
        (root/'STOP').touch()
        result=self.invoke(root,'pilot-restart')
        self.assertEqual(result.stdout.strip(),'STOP')
        self.assertFalse((root/'attempt-000').exists())
        (root/'STOP').unlink()
        self.assertIn('Campaign archive or disk reservation exhausted',
                      self.invoke(root,'pilot-capacity').stdout)
        self.assertFalse((root/'attempt-000').exists())
        self.assertEqual(self.invoke(root,'pilot-after-claim').returncode,42)
        self.assertIn('Unreconciled attempt claim',self.invoke(root,'pilot-restart').stdout)
        self.assertFalse((root/'attempt-001').exists())
