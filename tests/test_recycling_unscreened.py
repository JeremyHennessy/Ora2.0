import copy
import unittest
from experiments import recycling_unscreened as worker
from experiments import recycling_unscreened_audit as audit

class RecyclingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = {mode: worker.simulate(dict(seed=17, mode=mode)) for mode in worker.MODES}

    def test_fresh_panel_and_separate_interpreter(self):
        self.assertEqual(worker.configs(), audit.configurations()); self.assertEqual(len(worker.configs()), 288)
        for mode, r in self.records.items():
            with self.subTest(mode=mode): self.assertEqual(worker.metrics(r), audit.verify_record(r, r['config']))

    def test_common_noise_and_random_bits_preserved_across_all_controls(self):
        reference = self.records['candidate']
        for r in self.records.values():
            self.assertEqual(r['initial']['atoms'], reference['initial']['atoms'])
            self.assertEqual([e['draw'] for e in r['events']], [e['draw'] for e in reference['events']])
            self.assertEqual(r['rng_initial'], reference['rng_initial']); self.assertEqual(r['rng_terminal'], reference['rng_terminal'])
            self.assertEqual(r['noise_cursor'], 1536)
        empty = worker.metrics(self.records['no_initial_work'])['totals']
        self.assertEqual(empty['assemblies'], 0); self.assertEqual(empty['assembled_captures'], 0)

    def test_supplied_manufacture_spends_finite_resources_and_no_noise(self):
        c = dict(seed=17, mode='supplied'); s, rng, prep = worker.initial(c); other, noise, independent = audit.genesis(c)
        self.assertEqual(s, other); self.assertEqual(prep, independent); self.assertEqual(rng.getstate(), noise.getstate())
        self.assertEqual(len(s['bank']), 42); self.assertEqual(len(s['waste']), 11); self.assertEqual(len(prep), 18)
        product = next(v for v in s['history'].values() if v['kind'] == 'product')
        self.assertEqual(len(product['atoms']), 6); self.assertEqual(len(product['debits']), 19)
        self.assertEqual(len(product['endowment']), 2); self.assertFalse(product['fully_capture_funded'])
        audit.cut.validate(s)

    def test_rehashed_opportunity_noise_manufacture_and_terminal_forgeries_reject(self):
        for mode, field in (('candidate', 'opportunity'), ('candidate', 'noise'), ('candidate', 'cursor'), ('supplied', 'manufacture'), ('candidate', 'terminal')):
            r = self.records[mode]; bad = copy.deepcopy(r)
            if field == 'opportunity':
                bad['events'][128]['opportunities']['capture_cut_reserve_pairs'] += 1
                previous = bad['events'][0]['previous']
                for event in bad['events']:
                    event['previous'] = previous; event.pop('sha256')
                    event['sha256'] = worker.cut.digest(event); previous = event['sha256']
            elif field == 'noise': bad['rng_terminal'] = bad['rng_initial']
            elif field == 'cursor': bad['noise_cursor'] = True
            elif field == 'manufacture':
                bad['preparation'][0]['result']['spent'] = []
                previous = bad['preparation'][0]['previous']
                for event in bad['preparation']:
                    event['previous'] = previous; event.pop('sha256')
                    event['sha256'] = worker.cut.digest(event); previous = event['sha256']
            else: bad['terminal']['heat'] += 1
            with self.subTest(field=field), self.assertRaises(ValueError): audit.verify_record(bad, r['config'])

if __name__ == '__main__': unittest.main()
