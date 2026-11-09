import hashlib
import json
import random
import unittest
from copy import deepcopy
from unittest.mock import patch

from experiments import al02_depletion_checkpoint as codec


def fixture():
    return dict(config_sha256='a' * 64, tick=76, last_actor=0, next_organism_id=1,
                organisms=[dict(organism_id=0, tape=[[0, 0], [2, 1], [3, 2], [4, 3]],
                                energy=44, generation=0, parent_id=None, born_tick=0,
                                pc=1, read_head=1, nursery=[[0, 4]], nursery_write_ids=[0])],
                free_units=list(range(5, 256)), food_a=0, food_b=15, escrow_b=0,
                heat=260, events=[dict(kind='EXEC', outcome='ate_b') for _ in range(3)],
                births=[], counters=dict.fromkeys(codec.COUNTERS, 0))


def restore(raw):
    return codec.restore_checkpoint(raw, hashlib.sha256(raw).hexdigest())


class CheckpointTests(unittest.TestCase):
    def test_history_must_roundtrip_without_type_coercion(self):
        for invalid in ((1, 2), {1: 'integer key'}):
            state = fixture()
            state['events'][0]['extra'] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                codec.encode_checkpoint(state, random.Random(0))

    def test_real_rng_roundtrip_without_reseeding(self):
        rng = random.Random(0)  # Fixed unit fixture, not a scientific context.
        rng.gauss(0, 1)  # Leave a cached Gaussian in the serialized state.
        state = fixture()
        raw = codec.encode_checkpoint(state, rng)
        with patch.object(random.Random, 'seed', side_effect=AssertionError('reseed')):
            decoded, restored = restore(raw)
        self.assertEqual(decoded, state)
        self.assertEqual(restored.getstate(), rng.getstate())
        self.assertEqual(restored.gauss(0, 1), rng.gauss(0, 1))
        for _ in range(700):
            self.assertEqual(restored.random(), rng.random())
            self.assertEqual(restored.randrange(5), rng.randrange(5))

    def test_rehashed_invalid_rng_rejected(self):
        raw = codec.encode_checkpoint(fixture(), random.Random(0))
        for index, bad in ((0, True), (17, -1), (624, 625)):
            value = json.loads(raw)
            value['rng'][1][index] = bad
            with self.subTest(index=index), self.assertRaises(ValueError):
                restore(codec._canonical(value))
        with self.assertRaises(ValueError):
            codec.restore_checkpoint(raw, '0' * 64)
        with self.assertRaises(ValueError):
            restore(raw + b' ')

    def test_escrow_detached_and_preserves_rng_and_meal_count(self):
        source = fixture()
        original = deepcopy(source)
        rng = random.Random(0)
        result = codec.sequester_b(source)
        self.assertEqual(source, original)
        self.assertEqual(result, dict(original, food_b=0, escrow_b=15))
        decoded, resumed = restore(codec.encode_checkpoint(result, rng))
        self.assertEqual(decoded, result)
        self.assertEqual(resumed.getstate(), rng.getstate())
        result['organisms'][0]['pc'] = 3
        self.assertEqual(source, original)

    def test_corrupt_actor_scheduler_ledger_and_meals_rejected(self):
        rng = random.Random(0)
        changes = (('last_actor', 1), ('free_units', list(range(4, 255))),
                   ('heat', 261), ('events', [dict(kind='EXEC', outcome='ate_b')]))
        for key, bad in changes:
            with self.subTest(key=key), self.assertRaises(ValueError):
                codec.encode_checkpoint(dict(fixture(), **{key: bad}), rng)
        state = fixture()
        state['organisms'][0]['pc'] = 5
        with self.assertRaises(ValueError):
            codec.encode_checkpoint(state, rng)
