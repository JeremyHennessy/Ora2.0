"""Readiness deadline and evidence tests; no server or model launched."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from experiments.ora_owned_ollama_v1 import OwnedOllama

class Ready(unittest.TestCase):
 def run_case(self,request,listener=12,stop=False,alive=True):
  clock=[0.0]
  with tempfile.TemporaryDirectory() as directory:
   server=OwnedOllama(directory,0);server.path.mkdir();server.start={'pid':12,'creation_filetime_decimal':'123'};server.thread=Mock();server.thread.is_alive.return_value=alive
   if stop:(Path(directory)/'STOP').touch()
   def sleep(n):clock[0]+=n
   def probe(*a,**kw):return request(clock,kw)
   with patch('experiments.ora_owned_ollama_v1.time.monotonic',side_effect=lambda:clock[0]),patch('experiments.ora_owned_ollama_v1.time.sleep',side_effect=sleep),patch('experiments.ora_owned_ollama_v1.listener_pid',return_value=listener),patch('experiments.ora_owned_ollama_v1.request',side_effect=probe) as req:
    error=None
    try:server.wait_ready()
    except BaseException as exc:error=exc
   return json.loads((server.path/'readiness.json').read_text()),error,req.call_count
 def test_success_receipt(self):
  r,e,n=self.run_case(lambda c,k:{'version':'fixture'});self.assertIsNone(e);self.assertTrue(r['ready']);self.assertEqual(n,1)
 def test_socket_timeout_retained_bounded(self):
  timeouts=[]
  def fail(c,k):
   timeouts.append(k['timeout']);c[0]+=k['timeout'];raise TimeoutError('fixture timeout')
  r,e,n=self.run_case(fail);self.assertIsInstance(e,TimeoutError);self.assertFalse(r['ready']);self.assertLessEqual(r['elapsed_seconds'],20.0001);self.assertLessEqual(len(r['recent']),8);self.assertIn('fixture timeout',str(r));self.assertLess(timeouts[-1],3)
 def test_wrong_listener_never_probed(self):
  r,e,n=self.run_case(lambda c,k:None,listener=99);self.assertIsInstance(e,TimeoutError);self.assertEqual(n,0);self.assertEqual(r['listener_matches'],0)
 def test_stop_and_dead_worker_not_retried(self):
  for options,kind in [({'stop':True},InterruptedError),({'alive':False},RuntimeError)]:
   r,e,n=self.run_case(lambda c,k:None,**options);self.assertIsInstance(e,kind);self.assertEqual(n,0);self.assertIn('error',r)
 def test_late_success_rejected(self):
  def late(c,k):c[0]=21;return {}
  r,e,n=self.run_case(late);self.assertIsInstance(e,TimeoutError);self.assertFalse(r['ready'])
 def test_malformed_response_not_retried(self):
  def malformed(c,k):raise ValueError('invalid response')
  r,e,n=self.run_case(malformed);self.assertIsInstance(e,ValueError);self.assertEqual(n,1);self.assertIn('invalid response',r['error'])
if __name__=='__main__':unittest.main()
