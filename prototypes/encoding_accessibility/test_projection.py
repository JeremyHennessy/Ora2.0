"""New codec/copy unit qualification; no retained-data analysis or controller run."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).with_name('census.py')
spec = importlib.util.spec_from_file_location('encoding_projection', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Projection(unittest.TestCase):
    def test_injective_complete_mappings(self):
        for bits in (6, 8):
            mapped = [m.expand(g, bits) for g in range(1 << bits)]
            self.assertEqual(len(set(mapped)), 1 << bits)
            self.assertTrue(all(0 <= x < 4096 for x in mapped))

    def test_prior_is_explicit_not_hidden_learning(self):
        for g in range(64):
            full = m.expand(g, 6)
            for state in (0, 1):
                for signal in range(3):
                    cell = (full >> (2*(3*state+signal))) & 3
                    self.assertEqual(cell & 1, ((g >> state) & 1) if signal==2 else 0)
                    if signal==2:
                        self.assertEqual(cell >> 1, state)

    def test_single_bit_mutations_preserved(self):
        for bits in (6, 8):
            for g in range(1 << bits):
                for bit in range(bits):
                    self.assertEqual((m.expand(g, bits)^m.expand(g^(1<<bit), bits)).bit_count(), 1)

    def test_copy_requires_all_fees_and_no_future_income(self):
        for bits in (6, 8, 12):
            fee = 2*bits+10
            for budget in range(fee+2):
                x = m.copy_bits(17, bits, budget)
                self.assertEqual(x['complete_fixture_child'], budget >= fee)
                self.assertEqual(x['remaining']+x['heat']+x['child_energy'], budget)
                self.assertEqual(x['free_units']+len(x['copied_bits'])+int(x['complete_fixture_child']), bits+1)
                self.assertGreaterEqual(x['remaining'], 0)

    def test_heritable_bits_and_blank_state_fixture(self):
        for bits in (6, 8, 12):
            for flip in (None, *range(bits)):
                x = m.copy_bits(17, bits, 2*bits+10, flip)
                self.assertEqual(x['child'], 17 ^ (0 if flip is None else 1 << flip))
                self.assertEqual(x['child_memory'], 0)
                self.assertEqual(x['child_energy'], 8)
                self.assertEqual(x['remaining'], 0)

    def test_illegal_inputs_refused(self):
        for value in (-1, 64, True):
            with self.assertRaises(AssertionError):m.expand(value, 6)
        for args in ((True,6,22,None),(0,6,True,None),(0,6,22,True),(0,6,-1,None)):
            with self.assertRaises(AssertionError):m.copy_bits(*args)

    def test_native_guard_reused_byte_identically(self):
        guard = P.with_name('bounded_runner.py').read_bytes()
        self.assertEqual(hashlib.sha256(guard).hexdigest(),
                         '4574f84a3e1945adecf2283b1e0c26d0bacc63ebd2d495de0236634ebe9410d0')


if __name__=='__main__':unittest.main()
