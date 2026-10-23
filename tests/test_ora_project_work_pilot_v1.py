import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.ora_project_work_pilot_v1 import *
class Pilot(unittest.TestCase):
    def test_boundary_oracle(self):
        self.assertEqual(oracle((120,16384,'60s')),'ACCEPT');self.assertEqual(oracle((120,16385,'60s')),'REJECT')
        for x in [(119,1,'60s'),(120,1,'30s')]:self.assertEqual(oracle(x),'REJECT')
        with self.assertRaises(ValueError):oracle((120,-1,'60s'))
    def test_no_overlap_balanced_reserve(self):
        self.assertFalse(set(TRAIN)&set(TEST));self.assertEqual(sum(oracle(x)=='ACCEPT' for x in TEST),4)
    def test_disruption_preserves_own_scores_but_changes_association(self):
        h=[[x,'ACCEPT',i==0] for i,x in enumerate(TRAIN)];d=visible_history('disrupted-history',h)
        self.assertEqual([x[1:] for x in h],[x[1:] for x in d]);self.assertTrue(all(a[0]!=b[0] for a,b in zip(h,d)));self.assertEqual(visible_history('no-history',h),[])
    def test_context_and_call_caps(self):
        h=[[list(x),'INVALID',False] for x in TRAIN]
        for a in ARMS:
            for c in TRAIN+TEST:self.assertLessEqual(len(question(c,visible_history(a,h)).encode()),512)
        self.assertEqual((len(TRAIN)+len(TEST))*len(ARMS),36)
    def test_invalid_output_cannot_count(self):
        for s in ['ACCEPT','{"answer":"ACCEPT","cite":"M1"}','{"answer":"ACCEPT","cite":"D1","command":"delete"}']:
            self.assertEqual(response({'answer':s}),'INVALID')
    def test_runtime_failure_seals_no_retry(self):
        import tempfile
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as d:
            client=Mock()
            with self.assertRaises(RuntimeError):execute(registration('a'*64),client,d,Mock(side_effect=RuntimeError('hold')))
            self.assertTrue((Path(d)/'failure.json').exists());client.ask.assert_not_called()
            with self.assertRaises(ValueError):execute(registration('a'*64),client,d,lambda:None)
if __name__=='__main__':unittest.main()
