"""Exercise exact inactive campaign artifacts and disposable custody effects."""
from hashlib import sha256
import json
import os
import shutil
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

from experiments import al02_campaign_admission as gate, al02_one_pair_custody as custody
from experiments import al02_one_pair as pair, al02_one_pair_job as job
from tools.al02_campaign_evidence import verify_attempt
from tools.run_al02_campaign import run_next


class CampaignAdmissionTests(TestCase):
    def test_all_frozen_scopes_and_inactive_controller(self):
        b=gate.binding()
        rows=gate.inventory()
        for row in rows:
            dest=gate.DESTINATION/row['attempt']
            cmd=[b['python'],'-I','-S','-B',b['worker'],str(dest/'00-pending.json'),gate.TOKEN]
            with self.assertRaisesRegex(ValueError,'authorization absent'):
                gate.admitted(dest,gate.CHECKOUT,cmd,gate.OWNER,row['context_sha256'],gate.LIMITS,b['pins'])
            with self.assertRaisesRegex(ValueError,'scope differs'):
                gate.admitted(dest,gate.CHECKOUT,cmd,gate.OWNER,'0'*64,gate.LIMITS,b['pins'])
        with self.assertRaisesRegex(ValueError,'authorization absent'):
            run_next()
        self.assertFalse(gate.DESTINATION.exists())

    def test_exact_release_identity_through_real_inert_custody(self):
        root=Path(__file__).resolve().parents[1]
        real_admit=gate.admitted
        real_read=gate.read_pinned
        b=gate.binding()
        row=gate.inventory()[0]
        destination=gate.DESTINATION/row['attempt']
        proposed=[b['python'],'-I','-S','-B',b['worker'],str(destination/'00-pending.json'),gate.TOKEN]
        authority=json.dumps(dict(schema='al02-campaign-one-claim-per-index-v1',owner=gate.OWNER,
            binding_sha256=gate.BINDING_SHA256,package_sha256=gate.PACKAGE_SHA256,
            contexts_sha256=gate.CONTEXTS_SHA256)).encode()
        pin=sha256(authority).hexdigest()
        with TemporaryDirectory() as temp:
            stage=Path(temp).resolve()
            authority_file=stage/'campaign-authority.json'
            authority_file.write_bytes(authority)
            fixture=stage/'lawful.bin'
            historical=Path('D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3/raw.bin')
            fixture.write_bytes(historical.read_bytes())
            shim=stage/'inert.py'
            template=(root/'tests/al02_release_rehearsal/inert-worker.py').read_text()
            shim.write_text(template.replace('ORA-PHASE6-INERT',gate.TOKEN),encoding='ascii')
            attempt=stage/'attempt-v3'
            python=getattr(sys,'_base_executable',sys.executable)
            command=[python,'-I','-S','-B',str(shim),str(attempt/'00-pending.json'),gate.TOKEN]
            paths=(Path(python),shim,fixture,Path(gate.__file__),Path(pair.__file__),
                   Path(custody.__file__),Path(job.__file__),
                   root/'experiments/process_limits.py',root/'experiments/al02_one_pair_worker.py')
            pins={str(path):custody.digest(path) for path in paths}
            def reader(path, expected):
                if path == gate.DESTINATION/'campaign-authority.json':
                    path=authority_file
                return real_read(path,expected)
            def inert_admit(directory,cwd,argv,owner,context,limits,actual_pins):
                self.assertEqual((directory,cwd,list(argv),context,actual_pins),
                                 (attempt,root,command,pair.CONTEXT_SHA256,pins))
                self.assertEqual((owner,limits),(gate.OWNER,gate.LIMITS))
                identity=real_admit(destination,gate.CHECKOUT,proposed,owner,
                                    row['context_sha256'],limits,b['pins'])
                # Scientific scope is verified separately from the historical
                # raw fixture. The terminal cannot be accepted as a panel row.
                return dict(identity,seed=pair.SEED,committed_seed=row['seed'],
                            inert_execution=True,fixture_context_sha256=pair.CONTEXT_SHA256)
            with mock.patch.multiple(gate,AUTHORIZATION_SHA256=pin,read_pinned=reader,admitted=inert_admit):
                def run():
                    return custody.transaction(attempt,command=command,cwd=root,pins=pins,
                        expected_account=gate.OWNER,context=pair.CONTEXT_SHA256,
                        referee=None,consent=gate.TOKEN)
                self.assertEqual(run()['contrast'],0)
                with self.assertRaises(FileExistsError):
                    run()
            terminal=attempt/'04-terminal.json'
            data=json.loads(terminal.read_bytes())
            identity=data['release_identities']
            self.assertEqual(identity['binding_sha256'],gate.BINDING_SHA256)
            self.assertEqual(identity['package_sha256'],gate.PACKAGE_SHA256)
            self.assertEqual(identity['contexts_sha256'],gate.CONTEXTS_SHA256)
            self.assertTrue(identity['inert_execution'])
            checked=verify_attempt(attempt,dict(index=0,attempt=attempt.name,context=pair.CONTEXT,
                context_sha256=pair.CONTEXT_SHA256,seed=pair.SEED),command=command,pins=pins,
                identities=identity,terminal_pin=custody.digest(terminal))
            self.assertEqual(checked['result']['branches']['accessible']['b_meals'],0)
            self.assertFalse(checked['result']['authenticated_execution'])
            with self.assertRaisesRegex(ValueError,'Attempt directory differs'):
                verify_attempt(attempt,row,command=command,pins=pins,
                               identities=identity,terminal_pin=custody.digest(terminal))
            evidence = os.environ.get('AL02_CAMPAIGN_TEST_EVIDENCE')
            if evidence:
                shutil.copytree(attempt, Path(evidence)/'inert-attempt')
            print(json.dumps(dict(terminal_sha256=custody.digest(terminal),identities=identity,
                                  result=checked['result'])))
        self.assertFalse(gate.DESTINATION.exists())
