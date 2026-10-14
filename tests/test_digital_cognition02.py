"""Tests mechanism and custody, never assumes a favorable research conclusion."""
import copy
import unittest

from experiments import digital_cognition01 as old
from experiments import digital_cognition02 as v2
from experiments import digital_cognition02_referee as judge


class Cognition02Tests(unittest.TestCase):
    def test_fresh_banks_and_immutable_source_dependent_environment(self):
        self.assertEqual(v2.PRIMARY, tuple(range(78400, 78408)))
        self.assertEqual(v2.UNSEEN, tuple(range(78600, 78608)))
        self.assertTrue(set(v2.PRIMARY + v2.UNSEEN).isdisjoint(old.PRIMARY + old.UNSEEN))
        self.assertEqual(len(v2.ARMS), 8)
        for seed in (78400, 78607):
            with self.assertRaises(ValueError):
                v2.run_trial(seed, 'intact')
            with self.assertRaises(ValueError):
                v2.run_trial(seed, 'no_such_policy')

    def test_first_failure_erases_rapid_memory_but_not_historical(self):
        quick = v2.Policy('quick_memory', [0] * 8)
        historic = v2.Policy('historic_memory', [0] * 8)
        for p in (quick, historic):
            for _ in range(9):
                p.learn(0, 1, 1)
        self.assertEqual((quick.weights[0], historic.weights[0]), (2, 12))
        quick.learn(0, 1, 0)
        historic.learn(0, 1, 0)
        self.assertEqual((quick.weights[0], historic.weights[0]), (0, 10))
        self.assertEqual(quick.choose(0, 0, False, 1), 0)
        self.assertEqual(historic.choose(0, 0, False, 1), 1)

    def test_all_arms_identical_exogenous_inputs_and_paid_debits(self):
        histories = [v2.run_trial(78400, arm) for arm in v2.ARMS]
        for h in histories:
            self.assertEqual(h['sha256'], v2.run_trial(78400, h['arm'])['sha256'])
            judge.audit_trial(h)
            self.assertEqual(len(h['events']), 256)
        for t in range(256):
            observed = [(r['events'][t]['site'], r['events'][t]['target'],
                         r['events'][t]['tie'], r['events'][t]['explore'],
                         r['events'][t]['noise']) for r in histories]
            self.assertEqual(len(set(observed)), 1)
            self.assertTrue(all(r['events'][t]['cost'] in (0, 3) for r in histories))

    def test_referee_rejects_coherently_rehashed_wrong_feedback_and_memory(self):
        original = v2.run_trial(78401, 'quick_memory')
        for key in ('target', 'port', 'feedback', 'memory_after', 'heat'):
            bad = copy.deepcopy(original)
            cell = bad['events'][3][key]
            bad['events'][3][key] = 99 if isinstance(cell, int) else [99] * 8
            bad['sha256'] = old.digest({k: val for k, val in bad.items() if k != 'sha256'})
            with self.assertRaises(AssertionError):
                judge.audit_trial(bad)

    def test_full_frozen_two_bank_assay_agrees_with_separate_referee(self):
        trials, summary = v2.run_panel()
        referee = judge.audit_panel(trials)
        self.assertEqual((referee['trials'], referee['opportunities']), (128, 32768))
        self.assertTrue(referee['verified'])
        self.assertEqual(referee['banks'], summary['banks'])
        self.assertEqual(referee['registered_pass'], summary['registered_pass'])


if __name__ == '__main__':
    unittest.main()
