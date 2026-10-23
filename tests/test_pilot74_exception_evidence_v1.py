"""New synthetic same-handle observation tests;zero native launches or Worlds."""
import sys,unittest,os
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.digital_pilot74_guardian_v1 import failure_observation,attach_failure_evidence
from experiments import digital_pilot74_guardian_v1 as guardian
class Evidence(unittest.TestCase):
    def test_termination_is_not_closure(self):
        job=Mock();job.usage.return_value={'active_before_close':1};job.pids.return_value=[123]
        k=Mock();k.WaitForSingleObject.return_value=258
        v=failure_observation(job,k,999,123,456,'wait')
        self.assertFalse(v['closure_observed']);self.assertEqual(v['creation_filetime_decimal'],'456');k.WaitForSingleObject.assert_called_once_with(999,0)
    def test_unavailable_facts_preserved_as_unknown(self):
        job=Mock();job.usage.side_effect=OSError('query');job.pids.side_effect=OSError('enumeration')
        v=failure_observation(job,Mock(),None,0,None,'create')
        self.assertIsNone(v['usage']);self.assertIsNone(v['pid']);self.assertFalse(v['closure_observed']);self.assertEqual(len(v['observation_errors']),2)
    def test_observed_closure_requires_signaled_handle_and_zero_job(self):
        job=Mock();job.usage.return_value={'active_before_close':0};job.pids.return_value=[]
        k=Mock();k.WaitForSingleObject.return_value=0
        self.assertTrue(failure_observation(job,k,1,123,456,'wait')['closure_observed'])
    def test_first_exception_identity_and_snapshot_are_preserved(self):
        error=ValueError('original');body={'first_exception':repr(error),'cleanup_errors':[]};attach_failure_evidence(error,body);body['cleanup_errors'].append('later')
        self.assertEqual(str(error),'original');self.assertEqual(error.guardian_failure_evidence['cleanup_errors'],[])
    def test_inconsistent_or_malformed_observations_are_not_closure(self):
        for usage,pids in [({},[]),({'active_before_close':0},[123]),({'active_before_close':False},[])]:
            job=Mock();job.usage.return_value=usage;job.pids.return_value=pids;k=Mock();k.WaitForSingleObject.return_value=0
            self.assertFalse(failure_observation(job,k,1,123,456,'wait')['closure_observed'])
    @unittest.skipUnless(os.name=='nt','Windows stdlib handle setup;all kernel/process operations mocked')
    def test_launch_create_failure_and_cleanup_error_keep_first_exception(self):
        self.create_failure_case(False)
    @unittest.skipUnless(os.name=='nt','Windows stdlib handle setup;all kernel/process operations mocked')
    def test_diagnostic_and_cleanup_failure_cannot_skip_termination_or_replace_first(self):
        self.create_failure_case(True)
    def create_failure_case(self,diagnostic_failure):
        error=RuntimeError('synthetic create failure');k=Mock();k.SetHandleInformation.return_value=1
        def attributes(*args):args[-1]._obj.value=128;return 1
        k.InitializeProcThreadAttributeList.side_effect=attributes;k.UpdateProcThreadAttribute.return_value=1
        k.GetTickCount64.return_value=123;k.CreateProcessW.side_effect=error
        job=Mock();job.handle=12345;job.usage.return_value={'active_before_close':0};job.pids.return_value=[];job.close.side_effect=OSError('synthetic cleanup failure')
        r={'guardian':{'artifact':{'path':'synthetic.exe'}},'source_root':'synthetic'}
        observation=guardian.failure_observation
        with patch.object(guardian,'validate_host_registration',return_value=r),patch.object(guardian,'_kernel',return_value=k),patch('experiments.process_limits.Job',return_value=job),patch.object(guardian,'failure_observation',side_effect=RuntimeError('synthetic diagnostic failure') if diagnostic_failure else observation):
            with self.assertRaises(RuntimeError) as raised:guardian.launch_guardian({'path':'synthetic.json','extent':1,'sha256':'f'*64},'f'*64)
        self.assertIs(raised.exception,error);job.terminate.assert_called_once();k.CreateProcessW.assert_called_once()
        if diagnostic_failure:
            self.assertFalse(hasattr(error,'guardian_failure_evidence'));self.assertTrue(any('diagnostic unavailable' in n for n in error.__notes__));return
        e=error.guardian_failure_evidence
        self.assertEqual(e['before_termination']['phase'],'create');self.assertTrue(e['termination_requested']);self.assertFalse(e['after_termination']['closure_observed']);self.assertIn('synthetic cleanup failure',e['cleanup_errors'][0]);k.CreateProcessW.assert_called_once()
if __name__=='__main__':unittest.main()
