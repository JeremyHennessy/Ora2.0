import copy,json,unittest
from decimal import Decimal as D
from experiments.mode_converter import fixtures,World
from experiments.mode_converter_audit import audit,unique
class ModeConverterTests(unittest.TestCase):
    def test_complete_independent_interpretation(self):self.assertTrue(audit(fixtures())['verified'])
    def test_mode_is_paid_and_can_return_energy(self):
        events=World('candidate').run()['events']
        first=events[0];self.assertEqual(first['channel'],'form');self.assertEqual(D(first['formation_debit']),1)
        self.assertTrue(any(e['channel']=='release' for e in events))
    def test_complete_loss_preserves_material_and_no_rescue(self):
        event=next(e for e in World('candidate').run()['events'] if e['kind']=='damage')
        self.assertTrue(all(p['bond'] is None and p['mode']==0 for p in event['after']['parts']))
        self.assertEqual(D(event['formation_debit']),0);self.assertEqual(D(event['compression_debit']),0);self.assertEqual(D(event['load_work']),0)
    def test_free_compression_or_omitted_event_refused(self):
        original=fixtures();a=copy.deepcopy(original);a['records'][0]['events'][0]['formation_debit']='0'
        with self.assertRaises(ValueError):audit(a)
        original['records'][0]['events'].pop(1)
        with self.assertRaises(ValueError):audit(original)
    def test_forged_counter_or_success_refused(self):
        f=fixtures();f['records'][0]['initial']['next_object']=False
        with self.assertRaises(ValueError):audit(f)
        f=fixtures();f['records'][0]['score']['success']=True
        with self.assertRaises(ValueError):audit(f)
    def test_nonfinite_or_duplicate_energy_refused(self):
        f=fixtures();f['records'][0]['events'][0]['load_work']='NaN'
        with self.assertRaises(ValueError):audit(f)
        with self.assertRaises(ValueError):json.loads('{"energy":0,"energy":1}',object_pairs_hook=unique)
if __name__=='__main__':unittest.main()
