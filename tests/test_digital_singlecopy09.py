import copy,unittest
from experiments.digital_singlecopy09 import World,history,h,draw
from experiments.digital_singlecopy09_audit import audit,sample

class SingleCopy09(unittest.TestCase):
    def test_matched_selector_draw_and_storage_bill(self):
        signatures=[]
        for mode in ('single','per_word','faithful'):
            w=World(25789,mode,'ancestor');w.entities[0]['pc']=3
            energy=w.entities[0]['energy'];w.step();event=w.events[-1]
            self.assertEqual(len(w.entities[0]['state_units']),18)
            self.assertEqual(event['selector_store_energy'],2)
            self.assertEqual(event['copy_energy'],3+len(event['sampling'])+2)
            self.assertEqual(energy-w.entities[0]['energy'],1+event['copy_energy'])
            signatures.append((event['selector'],event['sampling'],event['copy_energy']))
        self.assertEqual(signatures[0],signatures[1]);self.assertEqual(signatures[0],signatures[2])
        for modulus in (18,31,558):self.assertEqual(draw(25789,['fixture'],modulus),sample(25789,['fixture'],modulus))

    def test_complete_reproduction_certificates_and_tamper_refusal(self):
        faithful=history(25789,'ancestor','faithful');f=audit(faithful)
        self.assertGreater(f['births'],0)
        single=history(25789,'ancestor','single');s=audit(single)
        self.assertGreater(s['paid_copy_words'],0);self.assertTrue(all(n==1 for n in s['offspring_errors']))
        self.assertEqual(audit(history(25789,'ancestor','copy_disabled'))['births'],0)
        bad=copy.deepcopy(faithful);event=next(e for e in bad['final']['events'] if 'sampling' in e)
        event['sampling'][0]['energy']=0;bad['hash']=h(bad['final'])
        with self.assertRaises(AssertionError):audit(bad)
        bad=copy.deepcopy(faithful);bad['checkpoint']['formation'][0]['energy']=True
        with self.assertRaises(AssertionError):audit(bad)
