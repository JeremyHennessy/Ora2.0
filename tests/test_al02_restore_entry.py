"""Exercise the real continuation entry without constructing or stepping a World."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from random import Random
from types import SimpleNamespace as Row
from unittest import TestCase, mock

from experiments import al02_depletion_producer as producer, executed_heredity as frozen
from experiments.al02_depletion_checkpoint import COUNTERS, _canonical, encode_checkpoint, restore_checkpoint
from experiments.al02_depletion_projection import project_depletion
from tests import test_al02_depletion_integration as fixture


def settled_fixture():
    def records(rows):
        return [dict(zip(fixture._PAIR_COLUMNS[row[0]], deepcopy(row[1:]), strict=True))
                for row in rows]

    state = deepcopy(fixture._PAIR_STATE)
    actors = state.pop('organisms')
    for actor in actors:
        for field in ('tape', 'nursery'):
            actor[field] = [Row(op=op, material_unit=unit) for op, unit in actor[field]]
    state.update(organisms={actor['organism_id']: Row(**actor) for actor in actors},
                 events=records(fixture._PAIR_PREFIX), births=records(fixture._PAIR_BIRTHS))
    config = dict(seed=42, variant='mutating', copy_enabled=True, mutation_rate=0.08,
                  material_units=256, population_limit=64, genesis_energy=604,
                  genesis_material=256, initial_food_a=12, initial_food_b=18)
    rng = Random(42)
    for _ in range(31):
        if rng.random() < 0.08:
            rng.randrange(5)
    return Row(**config, **state, rng=rng), config


class RestoreEntryTests(TestCase):
    def setUp(self):
        for name in ('__init__', 'execute_one', 'next_actor'):
            guard = mock.patch.object(frozen.World, name, side_effect=AssertionError(
                f'No-World barrier: {name}'))
            guard.start()
            self.addCleanup(guard.stop)
        world, self.config = settled_fixture()
        self.source = Path(frozen.__file__).read_bytes()
        self.config_pin = sha256(_canonical(self.config)).hexdigest()
        self.raw = project_depletion(world, self.source, self.config_pin)
        self.pin = sha256(self.raw).hexdigest()
        self.state, self.rng = restore_checkpoint(self.raw, self.pin)

    def test_real_restore_and_both_branch_starts(self):
        entry = producer.EscrowContinuation.restore
        source = Path(producer.__file__).resolve()
        self.assertEqual(Path(entry.__func__.__code__.co_filename).resolve(), source)
        self.assertEqual(source, Path(__file__).resolve().parents[1] /
                         'experiments/al02_depletion_producer.py')
        accessible, sequestered = (entry(self.raw, self.pin, 42, role)
                                  for role in ('accessible', 'sequestered'))
        for branch, accessible_b, escrow in ((accessible, 10, 0), (sequestered, 0, 10)):
            with self.subTest(escrow=escrow):
                self.assertEqual({key: getattr(branch, key) for key in self.config}, self.config)
                actual = dict(config_sha256=self.config_pin, tick=branch.tick_count,
                              free_units=sorted(branch.free_units),
                              counters={key: getattr(branch, key) for key in COUNTERS})
                for key in ('last_actor', 'next_organism_id', 'food_a', 'food_b',
                            'escrow_b', 'heat', 'events', 'births'):
                    actual[key] = getattr(branch, key)
                actual['organisms'] = []
                self.assertEqual(list(branch.organisms), sorted(branch.organisms))
                for identity, actor in branch.organisms.items():
                    self.assertEqual(identity, actor.organism_id)
                    row = asdict(actor)
                    for name in ('tape', 'nursery'):
                        row[name] = [[gene.op, gene.material_unit] for gene in getattr(actor, name)]
                    actual['organisms'].append(row)
                expected = dict(self.state, food_b=accessible_b, escrow_b=escrow)
                self.assertEqual(actual, expected)
                self.assertEqual(branch.rng.getstate(), self.rng.getstate())
                self.assertEqual(encode_checkpoint(actual, branch.rng),
                                 encode_checkpoint(expected, self.rng))
                self.assertEqual(branch.assert_invariants(), (0, 0))
                summary = branch.run(maximum_ticks=self.state['tick'])
                self.assertEqual((summary['ticks'], summary['remaining_food_b'],
                                  summary['escrow_b'], summary['consumed_food_b']),
                                 (self.state['tick'], accessible_b, escrow, 8))
                self.assertEqual(branch.rng.getstate(), self.rng.getstate())
        self.assertEqual(project_depletion(accessible, self.source, self.config_pin), self.raw)
        self.assertIsNot(accessible.rng, sequestered.rng)
        for field in ('events', 'births', 'free_units', 'organisms'):
            self.assertIsNot(getattr(accessible, field), getattr(sequestered, field))
        for identity, actor in accessible.organisms.items():
            other = sequestered.organisms[identity]
            self.assertIsNot(actor, other)
            self.assertIsNot(actor.nursery, other.nursery)
        accessible.events[0]['kind'] = 'TEST MUTATION'
        self.assertEqual(sequestered.events, self.state['events'])
        print(f'restore_entry={source} sha256={sha256(source.read_bytes()).hexdigest()} '
              f'checkpoint_sha256={self.pin} tick={self.state["tick"]} '
              'branches=accessible,sequestered dispatch=blocked', flush=True)

    def test_corrupt_checkpoint_and_wrong_scope(self):
        restore = producer.EscrowContinuation.restore
        for raw, pin, seed, role, error in (
            (self.raw, self.pin, 42, 'wrong', 'Unknown branch role'),
            (self.raw, self.pin, 43, 'accessible', 'Configuration pin mismatch'),
            (self.raw, '0'*64, 42, 'accessible', 'Checkpoint pin mismatch'),
        ):
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                restore(raw, pin, seed, role)
