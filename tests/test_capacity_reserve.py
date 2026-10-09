import copy
import unittest
from experiments import capacity_reserve as worker
from experiments import capacity_reserve_audit as audit

class CapacityTests(unittest.TestCase):
    def test_frozen_scope_and_independent_complete_costs(self):
        self.assertEqual(list(worker.configs()), audit.configurations())
        self.assertEqual(len(audit.configurations()), 2688)
        for p in (4, 5, 6):
            for mode in worker.MODES:
                for word in ('00', '000', '0000'):
                    c = dict(payer_size=p, word=word, budget=32, food_bit='1', mode=mode)
                    r = worker.simulate(c)
                    self.assertEqual(worker.metrics(r), audit.verify_record(r, c))
                    self.assertLessEqual(len(r['events']) + len(r['preparation']), 80)
                    audit.prior.validate(r['terminal'])

    def test_supplied_manufacture_is_fully_paid_not_free_endowment(self):
        for p in (4, 5, 6):
            c = dict(payer_size=p, word='00', budget=0, food_bit='1', mode='supplied')
            s, prep = worker.initial(c); other, transcript = audit.genesis(c)
            self.assertEqual(s, other); self.assertEqual(prep, transcript)
            self.assertEqual(sum(len(e['result']['spent']) for e in prep if e['request']['op'] == 0), 4 * p - 2)
            self.assertEqual(len(s['waste']), 2 * p - 1)
            payer = next(v for v in s['history'].values() if v['kind'] == 'product')
            self.assertEqual(len(payer['debits']), 3 * p + 1)
            self.assertEqual(len(payer['bonds']), p - 1); self.assertEqual(len(payer['endowment']), 2)
            self.assertFalse(payer['fully_capture_funded']); audit.prior.validate(s)

    def test_cut_ghost_identical_full_debits_and_reserve_bounds(self):
        for p in (4, 5, 6):
            for n in (2, 3, 4):
                snapshots = []
                for mode in ('candidate', 'cut_ghost'):
                    c = dict(payer_size=p, word='0' * n, budget=32, food_bit='1', mode=mode)
                    s, _ = worker.initial(c)
                    for t, op, a, phase in worker.schedule(c):
                        q = worker.select(s, c, op, a, phase); result = worker.prior.step(s, c, t, q)
                        if op == 6:
                            snapshots.append((copy.deepcopy(s), result)); break
                self.assertEqual(snapshots[0][1]['spent'], snapshots[1][1]['spent'])
                self.assertEqual(snapshots[0][1]['heat'], snapshots[1][1]['heat'])
                if p >= n + 1:
                    s, result = snapshots[0]
                    self.assertEqual(len(s['products'][result['actor']]['work']), p - n - 1)
                if p < n + 3:
                    c['mode'] = 'candidate'
                    self.assertEqual(worker.metrics(worker.simulate(c))['fully_capture_paid_probe'], 0)

    def test_manufacture_funding_capacity_and_boolean_forgeries_reject(self):
        c = dict(payer_size=6, word='00', budget=32, food_bit='1', mode='supplied'); r = worker.simulate(c)
        for kind in ('manufacture', 'heat', 'funding', 'capacity'):
            bad = copy.deepcopy(r)
            if kind == 'manufacture': bad['preparation'][0]['result']['spent'] = []
            elif kind == 'heat': bad['terminal']['heat'] += 1
            elif kind == 'funding':
                next(v for v in bad['terminal']['history'].values() if v['kind'] == 'product')['fully_capture_funded'] = 1
            else: bad['config']['payer_size'] = 7
            with self.subTest(kind=kind), self.assertRaises(ValueError): audit.verify_record(bad, c)

if __name__ == '__main__': unittest.main()
