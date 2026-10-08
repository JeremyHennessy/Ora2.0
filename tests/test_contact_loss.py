from copy import deepcopy
import itertools
import json
import unittest
from experiments import contact_loss as worker
from experiments import contact_loss_audit as audit
from experiments import precursor_coupling as old
from experiments import precursor_coupling_audit as ledger


def config(bits='0101', **changes):
    c = dict(kind='contact', bits=bits, candidate=bits, budget=len(bits), fuel=2*len(bits),
             phases=1, mode='coupled', source='producer', order=list(range(len(bits))),
             contacts='free', food='compatible', loss=0, founder='present')
    c.update(changes)
    return c


class ContactTests(unittest.TestCase):
    def test_registered_scope_and_canonical_order_inventory(self):
        panel = list(worker.configs())
        self.assertEqual(panel, list(audit.panel()))
        self.assertEqual(len(panel), 12288)
        self.assertEqual(sum(len(list(worker.requests(c))) for c in panel), 510976)
        totals = {n: 0 for n in (2, 3, 4)}
        for n in totals:
            for bits in map(''.join, itertools.product('01', repeat=n)):
                selected = worker.orders(bits)
                self.assertEqual(selected, audit.orders(bits))
                self.assertEqual(len(selected), len({''.join(bits[i] for i in ids) for ids in selected}))
                totals[n] += len(selected)
        self.assertEqual(totals, {2: 6, 3: 20, 4: 70})

    def test_extensions_disabled_elementary_law_equivalence(self):
        for n in (2, 3, 4):
            for bits in map(''.join, itertools.product('01', repeat=n)):
                for mode, source in itertools.product(old.MODES, ('producer', 'external')):
                    c = config(bits, mode=mode, source=source)
                    new_state, old_state = worker.initial(c), old.initial(c)
                    self.assertEqual(new_state, old_state)
                    for tick, request in enumerate(old.requests(c)):
                        new_state, result = worker.step(new_state, c, tick, request)
                        old_state, previous = old.step(old_state, c, tick, request)
                        self.assertEqual(new_state, old_state)
                        for field in ('failed_contact', 'failed_debit', 'lost_activation'):
                            result.pop(field)
                        self.assertEqual(result, previous)

    def test_paid_failed_food_and_partial_budget_conserve_without_capture(self):
        c = config(contacts='paid', food='mixed')
        s = worker.initial(c)
        before = ledger.balance(s)
        after, event = worker.step(s, c, 0, ['harvest', 'C', 'F0.1', None])
        self.assertEqual(event['failed_debit'], ['G0', 'G1'])
        self.assertEqual(event['heat'], 2)
        self.assertEqual(event['returned'], [])
        self.assertIn('F0.1', after['food'])
        self.assertEqual(after['waste'], [])
        self.assertEqual(ledger.balance(after), before)
        self.assertEqual((after, event), audit.advance(s, c, 0, ['harvest', 'C', 'F0.1', None]))
        s['environment']['protected'] = s['objects']['C']['work'][1:]
        s['objects']['C']['work'] = s['objects']['C']['work'][:1]
        before = ledger.balance(s)
        after, event = worker.step(s, c, 1, ['harvest', 'C', 'F0.0', None])
        self.assertEqual(event['outcome'], 'starved')
        self.assertEqual(event['failed_debit'], ['G0'])
        self.assertEqual(event['heat'], 1)
        self.assertIn('F0.0', after['food'])
        self.assertEqual(ledger.balance(after), before)
        c['contacts'] = 'free'
        free, result = worker.step(s, c, 1, ['harvest', 'C', 'F0.0', None])
        self.assertEqual(result['failed_debit'], [])
        self.assertEqual(free, s)

    def test_loss_round_dissipates_owned_potential_and_blocks_copy(self):
        c = config(loss=1)
        s = worker.initial(c)
        program = list(worker.requests(c))
        for tick, request in enumerate(program[:12]):
            s, _ = worker.step(s, c, tick, request)
        before = ledger.balance(s)
        after, result = worker.step(s, c, 12, program[12])
        self.assertEqual(len(result['lost_activation']), 4)
        self.assertEqual(result['heat'], 4)
        self.assertTrue(all(len(v) == 2 for v in after['activation'].values()))
        self.assertEqual(after['objects'], s['objects'])
        self.assertEqual(ledger.balance(after), before)
        record = worker.simulate(c)
        self.assertEqual(audit.verify_record(record, c), worker.counts(record))
        self.assertNotIn('D0', record['terminal']['objects'])

    def test_founder_ablation_preserves_assets_and_never_uses_protected_work(self):
        for food in ('compatible', 'mixed'):
            c = config(source='external', food=food)
            present = worker.initial(c)
            c['founder'] = 'removed'
            removed = worker.initial(c)
            self.assertEqual(ledger.balance(present), ledger.balance(removed))
            self.assertEqual(present['history'], removed['history'])
            self.assertEqual(removed['environment']['protected_founder_work'], ['G0', 'G1', 'G2', 'G3'])
            record = worker.simulate(c)
            self.assertEqual(audit.verify_record(record, c), worker.counts(record))
            self.assertEqual(record['terminal']['environment']['protected_founder_work'], ['G0', 'G1', 'G2', 'G3'])
            self.assertEqual(worker.counts(record)['constructions'], 0)
            self.assertEqual(worker.counts(record)['external_activation'], 4)

    def test_repeated_contacts_identity_symmetry_and_real_composition(self):
        same_word = {}
        for ids in itertools.permutations(range(4)):
            c = config(source='external', order=list(ids))
            record = worker.simulate(c)
            stats = worker.counts(record)
            self.assertEqual(audit.verify_record(record, c), stats)
            word = ''.join(c['bits'][i] for i in ids)
            # Counts/probe behavior must not depend on swapping equal-bit atom IDs.
            self.assertEqual(stats, same_word.setdefault(word, stats))
        c = config(source='external', mode='untemplated', order=[1, 0, 2, 3])
        record = worker.simulate(c)
        self.assertEqual(record['terminal']['history']['D0']['bits'], '1001')
        self.assertEqual(worker.counts(record)['probe_functions'], 1)
        self.assertEqual(worker.counts(record)['matching_functional'], 0)
        active = worker.simulate(config())
        ghost = worker.simulate(config(mode='ghost'))
        self.assertEqual(active['terminal']['history']['D0']['construction_debits'], ghost['terminal']['history']['D0']['construction_debits'])
        self.assertEqual(worker.counts(ghost)['probe_functions'], 0)

    def test_all_extension_combinations_have_independent_ledgers(self):
        for bits in ('01', '010', '0101'):
            for mode, source, contact, food, loss, founder in itertools.product(old.MODES, ('producer', 'external'),
                    ('free', 'paid'), ('compatible', 'mixed'), (0, 1), ('present', 'removed')):
                c = config(bits, mode=mode, source=source, contacts=contact, food=food, loss=loss, founder=founder)
                record = worker.simulate(c)
                self.assertEqual(audit.verify_record(record, c), worker.counts(record))

    def test_rehashed_contact_loss_genesis_and_ancestry_forgeries_rejected(self):
        for c, action, field in [(config(contacts='paid', food='mixed'), 'harvest', 'heat'), (config(loss=1), 'loss', 'heat')]:
            record = worker.simulate(c)
            forged = deepcopy(record)
            target = next(e for e in forged['events'] if e['request'][0] == action)
            target['result'][field] += 1
            chain = old.digest(forged['initial'])
            for event in forged['events']:
                event['previous'] = chain
                event.pop('sha256')
                event['sha256'] = old.digest(event)
                chain = event['sha256']
            with self.assertRaisesRegex(ValueError, 'Semantic contact'):
                audit.verify_record(forged, c)
        c = config(source='external')
        forged = worker.simulate(c)
        forged['terminal']['history']['D0']['producer_funded'] = True
        with self.assertRaisesRegex(ValueError, 'Terminal semantic'):
            audit.verify_record(forged, c)
        c = config(food='mixed')
        state = worker.initial(c)
        state['atoms']['F0.1']['bit'] = '0'
        initial, chain, events = deepcopy(state), old.digest(state), []
        for tick, request in enumerate(worker.requests(c)):
            before = old.digest(state)
            state, result = worker.step(state, c, tick, request)
            event = dict(tick=tick, request=request, before=before, after=old.digest(state), previous=chain, result=result)
            event['sha256'] = old.digest(event)
            chain = event['sha256']
            events.append(event)
        with self.assertRaisesRegex(ValueError, 'Genesis source'):
            audit.verify_record(dict(config=c, initial=initial, events=events, terminal=state), c)
        with self.assertRaisesRegex(ValueError, 'Duplicate key'):
            json.loads('{"loss":0,"loss":1}', object_pairs_hook=ledger.unique)


if __name__ == '__main__':
    unittest.main()
