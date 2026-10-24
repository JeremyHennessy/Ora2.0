"""Synthetic grant/receipt refusals only;no locks,processes,grants or Worlds."""
import copy,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import digital_pilot74_owner_registration_v1 as r
from experiments import digital_pilot74_outer_owner_v1 as outer


class Registration(unittest.TestCase):
    def fixture(self):
        registration={'path':'synthetic','extent':1,'sha256':'f'*64}
        reg=dict(owner={'pid':123,'birth':'456'},operator_lock={'synthetic':True},source_head='a'*40,
            source_files={'synthetic.py':'b'*64},python={'synthetic':True},argv_sha256='c'*64,prepared_monotonic_ns=1)
        grant=dict(schema='PILOT74-NEW-OWNER-PROBE-GRANT-v1',verdict='PASS',registration=registration,
            cases=r.CASES,reviewer_identity='SYNTHETIC',review_evidence=['fixture'],worlds=0,production_admission=False,
            issued_monotonic_ns=2,expires_monotonic_ns=100*10**9,**{k:reg[k] for k in reg if k!='prepared_monotonic_ns'})
        return registration,reg,grant

    def test_valid_shape_is_not_a_production_grant(self):
        pin,reg,grant=self.fixture();r.validate_grant(grant,pin,reg,3)
        self.assertFalse(grant['production_admission'])

    def test_expired_or_short_or_overlong_grant_refused(self):
        for expiry in [0,30*10**9,301*10**9]:
            pin,reg,g=self.fixture();g['expires_monotonic_ns']=expiry
            with self.assertRaises(AssertionError):r.validate_grant(g,pin,reg,3)

    def test_other_owner_registration_command_and_source_refused(self):
        for key in ['owner','operator_lock','registration','source_head','source_files','python','argv_sha256']:
            pin,reg,g=self.fixture();g[key]='changed'
            with self.assertRaises(AssertionError):r.validate_grant(g,pin,reg,3)

    def test_scientific_or_extra_case_authority_refused(self):
        for key,value in [('worlds',1),('production_admission',True),('cases',['ordinary','extra'])]:
            pin,reg,g=self.fixture();g[key]=value
            with self.assertRaises(AssertionError):r.validate_grant(g,pin,reg,3)

    def test_corrupt_physical_pin_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'data.json';r.write(path,{'a':1});p=r.pin(path);path.write_bytes(b'changed')
            with self.assertRaises(AssertionError):r.read(p)

    def test_deadline_cannot_be_extended_or_boolean(self):
        # Invalid boundary inputs fail before any process creation.
        from unittest.mock import patch,Mock
        for value in [True,0,3600001]:
            k=Mock();k.GetTickCount64.return_value=1
            # Exercise deadline validation past the platform gate without any
            # native call. The non-Windows refusal has its own test below.
            with patch.object(outer.os,'name','nt'),patch.object(outer.win,'kernel',return_value=k):
                with self.assertRaises(ValueError):outer.launch({'wall_ms':value},lambda request:True)
            k.CreateProcessW.assert_not_called()

    def test_non_windows_refuses_before_kernel_or_admission(self):
        from unittest.mock import patch,Mock
        admission=Mock()
        with patch.object(outer.os,'name','posix'),patch.object(outer.win,'kernel') as kernel:
            with self.assertRaisesRegex(OSError,'Windows only'):
                outer.launch({'wall_ms':1},admission)
        kernel.assert_not_called();admission.assert_not_called()

    def test_explicit_missing_terminal_observation_is_unknown(self):
        self.assertFalse(r.observed_closed(None))
        self.assertFalse(r.observed_closed({'after_termination':None}))
        self.assertFalse(r.observed_closed({'after_termination':{'closure_observed':False}}))

    def test_unspecified_shutdown_is_not_the_expected_crash(self):
        evidence={'phase':'wait','caller_exit_code':1,'command':['synthetic'],
                  'after_termination':{'closure_observed':True}}
        with self.assertRaises(AssertionError):r.verify_crash(evidence,{},['synthetic'],'synthetic')

    def test_nonzero_nested_exit_rejected_even_if_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)
            (path/'level-2.json').write_text('{}');(path/'level-1.json').write_text('{}')
            with self.assertRaises((AssertionError,KeyError)):
                r.verify_nested(path,{'native':{'command':[],'exit_code':1}},['python','-B','probe','case','reg','sha','dir','ordinary'])

    @unittest.skipUnless(sys.platform=='win32','Windows-only process policy;Popen mocked')
    def test_probe_child_explicitly_avoids_console_without_shell_or_inheritance(self):
        from unittest.mock import patch
        from experiments import digital_pilot74_owner_probe_v1 as probe
        with patch.object(probe.subprocess,'Popen') as create:
            probe.spawn_wait_child(['synthetic.exe'])
        args=create.call_args.kwargs
        self.assertEqual(args['creationflags'],probe.subprocess.DETACHED_PROCESS)
        self.assertTrue(args['close_fds'])
        self.assertFalse(args.get('shell',False))

    def crash_fixture(self):
        command=['D:/synthetic/python.exe','-B','probe.py','case','reg','sha','dir','caller-crash-live-child']
        child={'pid':222,'creation_filetime_decimal':'333','caller':{'pid':111,'creation_filetime_decimal':'444'},
            'child_wait_before_crash':258,'expected_caller_exit':78,'command':[command[0],'-B','probe.py','leaf-wait',*command[4:]]}
        evidence={'phase':'wait','caller_exit_code':78,'command':command,'after_termination':{'closure_observed':True},
            'before_termination':{'process_wait':0,'pid':111,'creation_filetime_decimal':'444','pids':[222],
                'usage':{'started_processes':2,'active_before_close':1}},
            'owned_identity_snapshot_before_termination':{'listed_pids':[222],'errors':[],
                'handles':[{'actual_pid':222,'membership':True,'birth':'333','image':command[0],'wait_result':258,'errors':[]}]}}
        return evidence,child,command

    def test_exact_live_child_identity_accepted_in_synthetic_fixture(self):
        evidence,child,command=self.crash_fixture();r.verify_crash(evidence,child,command,command[0])

    def test_wrong_child_birth_image_membership_or_wait_is_refused(self):
        for key,value in [('birth','wrong'),('image','D:/wrong.exe'),('membership',False),('wait_result',0)]:
            evidence,child,command=self.crash_fixture();evidence['owned_identity_snapshot_before_termination']['handles'][0][key]=value
            with self.assertRaises(AssertionError):r.verify_crash(evidence,child,command,command[0])


if __name__=='__main__':unittest.main()
