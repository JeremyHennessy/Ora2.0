"""Real Windows sharing tests on temporary files; no live tasks or model calls."""
import json,os,sqlite3,sys,tempfile,unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.ora_mailbox_reader_v1 import open_reader
from experiments.ora_mailbox_v1 import publish,Busy
from experiments.ora_task_store_v1 import Store,serve

@unittest.skipUnless(os.name=='nt','Windows sharing semantics')
class Sharing(unittest.TestCase):
 def fixture(self,root):
  with closing(sqlite3.connect(root/'memory.sqlite3')) as db:
   db.execute('create table meta(submitted integer)');db.execute('insert into meta values(0)');db.commit()
  (root/'inbox.json').write_text(json.dumps([dict(sequence=0,kind='ask',key='old',value='old')]))
 def test_held_reader_blocks_producer_before_intent_and_keeps_generation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);old=(root/'inbox.json').read_bytes();intents=[]
   def build(n):intents.append(n);return dict(sequence=n,kind='ask-isolated',key='new',value='question')
   with open_reader(root/'inbox.json') as held:
    with self.assertRaises(Busy):publish(root,build)
    self.assertEqual(held.read(),old)
   self.assertEqual(intents,[]);self.assertFalse((root/'mailbox.next').exists())
   self.assertEqual(publish(root,build),1)
   self.assertEqual(intents,[1])
   with open_reader(root/'inbox.json') as fresh:self.assertEqual(json.load(fresh)[0]['key'],'new')
   with self.assertRaises(Busy):publish(root,build)
 def test_consumer_skips_busy_producer_poll_without_consuming(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   def build(n):
    with open_reader(root/'inbox.json') as stream:self.assertIsNone(stream)
    return dict(sequence=n,kind='ask',key='new',value='new')
   self.assertEqual(publish(root,build),1)
 def test_standard_reader_still_denies_replace_without_retry(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);calls=[]
   def build(n):calls.append(n);return dict(sequence=n,kind='ask',key='one',value='one')
   with (root/'inbox.json').open('rb'):
    with self.assertRaises(PermissionError):publish(root,build)
   self.assertEqual(calls,[1]);self.assertTrue((root/'mailbox.next').exists())
 def test_exception_releases_reader_lock(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   with self.assertRaisesRegex(RuntimeError,'fixture'):
    with open_reader(root/'inbox.json'):raise RuntimeError('fixture')
   self.assertEqual(publish(root,lambda n:dict(sequence=n,kind='ask',key='new',value='new')),1)
 def test_producer_lock_in_other_process_prevents_reader_open(self):
  import subprocess
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   code="import msvcrt,sys; f=open(sys.argv[1],'a+b'); msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1); print('locked',flush=True); sys.stdin.readline()"
   child=subprocess.Popen([sys.executable,'-B','-c',code,str(root/'mailbox.lock')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
   try:
    self.assertEqual(child.stdout.readline().strip(),'locked')
    with open_reader(root/'inbox.json') as stream:self.assertIsNone(stream)
   finally:
    child.communicate('release\n',timeout=5)
   with open_reader(root/'inbox.json') as stream:self.assertIsNotNone(stream)
 def test_missing_file_error_is_not_retried_or_created(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'absent'
   with self.assertRaises(OSError):
    with open_reader(p):pass
   self.assertFalse(p.exists())
 def test_service_uses_sharing_reader_and_preserves_task_identity(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);inbox=root/'inbox.json'
   inbox.write_text(json.dumps([dict(sequence=1,kind='remember',key='fixture',value='approved-fixture')]))
   with Store(root) as store:
    import experiments.ora_task_store_v1 as module
    with patch.object(module,'open_reader',wraps=open_reader) as reader:
     self.assertEqual(serve(store,root/'STOP',seconds=1,max_tasks=1,inbox=inbox)['completed'],1)
     reader.assert_called_once_with(inbox)
    store.submit(2,'recall','fixture');self.assertEqual(store.complete(store.claim()),'approved-fixture')
 def test_oversized_mailbox_refused_before_task_submission(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'inbox.json';p.write_bytes(b' '*65537)
   with Store(root) as store:
    with self.assertRaisesRegex(ValueError,'64 KiB'):serve(store,root/'STOP',seconds=1,max_tasks=1,inbox=p)
    self.assertIsNone(store.claim())
if __name__=='__main__':unittest.main()
