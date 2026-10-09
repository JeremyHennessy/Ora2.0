"""Authored stoichiometric checks, not naturally realized organization."""
import copy
import unittest
from experiments import coupled_construction as producer
from experiments import coupled_construction_audit as verifier


class Accounting(unittest.TestCase):
    def test_all_local_inventory_rules_match_independent_vectors(self):
        # Complete closure of the richest registered case; compare edges as sets.
        pending = [producer.initial(36)]
        seen = set(pending)
        while pending:
            state = pending.pop()
            got = producer.successors(state, 15, 'network')
            self.assertEqual(set(got), set(verifier.following(state, 15, 'network')))
            for _, child in got:
                if child not in seen:
                    seen.add(child)
                    pending.append(child)

    def test_no_energy_or_recycle_refund(self):
        state = (1, 0, 1, 0, 0, 0, 2, 2, 0, 0)
        self.assertEqual(producer.successors(state, 15, 'network'),
                         [('recycle-0', (1, 0, 0, 0, 2, 0, 0, 2, 0, 0))])
        self.assertEqual(producer.successors(state, 15, 'no-recycling'), [])

    def test_immutable_raw_provenance_and_new_identity(self):
        case = producer.enumerate_case(15, 36, 'network')
        self.assertTrue(case['feasible'])
        w = dict(rows=producer.witness(case))
        verifier.interpret(w, case)
        self.assertEqual(len(w['rows'][-1]['objects']), 4)
        for field in ('heat', 'id', 'atoms'):
            forged = copy.deepcopy(w)
            if field == 'heat':
                forged['rows'][-1]['heat'] -= 1
            elif field == 'id':
                forged['rows'][-1]['objects'][-1]['id'] = 0
            else:
                forged['rows'][-1]['objects'][-1]['atoms'] = [0, 0]
            with self.assertRaises(ValueError):
                verifier.interpret(forged, case)

    def test_all_topologies_unfunded_and_no_recycle_refuse(self):
        for mask in range(16):
            for arm in producer.ARMS:
                self.assertFalse(producer.enumerate_case(mask, 12, arm)['feasible'])
            self.assertFalse(producer.enumerate_case(mask, 36, 'no-recycling')['feasible'])

    def test_blind_complete_damage_and_energy_removal(self):
        state = (0, 9, 4, 4, 0, 0, 0, 0, 1, 1)
        self.assertEqual(producer.successors(state, 6, 'withdrawal'),
                         [('damage', (1, 0, 4, 4, 0, 0, 2, 2, 0, 0))])


if __name__ == '__main__':
    unittest.main()
