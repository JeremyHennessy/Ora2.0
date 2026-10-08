import copy
import json
from pathlib import Path
import tempfile
import unittest

from experiments import energy_binding as worker
from experiments import energy_binding_audit as audit

REVISION = 'a'*40


class EnergyBindingTests(unittest.TestCase):
    def test_every_registered_case_has_independent_conserving_transitions(self):
        cases = list(worker.recipes())
        expected = list(audit.enumerate_cases())
        self.assertEqual(len(cases), 4192)
        for (c, requests), (other, independent) in zip(cases, expected):
            self.assertEqual(c, other)
            self.assertEqual([list(r) for r in requests], independent)
            state = worker.initial(c['bits'], c['work'], c['foods'], c['capacity'], c['storage'])
            oracle = audit.genesis(c)
            self.assertEqual(state, oracle)
            total = audit.ledger(state)
            for tick, request in enumerate(requests):
                state, result = worker.transition(state, c['mode'], tick, request)
                oracle, observed = audit.advance(oracle, c['mode'], tick, request)
                self.assertEqual((state, result), (oracle, observed))
                self.assertEqual(audit.ledger(state), total)

    def test_binding_trap_overflow_and_ghost_are_not_usable_capture(self):
        s = worker.initial('00', 1, [1], 2, 'local')
        total = audit.ledger(s)
        s, _ = worker.transition(s, 'selective', 0, ['recognize', 'N0'])
        s, r = worker.transition(s, 'selective', 1, ['process', None])
        self.assertEqual(r['outcome'], 'bound_starved')
        self.assertEqual((len(s['tokens']), s['bound'], audit.ledger(s)), (0, 'N0', total))
        s, _ = worker.transition(s, 'selective', 2, ['release', None])
        self.assertEqual((len(s['tokens']), s['food'], s['heat']), (0, ['N0'], 1))
        for mode, work, heat, overflow in [('selective', 2, 8, 1), ('ghost', 0, 10, 0)]:
            s = worker.initial('00', 2, [1], 2, 'local')
            s, _ = worker.transition(s, mode, 0, ['recognize', 'N0'])
            s, r = worker.transition(s, mode, 1, ['process', None])
            self.assertEqual((len(s['tokens']), s['heat'], len(r['overflow'])), (work, heat, overflow))
            self.assertEqual(audit.ledger(s)[1], 11)

    def test_protected_work_reclaims_are_explicitly_external(self):
        for store, reclaimed in [('local', False), ('protected', True)]:
            s = worker.initial('000', 2, [1], 3, store)
            for tick, request in enumerate([['recognize', 'N0'], ['process', None], ['decay', None], ['reclaim', 'B0']]):
                s, r = worker.transition(s, 'selective', tick, request)
            self.assertEqual(r['outcome'] == 'reclaimed', reclaimed)
            self.assertEqual(r['reclaimer'], 'engine_bank' if reclaimed else None)
            self.assertFalse(s['live'])
        forged = copy.deepcopy(s)
        forged['tokens'].append(copy.deepcopy(forged['tokens'][0]))
        with self.assertRaises(ValueError):
            audit.ledger(forged)

    def test_source_bound_audit_is_read_only_and_rejects_rehashed_costs(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'data'
            worker.run(output, REVISION)
            original = {p.name: p.read_bytes() for p in output.iterdir()}
            report = audit.audit(output, REVISION)
            self.assertEqual(report['authored_cases'], 4192)
            self.assertEqual(original, {p.name: p.read_bytes() for p in output.iterdir()})
            rows = [json.loads(line) for line in original['records.jsonl'].splitlines()]
            row = next(r for r in rows if r['events'][0]['result']['charged'] == 1)
            row['events'][0]['result']['charged'] = 0
            chain = worker.digest(row['initial'])
            for e in row['events']:
                e['previous'] = chain
                e['sha256'] = worker.digest({k: v for k, v in e.items() if k != 'sha256'})
                chain = e['sha256']
            raw = ''.join(worker.canonical(r)+'\n' for r in rows).encode()
            (output/'records.jsonl').write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'divergence'):
                audit.audit(output, REVISION)
            with self.assertRaises(ValueError):
                audit.unique([('x', 1), ('x', 2)])


if __name__ == '__main__':
    unittest.main()
