"""Inert ledger tests. No World construction or dispatch."""
from types import SimpleNamespace as Row
import unittest

from experiments.al02_depletion_producer import EscrowContinuation, b_accounting, check_ledger
from experiments.executed_heredity import World


class EscrowProducerTests(unittest.TestCase):
    def setUp(self):
        actor = Row(organism_id=0, parent_id=None, energy=24,
                    tape=[Row(material_unit=i) for i in range(4)], nursery=[])
        self.state = Row(food_a=0, food_b=0, escrow_b=10, initial_food_b=18, heat=380,
                         organisms={0: actor}, free_units=set(range(4, 256)),
                         material_units=256, genesis_material=256, genesis_energy=604,
                         material_residual_max=0, energy_residual_max=0,
                         population_limit=64, births=[],
                         events=[dict(kind='EXEC', outcome='ate_b') for _ in range(8)])

    def test_frozen_dispatch_and_conserved_compartments(self):
        self.assertIs(EscrowContinuation.execute_one, World.execute_one)
        for accessible, escrow in [(0, 10), (10, 0)]:
            self.state.food_b, self.state.escrow_b = accessible, escrow
            self.assertEqual(check_ledger(self.state), (0, 0))
            self.assertEqual(b_accounting(self.state), dict(
                remaining_food_b=accessible, escrow_b=escrow, consumed_food_b=8))

    def test_rejects_corrupt_ledgers(self):
        for key, value, error in [('escrow_b', 9, 'energy 20|energy -20'),
                                  ('food_b', 1, 'accessible B'),
                                  ('heat', 379, 'energy -1')]:
            with self.subTest(key=key):
                original = getattr(self.state, key)
                setattr(self.state, key, value)
                with self.assertRaisesRegex(AssertionError, error):
                    check_ledger(self.state)
                setattr(self.state, key, original)
        self.state.free_units.add(0)
        with self.assertRaisesRegex(AssertionError, 'Material units'):
            check_ledger(self.state)

    def test_rejects_birth_identity_hidden_under_authorized_key(self):
        self.state.organisms[0].organism_id = 1
        self.state.organisms[0].parent_id = 0
        with self.assertRaisesRegex(AssertionError, 'Unverified descendant'):
            check_ledger(self.state)

    def test_rejects_unregistered_birth_and_forged_meal(self):
        actor = self.state.organisms.pop(0)
        actor.organism_id = 1
        self.state.organisms[1] = actor
        with self.assertRaisesRegex(AssertionError, 'Unregistered'):
            check_ledger(self.state)
        self.state.events.append(dict(kind='EXEC', outcome='ate_b'))
        with self.assertRaisesRegex(AssertionError, 'do not reconcile'):
            b_accounting(self.state)
