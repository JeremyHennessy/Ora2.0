"""Engineering checks. Never require favorable scientific outcomes in unit tests."""
import copy
import unittest

from experiments import digital_cognition01 as source
from experiments import digital_cognition01_referee as referee


class Cognition01PreparedTests(unittest.TestCase):
    def test_prospectively_frozen_sizes_and_domains(self):
        self.assertEqual((source.HORIZON, source.SITES, source.RATE), (256, 8, 2))
        self.assertEqual(source.PRIMARY, tuple(range(78000, 78008)))
        self.assertEqual(source.UNSEEN, tuple(range(78200, 78208)))
        self.assertEqual(len(source.ARMS), 7)
        for bad_seed in (77999, 78008, 78208, True):
            with self.assertRaises(ValueError):
                source.run_trial(bad_seed, 'intact')

    def test_all_sites_reverse_without_a_hidden_policy_input(self):
        for site in range(8):
            self.assertEqual(source.target_port(78000, site, 0), source.target_port(78000, site, 127))
            self.assertNotEqual(source.target_port(78000, site, 127), source.target_port(78000, site, 128))
        p = source.Policy('intact', [0] * 8)
        self.assertEqual(set(p.__dict__), {'arm', 'fixed_ports', 'weights', 'latest'})
        # Policy has no seed/world/target/time/epoch parameter or hidden closure.
        self.assertEqual(p.choose(0, tie=1, explore=False, noise=0), 1)
        p.learn(0, chosen_port=1, feedback=0)
        self.assertEqual(p.choose(0, tie=1, explore=False, noise=1), 0)

    def test_memory_channel_intervention_and_costs(self):
        for arm in source.ARMS:
            p = source.Policy(arm, [0] * 8)
            p.learn(0, chosen_port=1, feedback=1)
            if arm == 'intact':
                self.assertEqual(p.weights, [2] + [0] * 7)
            elif arm == 'misbound_history':
                self.assertEqual(p.weights, [0, 2] + [0] * 6)
            else:
                self.assertEqual(p.weights, [0] * 8)
        for arm in source.ARMS:
            row = source.run_trial(78000, arm)
            self.assertEqual(len(row['events']), 256)
            self.assertEqual({e['cost'] for e in row['events'] if e['port'] is not None}, {3})
            self.assertEqual(len(referee.audit_trial(row)['audit_sha256']), 64)
            for step in row['events']:
                self.assertEqual(step['energy'] + step['heat'], 64 + 12 * (step['tick'] + 1))

    def test_full_replay_and_matched_external_draws(self):
        rows = [source.run_trial(78001, mode) for mode in source.ARMS]
        self.assertEqual([r['sha256'] for r in rows],
                         [source.run_trial(78001, mode)['sha256'] for mode in source.ARMS])
        for tick in range(256):
            keys = ('site', 'target', 'tie', 'explore', 'noise')
            reference = tuple(rows[0]['events'][tick][key] for key in keys)
            self.assertTrue(all(tuple(r['events'][tick][key] for key in keys) == reference for r in rows))

    def test_independent_referee_rejects_data_forgery_even_if_rehashed(self):
        original = source.run_trial(78002, 'intact')
        for tamper in ('target', 'port', 'feedback', 'energy', 'heat', 'memory_after'):
            damaged = copy.deepcopy(original)
            v = damaged['events'][5][tamper]
            damaged['events'][5][tamper] = (v + 1) % 2 if type(v) is int else [99] * 8
            damaged['sha256'] = source.digest({k: v for k, v in damaged.items() if k != 'sha256'})
            with self.assertRaises(AssertionError, msg=tamper):
                referee.audit_trial(damaged)

    def test_complete_banks_referee_and_replay(self):
        trials, summary = source.run_panel()
        checked = referee.audit_panel(trials)
        self.assertTrue(checked['verified'])
        self.assertEqual((checked['trials'], checked['opportunities']), (112, 28672))
        self.assertEqual(checked['banks'], summary['banks'])
        self.assertEqual(checked['registered_pass'], summary['registered_pass'])
        self.assertEqual(sum(row['qualifying'] for row in summary['rows']), sum(summary['banks'].values()))
        self.assertEqual(len(summary['rows']), 16)


if __name__ == '__main__':
    unittest.main()
