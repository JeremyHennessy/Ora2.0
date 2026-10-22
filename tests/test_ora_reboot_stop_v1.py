import json
from pathlib import Path
import sys,tempfile,threading,time,unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.ora_native_slice_v1 import run_slice,Limits
from experiments.ora_owned_ollama_v1 import OwnedOllama
from experiments.ora_controller_v1 import controller
from experiments.ora_mailbox_v1 import publish,Busy
import sqlite3
from contextlib import closing

class RebootStop(unittest.TestCase):
    def test_uninitialized_mailbox_is_busy_without_publishing(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with closing(sqlite3.connect(root/'memory.sqlite3')) as db:
                db.execute('create table meta(submitted integer)');db.commit()
            with self.assertRaises(Busy):publish(root,lambda n:{})
            self.assertFalse((root/'inbox.json').exists())

    def test_model_start_failure_holds_without_retry_and_refuses_relaunch(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch('experiments.ora_controller_v1.boot_token',return_value='fixture'),patch(
                'experiments.ora_controller_v1.OwnedOllama',side_effect=RuntimeError('model fixture')) as model:
                state=controller(root,seconds=160,epoch_seconds=10,practice=0)
                self.assertEqual(state['failures'],1)
                self.assertEqual(state['reason'],'controller-safety-hold')
                self.assertEqual(model.call_count,1)
                with self.assertRaisesRegex(RuntimeError,'Saved controller safety hold'):controller(root)
                self.assertEqual(model.call_count,1)

    def test_native_stop_allows_acknowledgement_and_still_kills_stubborn_child(self):
        for cooperative in (True,False):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);stop=root/'STOP'
                code=('import pathlib,time; p=pathlib.Path('+repr(str(stop))+'); '
                      '\nwhile not p.exists(): time.sleep(.01)\nprint("acknowledged")' if cooperative else 'import time;time.sleep(10)')
                timer=threading.Timer(.3,stop.touch);timer.start()
                result=run_slice(lambda *a:[sys.executable,'-B','-c',code],root,
                    Limits(memory_bytes=128*1024**2,cpu_seconds=2,processes=2,wall_seconds=4),
                    stop_path=stop,stop_grace_seconds=.5)
                timer.join()
                self.assertTrue(result['post_close_processes_exited'])
                self.assertEqual(result['usage']['active_before_close'],0)
                self.assertEqual(result['reason'],'exit' if cooperative else 'operator-stop')
                if cooperative:self.assertIn('acknowledged',result['output'])

    def test_prepare_stop_interrupts_request_without_waiting_for_http_timeout(self):
        with tempfile.TemporaryDirectory() as folder:
            model=OwnedOllama(folder,0);model.path.mkdir()
            def request(*a,**kw):
                until=time.monotonic()+3
                while not (model.path/'STOP').exists() and time.monotonic()<until:time.sleep(.01)
                raise ConnectionError('server stopped')
            (model.root/'STOP').touch()
            with patch('experiments.ora_owned_ollama_v1.verify_owner'),patch('experiments.ora_owned_ollama_v1.request',side_effect=request):
                started=time.monotonic()
                with self.assertRaises(InterruptedError):model.prepare()
                self.assertLess(time.monotonic()-started,1)

    def test_request_error_not_masked_by_close_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            model=OwnedOllama(folder,0);model.path.mkdir()
            with patch.object(model,'close',side_effect=RuntimeError('closure failed')):
                with self.assertRaises(BaseExceptionGroup) as errors:
                    model.__exit__(TimeoutError,TimeoutError('request timed out'),None)
            self.assertEqual([str(e) for e in errors.exception.exceptions],['request timed out','closure failed'])
            self.assertEqual(json.loads((model.path/'lifecycle-error.json').read_text())['type'],'TimeoutError')

if __name__=='__main__':unittest.main()
