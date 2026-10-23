"""Windows temporary-fixture diagnosis. No live store, models or tasks."""
import json,os,sqlite3,sys,tempfile,unittest
from pathlib import Path
from contextlib import closing
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.ora_mailbox_v1 import publish
from experiments.ora_project_knowledge_v1 import Client,digest
@unittest.skipUnless(os.name=='nt','Windows delete-sharing semantics')
class Diagnosis(unittest.TestCase):
 def fixture(self,root):
  with closing(sqlite3.connect(root/'memory.sqlite3')) as db:
   db.execute('create table meta(submitted integer)');db.execute('insert into meta values(0)')
   db.execute('create table tasks(id integer,kind text,key text,value text,state text,result text)');db.commit()
  (root/'inbox.json').write_text(json.dumps([dict(sequence=0,kind='ask',key='old',value='old')]))
 def test_open_standard_reader_reproduces_access_denial_without_publication(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);old=(root/'inbox.json').read_bytes();intents=[]
   def build(n):
    intents.append(n);return dict(sequence=n,kind='ask-isolated',key='pilot',value='question')
   with (root/'inbox.json').open('rb') as held_reader:
    self.assertEqual(held_reader.read(),old)
    with self.assertRaises(PermissionError) as error:publish(root,build)
   self.assertIn(error.exception.winerror,[5,32]);self.assertEqual(intents,[1])
   self.assertEqual((root/'inbox.json').read_bytes(),old)
   self.assertEqual(json.loads((root/'mailbox.next').read_text())[0]['key'],'pilot')
   with closing(sqlite3.connect(root/'memory.sqlite3')) as db:self.assertEqual(db.execute('select submitted from meta').fetchone(),(0,))
 def test_later_sequence_collision_cannot_recover_other_task_as_pilot(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);run=root/'saved';run.mkdir()
   publication=dict(sequence=1,kind='ask-isolated',key='pilot',payload_sha256=digest(b'question'))
   (run/'ask-publication.json').write_text(json.dumps(publication))
   with closing(sqlite3.connect(root/'memory.sqlite3')) as db:db.execute('insert into tasks values(1,?,?,?,?,?)',('ask','arithmetic-add:13:15','13+15','done','28'));db.commit()
   client=Client.__new__(Client);client.root=root
   with self.assertRaisesRegex(ValueError,'different content'):client.recover(run,'ask')
   self.assertFalse((run/'ask-result.json').exists())
 def test_standard_publish_works_when_no_reader_is_held(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   self.assertEqual(publish(root,lambda n:dict(sequence=n,kind='ask-isolated',key='fixture-only',value='question')),1)
   self.assertEqual(json.loads((root/'inbox.json').read_text())[0]['key'],'fixture-only')
if __name__=='__main__':unittest.main()
