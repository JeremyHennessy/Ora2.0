from copy import deepcopy
import itertools
import json
import unittest

from experiments import precursor_coupling as worker
from experiments import precursor_coupling_audit as audit


def config(bits='0101', mode='coupled', source='producer', budget=4, fuel=8, phases=1):
    return dict(kind='renewal' if phases == 2 else 'primary', bits=bits, candidate=bits,
                budget=budget, fuel=fuel, mode=mode, source=source, phases=phases)


class PrecursorTests(unittest.TestCase):
    def test_registered_scope_and_all_sequence_renewal_accounting(self):
        registered = list(worker.configs())
        self.assertEqual(len(registered), 9264)
        self.assertEqual(sum(len(list(worker.requests(c))) for c in registered), 189120)
        self.assertEqual(list(audit.panel()), registered)
        for c in registered:
            if c['kind'] != 'renewal':
                continue
            with self.subTest(bits=c['bits'], mode=c['mode'], source=c['source']):
                record = worker.simulate(c)
                self.assertEqual(audit.verify_record(record, c), worker.counts(record))

    def test_full_price_and_cost_matched_energetic_ghost(self):
        active = worker.simulate(config())
        ghost = worker.simulate(config(mode='ghost'))
        active_birth = next(e for e in active['events'] if e['result']['outcome'] == 'constructed')
        ghost_birth = next(e for e in ghost['events'] if e['result']['outcome'] == 'ghost_constructed')
        self.assertEqual(active['events'][:active_birth['tick']], ghost['events'][:ghost_birth['tick']])
        self.assertEqual(active_birth['result']['spent'], ghost_birth['result']['spent'])
        a, g = active['terminal']['history']['D0'], ghost['terminal']['history']['D0']
        self.assertEqual(len(a['construction_debits']), 13)
        self.assertEqual(a['atoms'], g['atoms'])
        self.assertEqual(a['bonds'], g['bonds'])
        self.assertEqual(len(a['work']), 2)
        self.assertEqual(g['work'], [])
        self.assertEqual(worker.counts(ghost)['probe_functions'], 0)
        self.assertEqual(worker.counts(active)['probe_functions'], 1)

    def test_external_funding_withdrawal_and_short_component_failure(self):
        for bits in ('01', '010', '0101'):
            c = config(bits=bits, source='withdrawn', budget=len(bits), fuel=2*len(bits), phases=2)
            record = worker.simulate(c)
            audit.verify_record(record, c)
            self.assertFalse(record['terminal']['history']['D0']['producer_funded'])
            self.assertEqual(worker.counts(record)['second_producer_funded_functional'], int(len(bits) == 4))
        own = worker.simulate(config(phases=2))
        self.assertEqual(worker.counts(own)['renewed_functional'], 1)
        uncoupled = worker.simulate(config(mode='uncoupled', source='external'))
        self.assertEqual(worker.counts(uncoupled)['constructions'], 0)

    def test_actual_composition_function_and_startup_controls(self):
        mismatched = config(source='external', budget=1, fuel=0)
        mismatched['candidate'] = '1101'
        selective = worker.simulate(mismatched)
        self.assertNotIn('D0', selective['terminal']['objects'])
        mismatched['mode'] = 'untemplated'
        free = worker.simulate(mismatched)
        self.assertEqual(free['terminal']['history']['D0']['bits'], '1101')
        self.assertFalse(free['terminal']['history']['D0']['matching'])
        self.assertEqual(worker.counts(free)['probe_functions'], 1)
        mismatched['candidate'] = '0100'
        wrong_function = worker.simulate(mismatched)
        self.assertEqual(worker.counts(wrong_function)['probe_functions'], 0)
        for budget in (0, 1):
            record = worker.simulate(config(budget=budget))
            self.assertEqual(worker.counts(record)['producer_funded_functional'], 0)

    def test_rehashed_energy_and_ancestry_forgery_rejection(self):
        c = config()
        record = worker.simulate(c)
        forged = deepcopy(record)
        forged['events'][0]['result']['heat'] += 1
        chain = worker.digest(forged['initial'])
        for event in forged['events']:
            event['previous'] = chain
            event.pop('sha256')
            event['sha256'] = worker.digest(event)
            chain = event['sha256']
        with self.assertRaisesRegex(ValueError, 'Semantic event'):
            audit.verify_record(forged, c)
        forged = deepcopy(record)
        forged['terminal']['history']['D0']['producer'] = 'environment0'
        with self.assertRaisesRegex(ValueError, 'Terminal semantic'):
            audit.verify_record(forged, c)
        # An internally conserved, re-simulated false genesis must still be rejected.
        c = config(source='external')
        original = worker.simulate(c)
        state = deepcopy(original['initial'])
        state['units']['E0.0']['origin'] = 'activation'
        false_initial = deepcopy(state)
        chain, events = worker.digest(state), []
        for tick, request in enumerate(worker.requests(c)):
            before = worker.digest(state)
            state, result = worker.step(state, c, tick, request)
            event = dict(tick=tick, request=request, before=before, after=worker.digest(state), previous=chain, result=result)
            event['sha256'] = worker.digest(event)
            chain = event['sha256']
            events.append(event)
        with self.assertRaisesRegex(ValueError, 'Genesis source'):
            audit.verify_record(dict(config=c, initial=false_initial, events=events, terminal=state), c)

    def test_duplicate_material_energy_and_json_rejected(self):
        s = worker.initial(config())
        duplicate = deepcopy(s)
        duplicate['ready'].append(duplicate['ready'][0])
        with self.assertRaisesRegex(ValueError, 'Unique material'):
            audit.balance(duplicate)
        duplicate = deepcopy(s)
        duplicate['objects']['C']['work'][0] = duplicate['objects']['C']['work'][1]
        with self.assertRaisesRegex(ValueError, 'Unique energy'):
            audit.balance(duplicate)
        with self.assertRaisesRegex(ValueError, 'Duplicate key'):
            json.loads('{"source":"producer","source":"external"}', object_pairs_hook=audit.unique)


if __name__ == '__main__':
    unittest.main()

