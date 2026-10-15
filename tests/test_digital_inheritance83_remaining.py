"""Remaining-role NON-PHYSICS dependency fixtures; never create a World."""
import copy
import hashlib
import unittest
from unittest.mock import patch

from experiments import digital_inheritance83_custody as old
from experiments import digital_inheritance83_remaining as remaining


class Remaining(unittest.TestCase):
    def test_cached_software_reserve_and_config_refused_before_world(self):
        import sys
        before = 'experiments.digital_inheritance83_world' in sys.modules
        for seed in (*remaining.CACHED, 2100080, 2140080, 1009000, 1009200):
            req = dict(configuration=copy.deepcopy(old.CONFIG), role=f'original:{seed}:variation:generate', kind='generate', input=None)
            with self.subTest(seed=seed), self.assertRaises(AssertionError): remaining.guard(req)
        req = dict(configuration=copy.deepcopy(old.CONFIG), role=remaining.plan()[0], kind='generate', input=None)
        remaining.guard(req)
        req['configuration']['horizon'] = 1
        with self.assertRaisesRegex(AssertionError, 'configuration'): remaining.guard(req)
        self.assertEqual(before, 'experiments.digital_inheritance83_world' in sys.modules)

    def test_exact_role_and_allocation_denominators(self):
        roles = remaining.plan()
        self.assertEqual(len(roles), len(set(roles)))
        self.assertEqual(len(roles), 209)
        self.assertEqual(sum(r.startswith('original:') and r.endswith(':generate') for r in roles), 65)
        self.assertEqual(sum(r.startswith('restored:') for r in roles), 65)
        self.assertEqual(sum(r.endswith(':audit') for r in roles), 65)
        self.assertEqual(sum(r.endswith(':metrics') for r in roles), 13)
        self.assertTrue(all(r not in roles for r in old.plan() if r != 'final:acceptance' and int(r.split(':')[1]) in remaining.CACHED))
        a = remaining.allocations()
        self.assertEqual(sum(n.startswith('native/') for n in a), 213)
        self.assertEqual(sum(n.startswith('cached-metrics/') for n in a), 3)
        self.assertLess(sum(a.values()) + 64*old.M, 12288*old.M)

    def fixtures(self):
        grants = {r: dict(device=1, inode=i, limit=(64 if r.endswith(':generate') else 8)*old.M)
                  for i, r in enumerate(remaining.plan(), 1)}
        cached = {s: dict(path='NON-PHYSICS/'+str(s), extent=1, sha256=str(s)) for s in remaining.CACHED}
        def read(spec, cap):
            return dict(seed=int(spec['sha256']), metrics=[dict(mode=m) for m in old.MODES])
        return grants, cached, read

    def test_all_new_dependencies_and_sixteen_mixed_final_inputs(self):
        grants, cached, read = self.fixtures(); calls = []
        def launch(role, inputs): calls.append((role, inputs)); return {}, {}
        def consume(role, inputs, *unused):
            if role.endswith(':metrics'):
                self.assertEqual([i['mode'] for i in inputs], list(old.MODES))
            if role == 'final:acceptance':
                self.assertEqual(inputs[:3], list(cached.values()))
                self.assertEqual(len(inputs), 16)
            token = role.replace('restored:', 'original:')
            return dict(path='NON-PHYSICS/'+token, extent=1, sha256=hashlib.sha256(token.encode()).hexdigest())
        progress = []
        with patch('experiments.digital_cognitive76_child.validate_grant'), patch('experiments.digital_cognitive76_child.read_spec', read), patch.object(old, 'consume', consume):
            result = remaining.pipeline(launch, {}, grants, cached, progress)
        self.assertEqual(progress, remaining.plan())
        self.assertEqual(len(calls), 209)
        self.assertEqual(result['original_cells'], 80)
        self.assertFalse(result['execution_admission'])

    def test_missing_slots_cache_and_parity_stop_before_next_role(self):
        grants, cached, read = self.fixtures(); calls = []
        def launch(role, inputs): calls.append(role); return {}, {}
        with patch('experiments.digital_cognitive76_child.validate_grant'), patch('experiments.digital_cognitive76_child.read_spec', read):
            missing = dict(grants); missing.pop('final:acceptance')
            with self.assertRaises(AssertionError): remaining.pipeline(launch, {}, missing, cached)
            with self.assertRaises(AssertionError): remaining.pipeline(launch, {}, grants, {})
            self.assertEqual(calls, [])
            with patch.object(old, 'consume', lambda role, *a: dict(path='NON-PHYSICS', extent=1, sha256=role)):
                with self.assertRaisesRegex(AssertionError, 'producer parity'): remaining.pipeline(launch, {}, grants, cached)
        self.assertEqual(len(calls), 2)

    def test_cache_manifest_tampering_refused_without_reading(self):
        with patch.object(remaining, 'pinned_read', side_effect=AssertionError('must not read')) as reader:
            with self.assertRaisesRegex(AssertionError, 'cache manifest'): remaining.cached_batches({'forged': True}, '0'*64)
            reader.assert_not_called()

    def test_qualified_report_omits_only_large_batch_field(self):
        value = dict(verified=True, new_worlds=0, metric_batches=[{'invented': True}])
        summary = dict(verified=True, new_worlds=0)
        remaining.qualified_summary(value, summary)
        for bad in (dict(summary, new_worlds=1), dict(verified=True), dict(summary, extra=True), value):
            with self.assertRaises(AssertionError): remaining.qualified_summary(value, bad)


if __name__ == '__main__': unittest.main()
