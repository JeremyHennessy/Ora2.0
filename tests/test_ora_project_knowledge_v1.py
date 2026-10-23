"""Synthetic temporary stores and keys only;no production approval/model."""
from pathlib import Path
from contextlib import contextmanager
import hashlib,json,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.ora_project_knowledge_v1 import Client,correction_check,prompt_for,digest,bound_note
from experiments.ora_task_store_v1 import Store
from experiments.ora_controller_v1 import atomic

@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);receipts=root/'receipts';receipts.mkdir();(root/'feedback.key').write_bytes(b't'*32)
        with Store(root,lambda p:'{"answer":"synthetic draft","cite":"NONE"}',b't'*32) as store:
            with store.db:
                store.db.execute('INSERT INTO memories VALUES(?,?,?)',('user:original','Protected baseline',1))
                store.db.execute('INSERT INTO memory_provenance VALUES(?,?,?)',('user:original',1,'operator'))
            c=object.__new__(Client);c.root=root;c.receipts=receipts;c.config={'documents':{}};c.healthy=lambda:None
            def immediate(run,tag,kind,key,build):
                n=store.status()['submitted']+1;value=build(n)
                atomic(run/(tag+'-publication.json'),dict(sequence=n,kind=kind,key=key,payload_sha256=digest(value.encode())))
                store.submit(n,kind,key,value);result=store.complete(store.claim())
                reply=dict(state='done',sequence=n,result=result);atomic(run/(tag+'-result.json'),reply);return reply
            c.request=immediate
            yield c,store

class Knowledge(unittest.TestCase):
    def test_actual_store_signed_correction_and_reopen(self):
        with fixture() as (c,s):
            q=c.ask('What fixture fact should be retained?');self.assertFalse(q['trusted'])
            answer=c.correct(q['run_id'],q['proposal_sha256'],'Synthetic operator fixture fact.')
            self.assertTrue(answer['approved'])
            review=c.review(q['run_id']);self.assertEqual(review['approved_note'][0],bound_note('What fixture fact should be retained?','Synthetic operator fixture fact.'))
            self.assertEqual(review['approved_note'][1],'operator')
            self.assertEqual(s.db.execute('SELECT value FROM memories WHERE key=?',('user:original',)).fetchone(),('Protected baseline',))
            self.assertNotIn((c.root/'feedback.key').read_bytes().hex(),json.dumps(review))

    def test_digest_mismatch_never_signs(self):
        with fixture() as (c,s):
            q=c.ask('Question')
            with self.assertRaises(ValueError):c.correct(q['run_id'],'a'*64,'Fixture correction')
            self.assertFalse((c.run_dir(q['run_id'])/'operator-correction.json').exists())
            self.assertEqual(s.db.execute('SELECT count(*) FROM memories').fetchone(),(1,))

    def test_protected_namespace_and_existing_notes(self):
        with fixture() as (c,s):
            q=c.ask('Question');key='user:project-note:'+q['run_id']
            with self.assertRaises(ValueError):correction_check(s.db,'user:original',q['proposal_sha256'],'bad overwrite')
            c.correct(q['run_id'],q['proposal_sha256'],'Fixture correction')
            with self.assertRaises(ValueError):c.correct(q['run_id'],q['proposal_sha256'],'Replacement')
            self.assertEqual(s.db.execute('SELECT value FROM memories WHERE key=?',(key,)).fetchone(),(bound_note('Question','Fixture correction'),))

    def test_expired_proposal_refused(self):
        with fixture() as (c,s):
            q=c.ask('Question')
            with s.db:s.db.execute('DELETE FROM proposals')
            with self.assertRaises(ValueError):c.correct(q['run_id'],q['proposal_sha256'],'Fixture correction')

    def test_capacity_prevents_baseline_eviction(self):
        with fixture() as (c,s):
            q=c.ask('Question')
            with s.db:
                for i in range(255):s.db.execute('INSERT INTO memories VALUES(?,?,?)',('fixture:'+str(i),'value',1))
            with self.assertRaises(ValueError):c.correct(q['run_id'],q['proposal_sha256'],'Fixture correction')
            self.assertEqual(s.db.execute('SELECT count(*) FROM memories').fetchone(),(256,))

    def test_prompt_bounds_and_quoted_document(self):
        p=prompt_for('What is the selected source timeout?',dict(id='DOC',sha256='a'*64,text='untrusted source text'))
        self.assertIn('quoted data',p);self.assertIn('D1',p);self.assertLessEqual(len(p.encode()),3000)
        with self.assertRaises(ValueError):prompt_for('x'*513)
        with self.assertRaises(ValueError):prompt_for('Q',dict(id='DOC',sha256='a'*64,text='x'*2049))

    def test_document_hash_change_refused(self):
        with fixture() as (c,s):
            doc=c.root/'doc.txt';doc.write_text('selected document')
            c.config['documents']={'DOC':dict(path=str(doc),sha256=digest(doc.read_bytes()))}
            self.assertEqual(c.document('DOC')['text'],'selected document')
            doc.write_text('changed')
            with self.assertRaises(ValueError):c.document('DOC')

    def test_review_recovers_without_resubmission(self):
        with fixture() as (c,s):
            q=c.ask('Question');root=c.run_dir(q['run_id']);(root/'answer.json').unlink()
            before=s.status()['submitted'];review=c.review(q['run_id'])
            self.assertEqual(review['proposal']['proposal_sha256'],q['proposal_sha256']);self.assertEqual(s.status()['submitted'],before)

    def test_sequence_content_conflict_refused(self):
        with fixture() as (c,s):
            q=c.ask('Question');root=c.run_dir(q['run_id']);p=root/'ask-publication.json';v=json.loads(p.read_text());v['payload_sha256']='a'*64;atomic(p,v)
            with self.assertRaises(ValueError):c.review(q['run_id'])

    def test_publication_uncertainty_is_not_retried(self):
        with fixture() as (c,s):
            run=c.receipts/('f'*32);run.mkdir()
            def uncertain(root,build):build(1);raise OSError('synthetic publication uncertainty')
            with patch('experiments.ora_project_knowledge_v1.publish',side_effect=uncertain) as publish:
                with self.assertRaises(OSError):Client.request(c,run,'fixture','approve','fixture',lambda n:'payload')
                with self.assertRaises(ValueError):Client.request(c,run,'fixture','approve','fixture',lambda n:'payload')
                self.assertEqual(publish.call_count,1)

    def test_receipt_path_and_input_bounds(self):
        with fixture() as (c,s):
            with self.assertRaises(ValueError):c.run_dir('../feedback.key')
            q=c.ask('Question')
            with self.assertRaises(ValueError):c.correct(q['run_id'],q['proposal_sha256'],'x'*513)

    def test_receipt_capacity_refuses_without_pruning(self):
        with fixture() as (c,s):
            for i in range(128):(c.receipts/format(i,'032x')).mkdir()
            with self.assertRaises(ValueError):c.ask('Question')
            self.assertEqual(len(list(c.receipts.iterdir())),128)
            self.assertEqual(s.status()['submitted'],0)

    def test_short_answer_keeps_question_for_native_transfer_retrieval(self):
        from experiments.ora_memory_context_v1 import context
        with fixture() as (c,s):
            q=c.ask('What is the HTTP timeout in the selected cold preparation source?')
            c.correct(q['run_id'],q['proposal_sha256'],'120 seconds')
            prompt,audit=context(s.db,'How many seconds is the HTTP timeout for cold preparation?')
            self.assertTrue(any(a['key']=='user:project-note:'+q['run_id'] for a in audit))
            self.assertIn('120 seconds',prompt)

if __name__=='__main__':unittest.main()
