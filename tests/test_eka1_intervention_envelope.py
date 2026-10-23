import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('envelope', Path(__file__).resolve().parents[1]/'tools/eka1_intervention_envelope.py')
envelope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(envelope)


def fixture():
    # Deliberately incomplete synthetic JSON. Never a restorable World receipt.
    return {'entities': {'1': {'memory': list(range(8)), 'pc': 3, 'energy': 12,
                             'registers': [1, 0], 'code': [[4, 0]], 'nursery': []},
                         '2': {'memory': [0]*8}},
            'food': {'0': [0, 0]}, 'tick': 7, 'heat': 2, 'turns': {'1': 3}}


class DeltaTests(unittest.TestCase):
    def test_all_addresses_values_and_inputs_preserved(self):
        for cell in range(8):
            for value in range(16):
                before = fixture(); saved = copy.deepcopy(before); after = copy.deepcopy(before)
                after['entities']['1']['memory'][cell] = value
                arm = 'sham' if cell == value else 'single_cell_lesion'
                r = envelope.validate_delta(before, after, actor='1', cell=cell, value=value, arm=arm)
                self.assertEqual(before, saved)
                self.assertFalse(r['execution_authorized'])
                self.assertFalse(r['causal_assay_qualified'])

    def test_every_control_field_collateral_change_rejected(self):
        for field in ['pc', 'energy', 'registers', 'code', 'nursery']:
            a = fixture(); b = copy.deepcopy(a); b['entities']['1']['memory'][0] = 15
            b['entities']['1'][field] = None
            with self.assertRaises(ValueError):
                envelope.validate_delta(a, b, actor='1', cell=0, value=15, arm='single_cell_lesion')

    def test_environment_and_other_actor_changes_rejected(self):
        for field in ['food', 'tick', 'heat', 'turns']:
            a = fixture(); b = copy.deepcopy(a); b[field] = None
            with self.assertRaises(ValueError):
                envelope.validate_delta(a, b, actor='1', cell=0, value=0, arm='sham')
        a = fixture(); b = copy.deepcopy(a); b['entities']['2']['memory'][0] = 1
        with self.assertRaises(ValueError):
            envelope.validate_delta(a, b, actor='1', cell=0, value=0, arm='sham')

    def test_bool_cannot_masquerade_as_integer_or_unchanged_state(self):
        a = fixture(); b = copy.deepcopy(a); b['entities']['1']['memory'][0] = False
        with self.assertRaises(ValueError):
            envelope.validate_delta(a, b, actor='1', cell=0, value=0, arm='sham')
        with self.assertRaises(ValueError):
            envelope.validate_delta(a, a, actor='1', cell=True, value=1, arm='sham')

    def test_empty_lesion_or_changed_sham_rejected(self):
        a = fixture()
        for arm, value in [('single_cell_lesion', 0), ('sham', 1), ('intact', 1)]:
            with self.assertRaises(ValueError):
                envelope.validate_delta(a, a, actor='1', cell=0, value=value, arm=arm)

    def test_forged_extra_receipt_or_second_cell_rejected(self):
        for extra in ['receipt', 'memory']:
            a = fixture(); b = copy.deepcopy(a); b['entities']['1']['memory'][0] = 15
            if extra == 'receipt': b['execution_authorized'] = True
            else: b['entities']['1']['memory'][1] = 15
            with self.assertRaises(ValueError):
                envelope.validate_delta(a, b, actor='1', cell=0, value=15, arm='single_cell_lesion')

    def test_shared_python_alias_cannot_hide_second_actor_delta(self):
        a = fixture(); a['entities']['2']['memory'] = a['entities']['1']['memory']
        b = copy.deepcopy(a); b['entities']['1']['memory'][0] = 15
        self.assertEqual(b['entities']['2']['memory'][0], 15)
        with self.assertRaises(ValueError):
            envelope.validate_delta(a, b, actor='1', cell=0, value=15, arm='single_cell_lesion')
        self.assertEqual(a['entities']['1']['memory'][0], 0)


if __name__ == '__main__':
    unittest.main()
