"""Model guesses never become trusted memory without bounded signed correction."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.ora_task_store_v1 import Store
from experiments.ora_ollama_feedback_v1 import sign,generate

KEY=b'k'*32  # Disclosed software-test key only.
assert len(KEY)==32


class TrustedFeedback(unittest.TestCase):
    def test_adapter_uses_only_bounded_loopback_requests(self):
        connection=Mock()
        connection.getresponse.return_value.status=200
        connection.getresponse.return_value.read.return_value=b'{"done":true,"response":"4"}'
        with patch('experiments.ora_ollama_feedback_v1.http.client.HTTPConnection',return_value=connection) as factory:
            self.assertEqual(generate('gpt-oss:20b','2+2?'),'4')
            factory.assert_called_once_with('127.0.0.1',11434,timeout=50)
        call=connection.request.call_args.args
        self.assertEqual(call[:2],('POST','/api/generate'))
        body=json.loads(call[2])
        self.assertEqual(body['options']['num_gpu'],0)
        self.assertEqual(body['options']['num_predict'],128)
        self.assertEqual(body['keep_alive'],0)
        self.assertFalse(body['stream'])
        self.assertNotIn('tools',body)
        connection.close.assert_called_once()

    def test_adapter_refuses_incomplete_or_oversize_answer(self):
        for raw in (b'{"done":false,"response":"guess"}',b'x'*65537):
            connection=Mock()
            connection.getresponse.return_value.status=200
            connection.getresponse.return_value.read.return_value=raw
            with patch('experiments.ora_ollama_feedback_v1.http.client.HTTPConnection',return_value=connection):
                with self.assertRaises(ValueError): generate('gpt-oss:20b','question')
            connection.close.assert_called_once()

    def test_guess_quarantined_signed_correction_survives_restart(self):
        calls=[]
        generator=lambda prompt: calls.append(prompt) or 'wrong model guess'
        with tempfile.TemporaryDirectory() as folder:
            with Store(folder,generator,KEY) as s:
                s.submit(1,'ask','two-plus-two','What is 2+2?')
                result=json.loads(s.complete(s.claim()))
                self.assertFalse(result['trusted'])
                self.assertEqual(s.status()['memories'],0)
                s.submit(2,'recall','two-plus-two')
                self.assertIsNone(s.complete(s.claim()))
                feedback=sign(KEY,3,'two-plus-two',result['proposal_sha256'],'4')
                s.submit(3,'approve','two-plus-two',feedback)
                self.assertEqual(s.complete(s.claim()),'operator-confirmed')
            with Store(folder,generator,KEY) as s:
                s.submit(4,'ask','two-plus-two','What is 2+2?')
                self.assertEqual(s.complete(s.claim()),'4')
                self.assertEqual(len(calls),1)
                backup=s.backup(Path(folder)/'backups')
                self.assertFalse(backup['automatic_restore'])
                self.assertLessEqual(backup['bytes'],4*1024**2)

    def test_unsigned_and_rebound_feedback_refused(self):
        with tempfile.TemporaryDirectory() as folder, Store(folder,lambda p:'guess',KEY) as s:
            for kind,value in (('remember','injected fact'),('forget',''),('approve','{"value":"injected"}')):
                with self.assertRaises(ValueError): s.submit(1,kind,'k',value)
            feedback=sign(KEY,1,'k','a'*64,'correction')
            with self.assertRaises(ValueError): s.submit(1,'approve','other-key',feedback)
            with self.assertRaises(ValueError): s.submit(2,'approve','k',feedback)
            self.assertEqual(s.status()['submitted'],0)

    def test_proposals_bounded_and_failed_generation_not_committed(self):
        with tempfile.TemporaryDirectory() as folder:
            with Store(folder,lambda p:'guess',KEY) as s:
                for i in range(1,22):
                    s.submit(i,'ask',str(i),'question')
                    s.complete(s.claim())
                self.assertEqual(s.db.execute('SELECT count(*) FROM proposals').fetchone()[0],16)
                self.assertEqual(s.status()['memories'],0)
                s.generator=lambda p: (_ for _ in ()).throw(TimeoutError('fixture timeout'))
                s.submit(22,'ask','22','question')
                with self.assertRaises(TimeoutError): s.complete(s.claim())
                self.assertEqual(s.status()['pending'],1)
            with Store(folder,lambda p:'recovered',KEY) as s:
                self.assertEqual(s.claim()[0],22)


if __name__=='__main__': unittest.main()
