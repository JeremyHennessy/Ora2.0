"""Mixed trusted program/operator sources with fake model; no real HTTP or Worlds."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from experiments.ora_task_store_v1 import Store,serve
from experiments.ora_mixed_stream_v1 import run_mix,read_one
from experiments.ora_mailbox_v1 import publish,Busy
from experiments.ora_ollama_feedback_v1 import sign


class MixedSource(unittest.TestCase):
    def test_real_exclusive_writer_read_retry_and_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with Store(root): pass
            writer=sqlite3.connect(root/'memory.sqlite3',check_same_thread=False)
            writer.execute('BEGIN EXCLUSIVE')
            released=threading.Event()
            def release():
                time.sleep(.5); writer.rollback(); writer.close(); released.set()
            thread=threading.Thread(target=release); thread.start()
            try:
                self.assertEqual(read_one(root,'SELECT submitted FROM meta',(),time.monotonic()+2),(0,))
            finally: thread.join(2)
            self.assertTrue(released.is_set())
            with closing(sqlite3.connect(root/'memory.sqlite3')) as db:
                db.execute('BEGIN EXCLUSIVE')
                with self.assertRaises(TimeoutError): read_one(root,'SELECT submitted FROM meta',(),time.monotonic()+.1)
                db.rollback()
            with self.assertRaises(sqlite3.OperationalError): read_one(root,'SELECT missing FROM meta',(),time.monotonic()+1)

    def test_all_three_lanes_preserve_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); key=b't'*32
            (root/'feedback.key').write_bytes(key)
            (root/'ollama.json').write_text('{"model":"gpt-oss:20b"}')
            ready=threading.Event(); failures=[]
            def worker():
                try:
                    with Store(root,lambda prompt:'untrusted proposed answer',key) as store:
                        ready.set(); serve(store,root/'STOP',seconds=15,max_tasks=50,inbox=root/'inbox.json')
                except BaseException as error: failures.append(error); ready.set()
            thread=threading.Thread(target=worker,daemon=True); thread.start()
            try:
                self.assertTrue(ready.wait(3))
                result=run_mix(root,['experiments/ora_ollama_prepare_v1.py'],seconds=10,practice=2)
                self.assertEqual(result['verified_arithmetic'],2)
                self.assertEqual(len(result['project_reviews_awaiting_operator']),1)
                project=result['project_reviews_awaiting_operator'][0]
                repeated=run_mix(root,['experiments/ora_ollama_prepare_v1.py'],seconds=3,practice=0)
                self.assertEqual(repeated['published_tasks'],0)
                self.assertEqual(repeated['project_reviews_awaiting_operator'][0]['proposal_sha256'],project['proposal_sha256'])
                next_batch=run_mix(root,seconds=3,practice=1,offset=2)
                self.assertEqual(next_batch['verified_arithmetic'],1)
                with closing(sqlite3.connect(root/'memory.sqlite3')) as db:
                    self.assertEqual(db.execute('SELECT count(*) FROM memories').fetchone()[0],3)
                    self.assertEqual(db.execute('SELECT DISTINCT issuer FROM memory_provenance').fetchall(),[('verified-arithmetic-v1',)])
                publish(root,lambda n:dict(sequence=n,kind='approve',key=project['key'],
                    value=sign(key,n,project['key'],project['proposal_sha256'],'Operator-reviewed correction')))
                import time
                deadline=time.monotonic()+3
                while time.monotonic()<deadline:
                    with closing(sqlite3.connect(root/'memory.sqlite3')) as db:
                        row=db.execute('SELECT issuer FROM memory_provenance WHERE key=?',(project['key'],)).fetchone()
                    if row==('operator',): break
                    time.sleep(.05)
                self.assertEqual(row,('operator',))
            finally:
                (root/'STOP').touch(); thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertFalse(failures,repr(failures))

    def test_unconsumed_task_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory,Store(directory) as store:
            publish(directory,lambda n:dict(sequence=n,kind='remember',key='operator',value='pending'))
            before=(Path(directory)/'inbox.json').read_bytes()
            with self.assertRaises(Busy):
                publish(directory,lambda n:dict(sequence=n,kind='remember',key='automatic',value='overwrite'))
            self.assertEqual((Path(directory)/'inbox.json').read_bytes(),before)

    def test_unknown_signature_issuer_refused(self):
        with tempfile.TemporaryDirectory() as directory,Store(directory,lambda p:'guess',b'k'*32) as store:
            signed=sign(b'k'*32,1,'key','a'*64,'fact',issuer='model-self-approval')
            with self.assertRaises(ValueError): store.submit(1,'approve','key',signed)


if __name__=='__main__': unittest.main()
