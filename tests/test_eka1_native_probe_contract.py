"""Offline refusal/archive tests only. OS fixtures have a separate finite entry."""
import json
import ast
from types import SimpleNamespace
import ctypes
import copy
import contextlib
import io
import os
import runpy
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
        # Explicit offline fixture only; production admission remains held.
        self.admission=patch.object(probe,'native_admission');self.admission.start()
    def tearDown(self):
        self.admission.stop();self.custody.stop();self.property.stop();self.ledger.close();os.close(self.fd);self.tmp.cleanup()
    def test_wrong_owner_before_kernel_or_files(self):
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaises(TypeError):probe.launch(None,None,3,object(),'x',0)
    def test_compiler_quotes_are_script_bytes_not_escaped_argv(self):
        setup=Path('C:/Program Files/VS/vcvars64.bat');line='"C:/Program Files/VS/cl.exe" /W4 /WX fixed.c'
        link_line='"C:/Program Files/VS/link.exe" fixed.obj /OUT:fixed.exe'
        command=probe.compiler_command(self.out,'fixture',setup,line,link_line)
        self.assertEqual(command[1:3],['/d','/c']);self.assertNotIn('"',command[-1]);self.assertNotIn('\\"',command[-1])
        raw=(self.out/'build-fixture.cmd').read_bytes()
        self.assertIn(('call "'+str(setup)+'"').encode(),raw);self.assertIn(line.encode(),raw)
        self.assertLess(raw.index(b'set "VSCMD_SKIP_SENDTELEMETRY=1"'),raw.index(b'call "'))
        self.assertNotIn(b'\\"',raw)
        self.assertLess(raw.index(b'if errorlevel 1 exit /b %errorlevel%'),raw.index(line.encode()))
        self.assertLess(raw.index(line.encode()),raw.rindex(b'if errorlevel 1 exit /b %errorlevel%'))
        self.assertLess(raw.rindex(b'if errorlevel 1 exit /b %errorlevel%'),raw.index(link_line.encode()))
        self.assertEqual(json.loads((self.out/'compiler-script-fixture.json').read_text())['script_sha256'],probe.sha(raw))
        with self.assertRaises(FileExistsError):probe.compiler_command(self.out,'fixture',setup,line,link_line)
    def test_compiler_script_unsafe_path_refused_before_write(self):
        with self.assertRaisesRegex(ValueError,'no whitespace'):probe.compiler_command(self.out/'space dir','fixture',Path('setup.bat'),'fixed','fixed-link')
        self.assertFalse((self.out/'space dir').exists())
    def test_bool_and_unlisted_case_rejected_before_effect(self):
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaises(ValueError):probe.launch(None,None,True,self.owner,'x',0)
            for mode in (-1,9,1.0):
                with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.launch(None,None,mode,self.owner,'x',0)
    def test_failed_slot_is_never_refunded(self):
        with patch.object(probe,'_launch',side_effect=OSError('synthetic start failure')) as invoke:
            with self.assertRaises(OSError):probe.launch(None,self.out,3,self.owner,self.owner._assignment,0)
            with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.launch(None,self.out,1,self.owner,self.owner._assignment,0)
            self.assertEqual(invoke.call_count,1)
            self.assertEqual(self.ledger._births,36);self.assertTrue(self.owner._closed);self.assertIn('synthetic start failure',self.owner._failed)
    def test_wrong_assignment_rejected_before_kernel(self):
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaisesRegex(ValueError,'Assignment'):probe.launch(self.out/'eka1_probe_guardian.exe',self.out,3,self.owner,'wrong',0)
    def test_resealed_alternate_limits_and_owner_refused(self):
        for field,value in (('raw_bytes_per_case',65537),('owner_birth',[1,1]),('scientific_admission',True)):
            registration=probe.registration_for({},0);registration[field]=value
            raw=probe.owner_source.canonical(registration);(self.out/'registration.json').write_bytes(raw);self.owner._assignment=probe.sha(raw)
            with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
                with self.assertRaisesRegex(ValueError,'registered synthetic'):probe.verify_reservations(self.owner,self.out,self.owner._assignment)
    def test_changed_source_refused_before_kernel(self):
        with patch.object(probe,'custody',return_value={'changed':'source'}),patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaisesRegex(ValueError,'Source/dependency'):probe.launch(None,self.out,3,self.owner,self.owner._assignment,0)
    def test_changed_binary_rejected_before_kernel(self):
        seal=self.owner._assignment
        exe=self.out/'eka1_probe_guardian.exe';exe.write_bytes(b'unreviewed')
        (self.out/'binary-custody.json').write_text(json.dumps({'artifact_sha256':'0'*64}))
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaisesRegex(ValueError,'compiled guardian'):probe.launch(exe,self.out,3,self.owner,seal,0)
    def test_empty_ledger_cannot_build_or_launch(self):
        self.ledger._births=0
        with patch.object(probe,'kernel',side_effect=AssertionError('OS effect')):
            with self.assertRaisesRegex(ValueError,'36-birth'):probe.build(self.out,self.owner,{},self.owner._assignment,0)
            with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.launch(None,self.out,3,self.owner,self.owner._assignment,0)
    def test_unexpected_native_result_terminally_closes_owner(self):
        result={'guardian_exit':125,'inner':None}
        with patch.object(probe,'_launch',return_value=result) as invoke:
            with self.assertRaisesRegex(ValueError,'closure/capture'):probe.launch(None,self.out,3,self.owner,self.owner._assignment,0)
            with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.launch(None,self.out,1,self.owner,self.owner._assignment,0)
        self.assertEqual(invoke.call_count,1);self.assertEqual(self.ledger._births,36)
    def test_failed_build_cannot_reuse_owner(self):
        with patch.object(probe,'_build',side_effect=OSError('compiler failure')) as invoke:
            with self.assertRaisesRegex(OSError,'compiler failure'):probe.build(self.out,self.owner,{},self.owner._assignment,0)
            with self.assertRaisesRegex(RuntimeError,'closed/incomplete'):probe.build(self.out,self.owner,{},self.owner._assignment,0)
        self.assertEqual(invoke.call_count,1);self.assertTrue(self.owner._closed);self.assertEqual(self.ledger._births,36)
    def tree_script(self,wait_result=0,deny=True,handle_pid=101,live=True):
        events=[];kernel=Mock();kernel.CloseHandle.return_value=True
        kernel.GetProcessId.return_value=handle_pid
        def times(handle,created,*unused):
            ctypes.cast(created,ctypes.POINTER(ctypes.c_ulonglong)).contents.value=999
            return True
        kernel.GetProcessTimes.side_effect=times
        def wait(handle,milliseconds):
            if handle==456:return 258 if live else 0
            events.append('birth_handshake');return wait_result
        kernel.WaitForSingleObject.side_effect=wait
        def spawn(*args,**kwargs):
            events.append('spawn')
            if events.count('spawn')==2 and deny:
                error=OSError('quota refused');error.winerror=1816;raise error
            return Mock(pid=101,_handle=456)
        output=io.StringIO()
        def write(fd,raw):output.write(raw.decode('ascii'));return len(raw)
        with patch.object(sys,'argv',['fixture','6','unused','123']),patch('ctypes.WinDLL',return_value=kernel),patch('subprocess.Popen',side_effect=spawn),patch('msvcrt.setmode'),patch('os.write',side_effect=write),contextlib.redirect_stdout(output):
            runpy.run_path(str(ROOT/'tools/eka1_probe_child.py'),run_name='__main__')
        return events,output.getvalue()
    def test_tree_child_waits_for_birth_before_second_attempt(self):
        events,output=self.tree_script()
        self.assertEqual(events,['spawn','birth_handshake','spawn'])
        self.assertIn('EKA_DESCENDANT_CREATED 101 999\n',output);self.assertIn('EKA_PROCESS_CAP_REFUSED 1816',output)
    def test_tree_handshake_timeout_blocks_second_attempt(self):
        with self.assertRaisesRegex(OSError,'handshake absent'):self.tree_script(wait_result=258)
    def test_tree_retained_handle_mismatch_refused_before_gate(self):
        with self.assertRaisesRegex(OSError,'handle PID differs'):self.tree_script(handle_pid=102)
    def test_tree_exited_birth_refused_before_gate(self):
        with self.assertRaisesRegex(OSError,'not live'):self.tree_script(live=False)
    def test_tree_unexpected_second_success_is_failure(self):
        with self.assertRaisesRegex(RuntimeError,'unexpectedly admitted'):self.tree_script(deny=False)
    def test_tree_receipt_requires_successful_descendant_identity(self):
        raw=self.out/'6.raw';raw.write_bytes(b'EKA_DESCENDANT_CREATED 101 999\nEKA_DESCENDANT_SELF 101 999\nEKA_PROCESS_CAP_REFUSED 1816\n')
        result={'guardian_exit':0,'root_empty':True,'usage':{'started_processes':4},'inner':{'error':0,'eof':True,'active':0,'process_cap':2,'started_processes':3,'desc_signaled':True,'desc_pid':101,'desc_birth':'999'},'descendant_records':[{'schema':'EKA-DESCENDANT-BOUND-v1','pid':101,'birth':'999','live':True,'private_job':True,'root_job':True,'self_ready':True,'tick':20},{'schema':'EKA-DESCENDANT-GATE-v1','pid':101,'birth':'999','tick':21}]}
        probe.accept_case(result,self.out,6)
        mutations=[lambda r:r['inner'].update(desc_pid=999),lambda r:r['inner'].update(desc_birth='998'),lambda r:r.update(descendant_records=[]),lambda r:r['descendant_records'].reverse(),lambda r:r['descendant_records'][1].update(tick=19)]
        mutations += [lambda r,flag=flag:r['descendant_records'][0].update({flag:False}) for flag in ('live','private_job','root_job','self_ready')]
        for mutate in mutations:
            altered=copy.deepcopy(result);mutate(altered)
            with self.subTest(altered=altered),self.assertRaisesRegex(ValueError,'containment'):probe.accept_case(altered,self.out,6)
        original=raw.read_bytes()
        for broken in (original.replace(b'EKA_DESCENDANT_SELF 101 999\n',b''),original.replace(b'SELF 101 999',b'SELF 101 998'),original+ b'EKA_DESCENDANT_SELF 101 999\n'):
            raw.write_bytes(broken)
            with self.assertRaisesRegex(ValueError,'containment'):probe.accept_case(result,self.out,6)
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

class PreResumeRootSourceChecks(unittest.TestCase):
    """Execute extracted Python guards with fake APIs; inspect C, never load it."""
    def source_function(self):
        tree=ast.parse((ROOT/'tools/eka1_native_probe.py').read_text())
        return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_launch')
    @staticmethod
    def run_nodes(nodes,env):
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'source_guard_fixture','exec'),env)
    @staticmethod
    def check(ok):
        if not ok:raise OSError('fake API refusal')
    def test_root_readback_false_or_error_never_reaches_resume(self):
        fn=self.source_function()
        attempt=next(n for n in ast.walk(fn) if isinstance(n,ast.Try) and any(isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='root_member' for t in s.targets) for s in n.body))
        start=next(i for i,s in enumerate(attempt.body) if isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='root_member' for t in s.targets))
        guard=attempt.body[start:start+4]
        self.assertEqual(ast.unparse(guard[-1]),'root_verified = True')
        for api_ok,member in ((0,False),(0,True),(1,False),(1,True)):
            with self.subTest(api_ok=api_ok,member=member):
                def query(process,job,result):
                    self.assertEqual((process,job),(123,456));result._obj.value=member;return api_ok
                resume=Mock();env=dict(wt=probe.wt,ctypes=ctypes,k=SimpleNamespace(IsProcessInJob=query),pi=SimpleNamespace(process=123),job=SimpleNamespace(handle=456),checked=self.check,root_verified=False,resume=resume)
                nodes=guard+ast.parse('resume()').body
                if api_ok and member:self.run_nodes(nodes,env)
                else:
                    with self.assertRaises((OSError,RuntimeError)):self.run_nodes(nodes,env)
                self.assertEqual(env['root_verified'],bool(api_ok and member));self.assertEqual(resume.call_count,int(bool(api_ok and member)))
        calls=[(n.lineno,ast.unparse(n.func)) for n in ast.walk(fn) if isinstance(n,ast.Call)]
        rootline=next(line for line,name in calls if name=='k.IsProcessInJob')
        self.assertLess(rootline,next(line for line,name in calls if name=='k.ResumeThread'))
    def test_unverified_creation_closes_by_owned_handle_without_extending_deadline(self):
        fn=self.source_function();expected=ast.dump(ast.parse('created and pi.process and not root_verified',mode='eval').body)
        node=next(n for n in ast.walk(fn) if isinstance(n,ast.If) and ast.dump(n.test)==expected)
        for initial_wait,terminate_ok,final_wait,now in ((0,1,0,100),(258,1,0,100),(258,0,0,100),(258,0,258,100),(258,1,258,100),(258,1,258,600)):
            with self.subTest(initial_wait=initial_wait,terminate_ok=terminate_ok,final_wait=final_wait,now=now):
                wait=Mock(side_effect=[initial_wait,final_wait]);terminate=Mock(return_value=terminate_ok);failures=[]
                env=dict(created=True,pi=SimpleNamespace(process=123),root_verified=False,k=SimpleNamespace(WaitForSingleObject=wait,TerminateProcess=terminate,GetTickCount64=lambda:now),end=500,checked=self.check,failures=failures)
                self.run_nodes([node],env)
                if initial_wait==0:terminate.assert_not_called();self.assertEqual(failures,[])
                else:
                    terminate.assert_called_once_with(123,125)
                    self.assertEqual(wait.call_args.args,(123,max(0,500-now)))
                    self.assertEqual(wait.call_count,2)
                    self.assertEqual(bool(failures),not terminate_ok or final_wait!=0)
        env=dict(created=True,pi=SimpleNamespace(process=123),root_verified=True,k=Mock(),end=500,checked=self.check,failures=[])
        self.run_nodes([node],env);self.assertEqual(env['k'].mock_calls,[])
        env.update(created=False,root_verified=False);self.run_nodes([node],env);self.assertEqual(env['k'].mock_calls,[])
        text=(ROOT/'tools/eka1_native_probe.py').read_text();self.assertLess(node.lineno,next(n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and ast.unparse(n.func)=='settle_root'))
        self.assertIn("'TerminateProcess':([wt.HANDLE,wt.UINT],wt.BOOL)",text)
    def test_c_guard_and_owned_cleanup_source_order_only(self):
        text=(ROOT/'experiments/native/eka1_probe_guardian.c').read_text()
        guard='if(!IsProcessInJob(pi.hProcess,root,&member)||!member){error=48;goto close;}'
        self.assertIn(guard,text);self.assertLess(text.index(guard),text.index('ResumeThread(pi.hThread)'))
        self.assertLess(text.index(guard),text.index('root_member_verified_before_resume'))
        close=text[text.index('\nclose:'):]
        self.assertIn('created&&pi.hProcess&&!root_verified',close);self.assertIn('TerminateProcess(pi.hProcess,125)',close)
        self.assertIn('now<close_end?(DWORD)(close_end-now):0',close)
        self.assertLess(close.index('TerminateProcess(pi.hProcess,125)'),close.index('CloseHandle(pi.hProcess)'))
        self.assertIn('root_verified=FALSE',text)

class NoBreakawayReadbackChecks(unittest.TestCase):
    """Exercise the real constructor with DATA fake APIs; no Windows Job exists."""
    def construct(self, extra=0, missing=0, close_ok=True):
        from experiments import process_limits as resource
        class KernelData:
            def __init__(self):self.closed=[];self.setting=None
            def CreateJobObjectW(self,unused,name):return 99
            def SetInformationJobObject(self,handle,kind,value,size):
                if kind==9:self.setting=value._obj
                return 1
            def QueryInformationJobObject(self,handle,kind,value,size,unused):
                if kind==9:
                    observed=value._obj
                    observed.basic.flags=(self.setting.basic.flags|extra)&~missing
                    observed.basic.job_cpu=self.setting.basic.job_cpu
                    observed.basic.active_processes=self.setting.basic.active_processes
                    observed.job_memory=self.setting.job_memory
                return 1
            def CloseHandle(self,handle):self.closed.append(handle);return int(close_ok)
        data=KernelData()
        def check(ok):
            if not ok:raise OSError('offline API failure')
        with patch.object(resource,'kernel',return_value=data),patch.object(resource,'checked',side_effect=check):
            try:job=resource.Job(resource.Limits())
            except BaseException:
                self.assertEqual(data.closed,[99])
                raise
        return job,data

    def test_required_flags_without_breakaway_are_accepted(self):
        job,data=self.construct()
        self.assertEqual(data.setting.basic.flags,0x4|0x8|0x200|0x2000)
        job.close();self.assertEqual(data.closed,[99])

    def test_either_breakaway_flag_refuses_and_closes_before_return(self):
        for flags in (0x800,0x1000,0x1800):
            with self.subTest(flags=flags):
                with self.assertRaisesRegex(RuntimeError,'readback differs'):
                    job,data=self.construct(extra=flags)
                    job.close()  # DATA fake cleanup if old predicate accepts.

    def test_each_required_flag_still_must_be_present(self):
        for flag in (0x4,0x8,0x200,0x2000):
            with self.subTest(flag=flag):
                with self.assertRaisesRegex(RuntimeError,'readback differs'):
                    self.construct(missing=flag)

    def test_setup_rejection_remains_primary_when_close_fails(self):
        with self.assertRaisesRegex(RuntimeError,'readback differs') as caught:
            self.construct(extra=0x800,close_ok=False)
        notes='\n'.join(caught.exception.__notes__)
        self.assertIn('Job setup cleanup UNKNOWN',notes)
        self.assertIn("OSError('offline API failure')",notes)
        self.assertIn('handle=99',notes)

class UnexpectedOutputContractTests(unittest.TestCase):
    def test_normal_success_requires_exact_zero_exit_and_reason(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'0.raw').write_bytes(b'EKA_SYNTHETIC_OK')
            value=dict(guardian_exit=0,root_empty=True,inner=dict(error=0,eof=True,active=0,overflow=False,reason=0,exit_code=0))
            probe.accept_case(value,out,0)
    def test_normal_rejects_boolean_and_missing_exit_or_reason(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'0.raw').write_bytes(b'EKA_SYNTHETIC_OK')
            for field in ('exit_code','reason'):
                for bad in (False,True,None):
                    inner=dict(error=0,eof=True,active=0,overflow=False,reason=0,exit_code=0)
                    if bad is None:del inner[field]
                    else:inner[field]=bad
                    with self.subTest(field=field,bad=bad):
                        with self.assertRaisesRegex(ValueError,'Normal fixture'):
                            probe.accept_case(dict(guardian_exit=0,root_empty=True,inner=inner),out,0)

    def test_normal_token_does_not_excuse_failed_exit_or_termination(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'0.raw').write_bytes(b'EKA_SYNTHETIC_OK')
            for exit_code,reason in ((9,0),(0,1),(0,3),(0,4)):
                value=dict(guardian_exit=0,root_empty=True,inner=dict(error=0,eof=True,active=0,overflow=False,reason=reason,exit_code=exit_code))
                with self.subTest(exit_code=exit_code,reason=reason):
                    with self.assertRaisesRegex(ValueError,'Normal fixture'):probe.accept_case(value,out,0)
    def test_normal_case_rejects_unexpected_output_termination(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'0.raw').write_bytes(b'EKA_SYNTHETIC_OK')
            for overflow,reason in ((True,2),(True,0),(False,2)):
                value=dict(guardian_exit=0,root_empty=True,inner=dict(error=0,eof=True,active=0,overflow=overflow,reason=reason))
                with self.subTest(overflow=overflow,reason=reason):
                    with self.assertRaisesRegex(ValueError,'Unexpected output'):probe.accept_case(value,out,0)
    def test_declared_output_fixture_still_accepts_observed_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'5.raw').write_bytes(b'x'*65536)
            value=dict(guardian_exit=0,root_empty=True,raw_bytes=65536,inner=dict(error=0,eof=True,active=0,overflow=True,reason=2))
            probe.accept_case(value,out,5)
            for reason in (0, 1, 3, 4, None):
                with self.subTest(reason=reason):
                    value['inner']['reason'] = reason
                    with self.assertRaisesRegex(ValueError, 'Output limit not observed'):
                        probe.accept_case(value, out, 5)

class JobCloseNoRetryTests(unittest.TestCase):
    def test_failed_close_is_not_reissued(self):
        from experiments import process_limits as resource
        job=resource.Job.__new__(resource.Job);job.handle=99
        kernel=SimpleNamespace(CloseHandle=Mock(side_effect=[False,True]));job.k=kernel
        def checked(value):
            if not value:raise OSError('synthetic close failure')
            return value
        with patch.object(resource,'checked',checked):
            with self.assertRaisesRegex(OSError,'synthetic close failure'):job.close()
            with self.assertRaisesRegex(OSError,'no retry'):job.close()
        self.assertEqual(kernel.CloseHandle.call_count,1)
        self.assertEqual(job.handle,99)
    def test_successful_close_remains_idempotent(self):
        from experiments import process_limits as resource
        job=resource.Job.__new__(resource.Job);job.handle=99
        job.k=SimpleNamespace(CloseHandle=Mock(return_value=True))
        with patch.object(resource,'checked',lambda value:value):job.close();job.close()
        self.assertEqual(job.k.CloseHandle.call_count,1);self.assertIsNone(job.handle)

class ReaderFailureContractTests(unittest.TestCase):
    def exercise(self, fail):
        tree=ast.parse((ROOT/'experiments/process_limits.py').read_bytes())
        run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        drain=next(n for n in run.body if isinstance(n,ast.FunctionDef) and n.name=='drain')
        guard=next(n for n in ast.walk(run) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='reader_errors')
        failure=OSError('synthetic reader failure')
        stream=Mock();stream.read.side_effect=[b'abcdefgh',failure if fail else b'']
        ns=dict(process=SimpleNamespace(stdout=stream),kept=bytearray(),counts={'bytes':0},reader_errors=[],OUTPUT_LIMIT=3)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[drain],type_ignores=[])),'drain','exec'),ns)
        import threading
        reader=threading.Thread(target=ns['drain']);reader.start();reader.join(timeout=2)
        self.assertFalse(reader.is_alive())
        self.assertEqual(ns['counts']['bytes'],8);self.assertEqual(ns['kept'],b'abc')
        code=compile(ast.fix_missing_locations(ast.Module(body=[guard],type_ignores=[])),'reader guard','exec')
        if fail:
            with self.assertRaises(OSError) as caught:exec(code,ns)
            self.assertIs(caught.exception,failure)
            self.assertEqual(failure.output_bytes,8);self.assertEqual(failure.retained_output,b'abc')
            self.assertIn('EOF unverified',' '.join(failure.__notes__))
        else:
            exec(code,ns);self.assertEqual(ns['reader_errors'],[])
        self.assertEqual(stream.read.call_count,2)
    def test_partial_read_failure_rejects_capture(self):self.exercise(True)
    def test_clean_eof_preserves_raw_and_retained_counts(self):self.exercise(False)

class ReaderCleanupFirstCauseTests(unittest.TestCase):
    def exercise(self, reader_failed):
        import sys
        tree=ast.parse((ROOT/'experiments/process_limits.py').read_bytes())
        run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        outer=next(n for n in run.body if isinstance(n,ast.Try))
        guard=next(n for n in ast.walk(run) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='reader_errors')
        calls=[]
        read_error=OSError('synthetic read failure')
        job_error=OSError('synthetic job close failure')
        errors=dict(job=job_error,terminate=OSError('synthetic terminate failure'),
                    reader=OSError('synthetic reader join failure'),stdout=OSError('synthetic stdout close failure'))
        def action(name):
            calls.append(name)
            if name in errors:raise errors[name]
        process=SimpleNamespace(poll=lambda:None,terminate=lambda:action('terminate'),
                                wait=lambda **kw:action('wait'),
                                stdin=SimpleNamespace(close=lambda:action('stdin')),
                                stdout=SimpleNamespace(close=lambda:action('stdout')))
        ns=dict(sys=sys,reader_errors=[read_error] if reader_failed else [],
                counts={'bytes':8},kept=bytearray(b'abc'),process=process,
                job=SimpleNamespace(close=lambda:action('job')),
                reader=SimpleNamespace(join=lambda **kw:action('reader')))
        node=ast.Try(body=[guard],handlers=[],orelse=[],finalbody=outer.finalbody)
        code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'actual reader guard and cleanup','exec')
        with self.assertRaises(OSError) as caught:exec(code,ns)
        primary=read_error if reader_failed else job_error
        self.assertIs(caught.exception,primary)
        self.assertEqual(calls,['job','terminate','reader','stdin','stdout'])
        notes='\n'.join(primary.__notes__)
        for error in errors.values():self.assertIn(repr(error),notes)
        self.assertIn('Cleanup UNKNOWN; no retry',notes)
        if reader_failed:
            self.assertEqual(read_error.output_bytes,8)
            self.assertEqual(read_error.retained_output,b'abc')
            self.assertIn('EOF unverified',notes)
    def test_reader_primary_survives_multiple_cleanup_failures(self):self.exercise(True)
    def test_cleanup_only_raises_first_and_attempts_remaining_closes(self):self.exercise(False)

if __name__=='__main__':unittest.main(verbosity=2)
