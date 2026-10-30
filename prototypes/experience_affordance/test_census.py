"""Small independent semantic fixtures; no census and no historical World imports."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('affordance', Path(__file__).with_name('census.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class Semantics(unittest.TestCase):
    def test_all_cell_addresses_and_values(self):
        for address in range(6):
            for value in range(4):
                genome = value << (2 * address)
                for state in (0, 1):
                    for signal in (0, 1, 2):
                        expected = value if 3 * state + signal == address else 0
                        self.assertEqual(c.transition(genome, state, signal), (expected % 2, expected // 2))

    def test_balanced_schedule_and_no_hidden_target_current_input(self):
        cases = c.episodes(3, (0, 1))
        self.assertEqual(len(cases), 16)
        for code in range(8):
            row = c.evaluate(code, cases, kind='memoryless')
            self.assertEqual(row['correct'] * 2, row['probes'])

    def test_sham_exact_and_erased_memoryless_unchanged(self):
        cases = [((0, 1, 0), 2)]
        for genome in (0, 137, 4095):
            self.assertEqual(c.evaluate(genome, cases), c.evaluate(genome, cases, 'sham'))
        for code in range(8):
            a = c.evaluate(code, cases, kind='memoryless')
            b = c.evaluate(code, cases, 'state_erased', kind='memoryless')
            self.assertEqual(a.pop('external_resets'), 0)
            self.assertEqual(b.pop('external_resets'), 6)
            self.assertEqual(a, b)

    def test_own_attempt_feedback_not_supplied_target(self):
        # Fixed1 attempting target1 sees success1; fixed0 sees failure0.
        for bit, signal in ((0, 0), (1, 1)):
            row = c.evaluate(bit, [((1,), 0)], kind='fixed')
            import hashlib
            stream = hashlib.sha256()
            for x in ((2, bit, 0, 0), (signal, bit, 0, 0), (2, bit, 0, 1), (2, bit, 0, 1)):
                stream.update(bytes(x))
            self.assertEqual(row['trace_sha256'], stream.hexdigest())

    def test_every_dispatch_formation_sense_and_storage_paid(self):
        cases = c.episodes(3, (0, 1))
        row = c.attach_sequences(c.evaluate(0, cases), cases)
        self.assertEqual(row['transitions'], 16 * 3 * 4 + 8 * 3)
        self.assertEqual(row['senses'], 48)
        self.assertEqual(c.cost(row), 16 * 13 + row['transitions'] + 48)
        self.assertEqual(c.cost(row, storage=2) - c.cost(row), 2 * row['transitions'])
        refs = c.references(cases)
        self.assertEqual(len(refs), 12)
        self.assertEqual(refs[0]['row']['transitions'], refs[0]['row']['probes'])
        strong = refs[-1]['row']
        self.assertEqual(strong['correct'], strong['probes'])

    def test_strong_reference_two_sided_reward_interval(self):
        # Cheaper but less accurate requires an upper reward bound, not infinity.
        a = dict(sequences=1, correct=1, transitions=0, senses=0, writes=0)
        b = dict(sequences=1, correct=2, transitions=100, senses=0, writes=0)
        interval = c.reward_interval(a, [dict(row=b, code_bits=12, state_bits=1)])
        self.assertEqual(interval, dict(possible=True, reward_strictly_above='0', reward_strictly_below='100'))


if __name__ == '__main__':
    unittest.main()
