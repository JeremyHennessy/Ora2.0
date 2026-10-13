"""Stub histories only: no fresh seed context/hash/World execution."""
import unittest
from unittest.mock import patch
from experiments import digital_firstborn63 as g
from experiments import digital_informative_exposure23 as substrate
from experiments.digital_transfer57 import PROGRAM, ROSTER, choice
from experiments.digital_informative_exposure23_interpret import clone, h
import json
from pathlib import Path


class Genesis(unittest.TestCase):
    def setUp(self):
        self.world = patch.object(substrate, 'World', side_effect=AssertionError('World forbidden'))
        self.world.start(); self.addCleanup(self.world.stop)
        self.manifest = json.loads((Path(__file__).resolve().parents[1]/'docs/DIGITAL-TRANSFER-57-SOURCE.json').read_bytes())['summary']
        self.registry = patch.object(substrate, 'PROGRAMS', {})
        self.registry.start(); self.addCleanup(self.registry.stop)
        self.before = h(substrate.PROGRAMS)

    def history(self, seed, route, mode):
        return dict(seed=seed, route=route, mode=mode,
                    genesis_program=clone(substrate.PROGRAMS[route]), stub=True)

    def generate(self, mode='faithful', arm='withheld', source=None):
        with patch.object(substrate, 'history', side_effect=self.history) as call:
            out = g.generate(64000, mode, arm, source, self.manifest)
            self.assertEqual(call.call_count, 1)
        self.assertEqual(h(substrate.PROGRAMS), self.before)
        return out

    def test_disclosed_baseline_both_modes(self):
        for mode in g.MODES:
            out = self.generate(mode)
            self.assertEqual(out['history']['genesis_program'], PROGRAM)
            self.assertIsNone(out['source'])
            self.assertEqual(out['version'], g.VERSION)
            self.assertEqual(out['source_manifest_hash'], g.SOURCE_HASH)

    def test_all_enrolled_ancestries_without_selection(self):
        for source in ROSTER:
            out = self.generate('mutating', 'retained', source)
            program, origin = choice('retained', source, self.manifest)
            self.assertEqual(out['source'], origin)
            self.assertEqual(out['history']['genesis_program'], program)

    def test_existing_unique_alias_reused(self):
        substrate.PROGRAMS['existing'] = clone(PROGRAM)
        self.before = h(substrate.PROGRAMS)
        self.assertEqual(self.generate()['history']['route'], 'existing')

    def test_duplicate_alias_refused_before_history(self):
        substrate.PROGRAMS.update(a=clone(PROGRAM), b=clone(PROGRAM))
        with patch.object(substrate, 'history', side_effect=AssertionError('history forbidden')) as call:
            with self.assertRaises(AssertionError): g.generate(64000, 'faithful', 'withheld', None, self.manifest)
            call.assert_not_called()

    def test_reserved_route_collision_refused(self):
        substrate.PROGRAMS[g.ROUTE] = clone(PROGRAM)
        before = h(substrate.PROGRAMS)
        with self.assertRaises(AssertionError): g.generate(64000, 'faithful', 'withheld', None, self.manifest)
        self.assertEqual(h(substrate.PROGRAMS), before)

    def test_invalid_identity_never_calls_history(self):
        with patch.object(substrate, 'history', side_effect=AssertionError('history forbidden')) as call:
            for seed in (True, 64100, 64300, 55000, -1, '64000'):
                with self.assertRaises(AssertionError): g.generate(seed, 'faithful', 'withheld', None, self.manifest)
            for mode in ('learning', None, True):
                with self.assertRaises(AssertionError): g.generate(64000, mode, 'withheld', None, self.manifest)
            for arm, source in (('unknown', None), ('withheld', ROSTER[0]), ('retained', (55020, 99)), ('retained', list(ROSTER[0]))):
                with self.assertRaises(AssertionError): g.generate(64000, 'faithful', arm, source, self.manifest)
            call.assert_not_called()

    def test_corrupt_manifest_refused_before_history(self):
        manifest = clone(self.manifest); manifest['eligible'] = 150
        with patch.object(substrate, 'history') as call:
            with self.assertRaises(AssertionError): g.generate(64000, 'faithful', 'withheld', None, manifest)
            call.assert_not_called()

    def test_history_failure_cleans_installed_alias(self):
        with patch.object(substrate, 'history', side_effect=RuntimeError('preserved native failure')):
            with self.assertRaises(RuntimeError): g.generate(64000, 'faithful', 'withheld', None, self.manifest)
        self.assertEqual(h(substrate.PROGRAMS), self.before)

    def test_failure_does_not_remove_existing_alias(self):
        substrate.PROGRAMS['existing'] = clone(PROGRAM); before = h(substrate.PROGRAMS)
        with patch.object(substrate, 'history', side_effect=RuntimeError('failure')):
            with self.assertRaises(RuntimeError): g.generate(64000, 'faithful', 'withheld', None, self.manifest)
        self.assertEqual(h(substrate.PROGRAMS), before)

    def test_mislabeled_output_refused_and_cleanup(self):
        for key, value in (('seed', 64100), ('mode', 'mutating'), ('route', 'other'), ('genesis_program', [[17,0,0]])):
            def bad(seed, route, mode):
                row = self.history(seed, route, mode); row[key] = value; return row
            with patch.object(substrate, 'history', side_effect=bad):
                with self.assertRaises(AssertionError): g.generate(64000, 'faithful', 'withheld', None, self.manifest)
            self.assertEqual(h(substrate.PROGRAMS), self.before)

    def test_registry_tampering_detected(self):
        def bad(seed, route, mode):
            row = self.history(seed, route, mode); substrate.PROGRAMS['unauthorized'] = [[17,0,0]]; return row
        with patch.object(substrate, 'history', side_effect=bad):
            with self.assertRaises(AssertionError): g.generate(64000, 'faithful', 'withheld', None, self.manifest)
        self.assertNotIn(g.ROUTE, substrate.PROGRAMS)


if __name__ == '__main__': unittest.main()
