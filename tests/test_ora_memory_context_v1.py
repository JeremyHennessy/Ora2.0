"""Synthetic temporary stores only; no production signing or model calls."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.ora_task_store_v1 import Store
from experiments.ora_memory_context_v1 import context

KEY=b't'*32
QUOTE='Keep it running and preserve the existing results.'


def memory(store,key,value,task=1,issuer='operator'):
    # Disclosed fixture rows; never authorizes a production correction.
    with store.db:
        store.db.execute('INSERT INTO memories VALUES(?,?,?)',(key,value,task))
        store.db.execute('INSERT INTO memory_provenance VALUES(?,?,?)',(key,task,issuer))


class MemoryContext(unittest.TestCase):
    def test_native_paraphrase_gets_provenance_and_output_stays_untrusted(self):
        calls=[]
        with tempfile.TemporaryDirectory() as folder,Store(folder,lambda p:calls.append(p) or 'retain originals',KEY) as s:
            memory(s,'user:policy',QUOTE)
            baseline=s.db.execute('SELECT * FROM memories').fetchall()
            s.submit(1,'ask','new-question','May we discard the original outputs?')
            result=json.loads(s.complete(s.claim()))
            self.assertIn(QUOTE,calls[0]);self.assertFalse(result['trusted'])
            self.assertEqual(result['retrieved_memories'][0]['key'],'user:policy')
            self.assertEqual(result['retrieved_memories'][0]['value_sha256'],hashlib.sha256(QUOTE.encode()).hexdigest())
            self.assertEqual(s.db.execute('SELECT * FROM memories').fetchall(),baseline)

    def test_isolated_mode_bypasses_both_exact_hit_and_context(self):
        calls=[]
        with tempfile.TemporaryDirectory() as folder,Store(folder,lambda p:calls.append(p) or 'unknown',KEY) as s:
            memory(s,'user:policy',QUOTE)
            q='Should we halt the daemon?'
            s.submit(1,'ask-isolated','user:policy',q)
            result=json.loads(s.complete(s.claim()))
            self.assertEqual(calls,[q]);self.assertEqual(result['retrieved_memories'],[])
            s.submit(2,'ask','user:policy',q)
            self.assertEqual(s.complete(s.claim()),QUOTE);self.assertEqual(len(calls),1)

    def test_untrusted_unsigned_arithmetic_excluded_even_in_small_coverage(self):
        with tempfile.TemporaryDirectory() as folder,Store(folder,lambda p:'unknown',KEY) as s:
            memory(s,'user:unsigned',QUOTE,issuer='local-operator')
            memory(s,'user:arithmetic',QUOTE,task=2,issuer='verified-arithmetic-v1')
            memory(s,'user:colour','Preferred heading colour is amber.',task=3)
            with s.db:s.db.execute('INSERT INTO proposals VALUES(?,?,?,?)',('user:guess',QUOTE,4,'a'*64))
            q='Should we halt the daemon?';prompt,audit=context(s.db,q)
            self.assertEqual([x['key'] for x in audit],['user:colour'])
            self.assertEqual(audit[0]['selection'],'small-preference-coverage')

    def test_conflicts_both_retained_without_latest_wins(self):
        with tempfile.TemporaryDirectory() as folder,Store(folder,lambda p:'unknown',KEY) as s:
            memory(s,'user:one','Keep the service running.',task=1)
            memory(s,'user:two','Stop the service during document tasks.',task=2)
            prompt,audit=context(s.db,'Should we pause the runtime?')
            self.assertEqual(len(audit),2)
            self.assertIn('Keep the service running.',prompt)
            self.assertIn('Stop the service during document tasks.',prompt)
            self.assertIn('conflict',prompt)

    def test_bounds_do_not_truncate_question_or_oversize_record(self):
        with tempfile.TemporaryDirectory() as folder,Store(folder,lambda p:'unknown',KEY) as s:
            memory(s,'user:long','run '+('x'*1900))
            q='pause daemon';self.assertEqual(context(s.db,q),(q,[]))
            with s.db:s.db.execute('DELETE FROM memories');s.db.execute('DELETE FROM memory_provenance')
            memory(s,'user:short',QUOTE)
            q='pause '+('x'*4089);self.assertEqual(len(q.encode()),4095)
            self.assertEqual(context(s.db,q),(q,[]))

    def test_two_record_cap_citations_and_read_only_query(self):
        with tempfile.TemporaryDirectory() as folder,Store(folder,lambda p:'unknown',KEY) as s:
            for i in range(5):memory(s,'user:'+str(i),'Retain original results.',task=i+1)
            changes=s.db.total_changes;prompt,audit=context(s.db,'Delete original outputs?')
            self.assertEqual(s.db.total_changes,changes)
            self.assertEqual([r['citation'] for r in audit],['M1','M2'])
            self.assertEqual([r['task'] for r in audit],[5,4])
            self.assertLessEqual(len(prompt.encode()),4096)

    def test_no_overlap_coverage_is_bounded_and_audited(self):
        with tempfile.TemporaryDirectory() as folder,Store(folder,lambda p:'unknown',KEY) as s:
            memory(s,'user:policy',QUOTE)
            q='What is the orbital period of Neptune?'
            prompt,audit=context(s.db,q)
            self.assertTrue(prompt.startswith(q))
            self.assertEqual([x['key'] for x in audit],['user:policy'])
            self.assertEqual(audit[0]['selection'],'small-preference-coverage')

    def test_larger_inventory_keeps_zero_overlap_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder,Store(folder,lambda p:'unknown',KEY) as s:
            for i in range(3):memory(s,'user:'+str(i),QUOTE,task=i+1)
            q='Which city hosts the astronomy meetup?'
            self.assertEqual(context(s.db,q),(q,[]))

    def test_coverage_never_silently_drops_a_record_to_fit(self):
        with tempfile.TemporaryDirectory() as folder,Store(folder,lambda p:'unknown',KEY) as s:
            memory(s,'user:one','x'*1900,task=1)
            memory(s,'user:two',QUOTE,task=2)
            q='What is the lunar phase?'
            self.assertEqual(context(s.db,q),(q,[]))


if __name__=='__main__':unittest.main()
