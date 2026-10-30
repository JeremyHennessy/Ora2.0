"""Offline refusal/archive tests only. OS fixtures have a separate finite entry."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,PropertyMock
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import eka1_native_probe as probe


class ProbeContractChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT);self.out=Path(self.tmp.name)
        self.owner=object.__new__(probe.owner_source.NativeOwnerCandidate)
        self.fd=os.open(self.out/'ledger',os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_BINARY,0o600)
        self.ledger=probe.owner_source.ledger_class()(self.fd)
        self.owner._closed=False;self.owner._failed=None;self.owner._cleanup_errors=[];self.owner._ledger=self.ledger;self.owner._fd=None
        for dose,index in [(1,i) for i in range(7)]+[(8,0),(8,1)]:
            self.ledger.role(dose,index)
            for unused in range(4):self.ledger.process_birth(dose,index)
        self.owner._path=self.out/'ledger'
        self.owner._requests=tuple(sorted({(d,r):probe.sha(probe.owner_source.canonical({'schema':'EKA-SYNTHETIC-ONLY-v1','dose':d,'role':r})) for d in (1,8) for r in probe.owner_source.ROLES}.items()))
        registration=probe.registration_for({},0)
        (self.out/'registration.json').write_bytes(probe.owner_source.canonical(registration))
        self.owner._assignment=probe.sha((self.out/'registration.json').read_bytes())
        self.property=patch.object(probe.owner_source.NativeOwnerCandidate,'ledger',new_callable=PropertyMock,return_value=self.ledger);self.property.start()
        # Only entry/refusal fixtures: no assertion of native dependency custody.
        self.custody=patch.object(probe,'custody',return_value={});self.custody.start()
    def tearDown(self):
        self.custody.stop();self.property.stop();self.ledger.close();os.close(self.fd);self.tmp.cleanup()
    def test_wrong_owner_before_kernel_or_files(self):
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaises(TypeError):probe.launch(None,None,0,object(),'x',0)
    def test_compiler_quotes_are_script_bytes_not_escaped_argv(self):
        setup=Path('C:/Program Files/VS/vcvars64.bat');line='"C:/Program Files/VS/cl.exe" /W4 /WX fixed.c'
        command=probe.compiler_command(self.out,'fixture',setup,line)
        self.assertEqual(command[1:3],['/d','/c']);self.assertNotIn('"',command[-1]);self.assertNotIn('\\"',command[-1])
        raw=(self.out/'build-fixture.cmd').read_bytes()
        self.assertIn(('call "'+str(setup)+'"').encode(),raw);self.assertIn(line.encode(),raw)
        self.assertLess(raw.index(b'set "VSCMD_SKIP_SENDTELEMETRY=1"'),raw.index(b'call "'))
        self.assertNotIn(b'\\"',raw)
        self.assertLess(raw.index(b'if errorlevel 1 exit /b %errorlevel%'),raw.index(line.encode()))
        self.assertEqual(json.loads((self.out/'compiler-script-fixture.json').read_text())['script_sha256'],probe.sha(raw))
        with self.assertRaises(FileExistsError):probe.compiler_command(self.out,'fixture',setup,line)
    def test_compiler_script_unsafe_path_refused_before_write(self):
        with self.assertRaisesRegex(ValueError,'no whitespace'):probe.compiler_command(self.out/'space dir','fixture',Path('setup.bat'),'fixed')
        self.assertFalse((self.out/'space dir').exists())
    def test_bool_and_unlisted_case_rejected_before_effect(self):
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaises(ValueError):probe.launch(None,None,True,self.owner,'x',0)
            for mode in (-1,9,1.0):
                with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.launch(None,None,mode,self.owner,'x',0)
    def test_failed_slot_is_never_refunded(self):
        with patch.object(probe,'_launch',side_effect=OSError('synthetic start failure')) as invoke:
            with self.assertRaises(OSError):probe.launch(None,self.out,0,self.owner,self.owner._assignment,0)
            with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.launch(None,self.out,1,self.owner,self.owner._assignment,0)
            self.assertEqual(invoke.call_count,1)
            self.assertEqual(self.ledger._births,36);self.assertTrue(self.owner._closed);self.assertIn('synthetic start failure',self.owner._failed)
    def test_wrong_assignment_rejected_before_kernel(self):
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaisesRegex(ValueError,'Assignment'):probe.launch(self.out/'eka1_probe_guardian.exe',self.out,0,self.owner,'wrong',0)
    def test_resealed_alternate_limits_and_owner_refused(self):
        for field,value in (('raw_bytes_per_case',65537),('owner_birth',[1,1]),('scientific_admission',True)):
            registration=probe.registration_for({},0);registration[field]=value
            raw=probe.owner_source.canonical(registration);(self.out/'registration.json').write_bytes(raw);self.owner._assignment=probe.sha(raw)
            with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
                with self.assertRaisesRegex(ValueError,'registered synthetic'):probe.verify_reservations(self.owner,self.out,self.owner._assignment)
    def test_changed_source_refused_before_kernel(self):
        with patch.object(probe,'custody',return_value={'changed':'source'}),patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaisesRegex(ValueError,'Source/dependency'):probe.launch(None,self.out,0,self.owner,self.owner._assignment,0)
    def test_changed_binary_rejected_before_kernel(self):
        seal=self.owner._assignment
        exe=self.out/'eka1_probe_guardian.exe';exe.write_bytes(b'unreviewed')
        (self.out/'binary-custody.json').write_text(json.dumps({'artifact_sha256':'0'*64}))
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaisesRegex(ValueError,'compiled guardian'):probe.launch(exe,self.out,0,self.owner,seal,0)
    def test_empty_ledger_cannot_build_or_launch(self):
        self.ledger._births=0
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaisesRegex(ValueError,'36-birth'):probe.build(self.out,self.owner,{},self.owner._assignment,0)
            with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.launch(None,self.out,0,self.owner,self.owner._assignment,0)
    def test_unexpected_native_result_terminally_closes_owner(self):
        result={'guardian_exit':125,'inner':None}
        with patch.object(probe,'_launch',return_value=result) as invoke:
            with self.assertRaisesRegex(ValueError,'closure/capture'):probe.launch(None,self.out,0,self.owner,self.owner._assignment,0)
            with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.launch(None,self.out,1,self.owner,self.owner._assignment,0)
        self.assertEqual(invoke.call_count,1);self.assertEqual(self.ledger._births,36)
    def test_failed_build_cannot_reuse_owner(self):
        with patch.object(probe,'_build',side_effect=OSError('compiler failure')) as invoke:
            with self.assertRaisesRegex(OSError,'compiler failure'):probe.build(self.out,self.owner,{},self.owner._assignment,0)
            with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.build(self.out,self.owner,{},self.owner._assignment,0)
        self.assertEqual(invoke.call_count,1);self.assertTrue(self.owner._closed);self.assertEqual(self.ledger._births,36)
    def test_changed_physical_reservation_chain_refused(self):
        raw=self.owner._path.read_bytes();self.owner._path.write_bytes(raw.replace(b'process_birth',b'process_forge',1))
        with self.assertRaisesRegex(ValueError,'chain/catalog'):probe.verify_reservations(self.owner,self.out,self.owner._assignment)
    def test_exact_archive_restore_is_data_only(self):
        raw=b'\x00partial\xffevidence';(self.out/'partial.raw').write_bytes(raw)
        probe.archive_evidence(self.out)
        self.assertEqual((self.out/'restored/partial.raw').read_bytes(),raw)
        receipt=json.loads((self.out/'archive-verification.json').read_text())
        self.assertEqual(receipt['file_count'],3);self.assertFalse(receipt['restored_code_executed'])
    def test_existing_archive_not_overwritten(self):
        (self.out/'evidence.zip').write_bytes(b'retained')
        with self.assertRaises(FileExistsError):probe.archive_evidence(self.out)
        self.assertEqual((self.out/'evidence.zip').read_bytes(),b'retained')
    def test_archive_failure_still_stops_watchdog(self):
        watchdog=Mock();watchdog.EkaStopWatchdog.return_value=True
        report={'status':'fixture','elapsed_seconds':0,'results':[]}
        with patch.object(probe,'_execution_consumed',False),patch.object(probe,'_evidence_directory',self.out),patch.object(probe,'_owner_watchdog_started',True),patch.object(probe,'_owner_watchdog',watchdog),patch.object(probe,'qualify',return_value=report),patch.object(probe,'archive_evidence',side_effect=OSError('archive failed')):
            with self.assertRaisesRegex(OSError,'archive failed'):probe.execute(self.out)
        watchdog.EkaStopWatchdog.assert_called_once()
    def test_primary_failure_survives_archive_and_stop_failures(self):
        watchdog=Mock();watchdog.EkaStopWatchdog.side_effect=RuntimeError('stop failed')
        with patch.object(probe,'_execution_consumed',False),patch.object(probe,'_evidence_directory',self.out),patch.object(probe,'_owner_watchdog_started',True),patch.object(probe,'_owner_watchdog',watchdog),patch.object(probe,'qualify',side_effect=ValueError('first cause')),patch.object(probe,'archive_evidence',side_effect=OSError('archive failed')):
            with self.assertRaisesRegex(ValueError,'first cause'):probe.execute(self.out)
        watchdog.EkaStopWatchdog.assert_called_once()
        self.assertTrue((self.out/'archive-failure.json').is_file());self.assertTrue((self.out/'watchdog-stop-failure.json').is_file())
    def test_rejected_existing_directory_is_not_archived(self):
        with patch.object(probe,'_execution_consumed',False),patch.object(probe,'_evidence_directory',None),patch.object(probe,'_owner_watchdog_started',False),patch.object(probe,'qualify',side_effect=FileExistsError('old evidence')),patch.object(probe,'archive_evidence') as archive:
            with self.assertRaises(FileExistsError):probe.execute(self.out)
        archive.assert_not_called()
    def test_cleanup_failure_matrix_retains_first_cause_even_without_writable_receipts(self):
        report={'status':'fixture','elapsed_seconds':0,'results':[]}
        for archive_error,stop_error,save_error,expected in ((None,None,None,None),(None,RuntimeError('stop only'),None,'stop only'),(OSError('archive first'),RuntimeError('stop second'),None,'archive first'),(OSError('archive first'),RuntimeError('stop second'),OSError('receipt failed'),'archive first')):
            with self.subTest(expected=expected,write_failure=bool(save_error)):
                watchdog=Mock();watchdog.EkaStopWatchdog.return_value=True;watchdog.EkaStopWatchdog.side_effect=stop_error
                with patch.object(probe,'_execution_consumed',False),patch.object(probe,'_evidence_directory',self.out),patch.object(probe,'_owner_watchdog_started',True),patch.object(probe,'_owner_watchdog',watchdog),patch.object(probe,'qualify',return_value=report),patch.object(probe,'archive_evidence',side_effect=archive_error),patch.object(probe,'save',side_effect=save_error):
                    if expected:
                        with self.assertRaisesRegex((OSError,RuntimeError),expected):probe.execute(self.out)
                    else:self.assertIs(probe.execute(self.out),report)
                watchdog.EkaStopWatchdog.assert_called_once()

if __name__=='__main__':unittest.main(verbosity=2)
