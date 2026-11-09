from hashlib import sha256
from pathlib import Path
from random import Random
from types import SimpleNamespace as Row
from unittest import TestCase
from unittest.mock import patch
import sys

from experiments import al02_one_pair as pair
from experiments.al02_depletion_checkpoint import COUNTERS, _canonical, restore_checkpoint
from experiments.al02_one_pair_job import run


class OnePairTests(TestCase):
    def test_context_rejected_before_constructor(self):
        with patch.object(pair.frozen, 'World') as constructor:
            with self.assertRaisesRegex(ValueError, 'context'):
                pair.produce(pair.CONTEXT, pair.CONTEXT_SHA256, pair.SEED + 1, b'')
            constructor.assert_not_called()

    def test_inert_terminal_wiring_and_independent_consumer(self):
        prefix = Row(food_a=12, food_b=18, heat=4, organisms={}, tick_count=1,
                     last_actor=0, next_organism_id=1, free_units=set(range(256)),
                     events=[dict(kind='GENESIS'), dict(kind='DEATH')], births=[],
                     rng=Random(42), **dict.fromkeys(COUNTERS, 0))
        source = Path(pair.frozen.__file__).read_bytes()
        with patch.object(pair.frozen, 'World', return_value=prefix):
            raw = pair.produce(pair.CONTEXT, pair.CONTEXT_SHA256, pair.SEED, source)
        import json
        payload = json.loads(raw)
        state, rng = restore_checkpoint(payload['checkpoint'].encode('ascii'),
                                        payload['checkpoint_sha256'])
        self.assertEqual(state['food_a'], 12)
        self.assertEqual(rng.getstate(), prefix.rng.getstate())
        self.assertEqual(set(payload['branches']), set(pair.ROLES))
        self.assertTrue(all(not arm['events'] for arm in payload['branches'].values()))
        # Structurally valid transport is insufficient when the historical events are false.
        with self.assertRaisesRegex(ValueError, 'Wrong genesis'):
            pair.verify(raw)
        with self.assertRaisesRegex(ValueError, 'format or context'):
            pair.verify(_canonical(dict(payload, context_sha256='0'*64)))

    def test_inert_fork_uses_common_pin_and_returns_only_suffixes(self):
        prefix = Row(food_a=1, organisms={0: object()}, tick_count=114,
                     events=[dict(kind='PREFIX')])
        def settle_last_a():
            prefix.tick_count += 1
            prefix.food_a = 0
            prefix.events.append(dict(kind='EXEC', outcome='ate_a'))
        prefix.execute_one = settle_last_a
        common = b'{"inert":"checkpoint"}'
        arms = []
        for role in pair.ROLES:
            arm = Row(events=[dict(kind='PREFIX'), dict(kind='EXEC', outcome='ate_a')])
            def finish(arm=arm, role=role):
                arm.events.append(dict(kind='SUFFIX', role=role))
            arm.run = finish
            arms.append(arm)
        with patch.object(pair.frozen, 'World', return_value=prefix), \
             patch.object(pair, 'project_depletion', return_value=common) as project, \
             patch.object(pair.EscrowContinuation, 'restore', side_effect=arms) as restore:
            raw = pair.produce(pair.CONTEXT, pair.CONTEXT_SHA256, pair.SEED,
                               Path(pair.frozen.__file__).read_bytes())
        self.assertEqual(prefix.tick_count, 115)
        project.assert_called_once()
        import json
        branches = json.loads(raw)['branches']
        for role, invocation in zip(pair.ROLES, restore.call_args_list, strict=True):
            self.assertEqual(invocation.args, (common, sha256(common).hexdigest(), pair.SEED, role))
            self.assertEqual(branches[role]['events'], [dict(kind='SUFFIX', role=role)])

    def test_windows_fake_worker_and_overflow(self):
        cwd = Path(__file__).resolve().parents[1]
        data, result = run([sys.executable, '-B', '-S', '-c', 'print(123)'], cwd)
        self.assertTrue(result['accepted'], result)
        self.assertEqual(data.strip(), b'123')
        self.assertEqual(result['final']['started_processes'], 2)
        self.assertGreaterEqual(result['final']['kernel_ticks'], 0)
        self.assertTrue(result['observed_closed'] and result['eof'])
        data, result = run([sys.executable, '-B', '-S', '-c',
                            'import sys,time; sys.stdout.buffer.write(b"x"*1200000);'
                            'sys.stdout.flush(); time.sleep(30)'], cwd)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['reason'], 'output_overflow')
        self.assertEqual(len(data), pair.MAX_OUTPUT)
        self.assertTrue(result['observed_closed'] and result['eof'], result)
