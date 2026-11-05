import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('adapter', Path(__file__).resolve().parents[1]/'tools/eka1_feedback_adapter.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)


def fixture(bit=0, arg=0, slot=0):
    words = [18, 0, 0] * 9; words[3*slot:3*slot+3] = [1, arg, 0]
    reg = [7, 9]; reg[arg % 2] = bit
    original = {'entities': {'1': {'code': [[v, i] for i, v in enumerate(words)],
                                 'pc': (slot+1) % 9, 'registers': reg,
                                 'feedback': bit, 'memory': [0]*8,
                                 'energy': 11, 'nursery': []},
                             '2': {'registers': [3, 4]}},
                'tick': 100, 'heat': 44, 'food': {'64': [0, 0]}}
    binding = {'schema': 'ORA-EKA1-OFFLINE-READ-BINDING-v1', 'source_sha256': a.SOURCE,
               'original_world_id': 'synthetic-not-world', 'actor': '1',
               'decoded': [1, arg, 0], 'original_state_sha256': a.digest(original),
               'original_read_receipt_sha256': 'a'*64,
               'branch_ids': {'true': 'proposed-true', 'identity_sham': 'proposed-sham', 'xor1': 'proposed-xor'}}
    return original, binding


class AdapterTests(unittest.TestCase):
    def test_all_bits_destinations_slots_and_roles(self):
        for bit in [0, 1]:
            for arg in range(32):
                for slot in range(9):
                    original, binding = fixture(bit, arg, slot); saved = copy.deepcopy(original)
                    for arm in ['true', 'identity_sham', 'xor1']:
                        derived, receipt = a.adapt(original, binding, arm)
                        a.verify(original, derived, binding, arm, receipt)
                        self.assertEqual(derived['entities']['1']['registers'][arg%2], bit ^ (arm=='xor1'))
                        self.assertEqual(original, saved)
                        self.assertFalse(receipt['execution_authorized'])
                        self.assertFalse(receipt['authentic_original_history_verified'])

    def test_context_tampering_refused(self):
        for field, value in [('source_sha256', 'b'*64), ('original_state_sha256', 'b'*64), ('decoded', [2,0,0]), ('actor', 'missing')]:
            original, b = fixture(); b[field] = value
            with self.assertRaises(ValueError): a.adapt(original, b, 'xor1')

    def test_forged_authority_refused(self):
        original, b = fixture(); derived, r = a.adapt(original, b, 'xor1')
        for field in ['execution_authorized', 'authentic_original_history_verified', 'ordinary_read_charge_verified', 'derived_checkpoint_authority_granted']:
            bad = copy.deepcopy(r); bad[field] = True
            with self.assertRaises(ValueError): a.verify(original, derived, b, 'xor1', bad)

    def test_all_nontarget_collateral_refused(self):
        for field in ['tick', 'heat', 'food']:
            original, b = fixture(); derived, r = a.adapt(original, b, 'xor1'); derived[field] = None
            with self.assertRaises(ValueError): a.verify(original, derived, b, 'xor1', r)
        for field in ['energy', 'pc', 'feedback', 'memory', 'code', 'nursery']:
            original, b = fixture(); derived, r = a.adapt(original, b, 'xor1'); derived['entities']['1'][field] = None
            with self.assertRaises(ValueError): a.verify(original, derived, b, 'xor1', r)

    def test_alias_cannot_modify_other_actor(self):
        original, b = fixture(); original['entities']['2']['registers'] = original['entities']['1']['registers']; b['original_state_sha256'] = a.digest(original)
        derived, r = a.adapt(original, b, 'xor1')
        self.assertEqual(derived['entities']['2']['registers'], original['entities']['2']['registers'])
        derived['entities']['2']['registers'][0] ^= 1
        with self.assertRaises(ValueError): a.verify(original, derived, b, 'xor1', r)

    def test_bool_feedback_and_untruthful_original_refused(self):
        for value in [True, 2]:
            original, b = fixture(); original['entities']['1']['feedback'] = value; b['original_state_sha256'] = a.digest(original)
            with self.assertRaises(ValueError): a.adapt(original, b, 'true')
        original, b = fixture(); original['entities']['1']['registers'][0] = 1; b['original_state_sha256'] = a.digest(original)
        with self.assertRaises(ValueError): a.adapt(original, b, 'true')

    def test_wrong_slot_and_extra_binding_refused(self):
        original, b = fixture(); original['entities']['1']['pc'] = 2; b['original_state_sha256'] = a.digest(original)
        with self.assertRaises(ValueError): a.adapt(original, b, 'true')

    def test_branch_label_collision_and_original_reuse_refused(self):
        for label in ['proposed-true', 'synthetic-not-world']:
            original, b = fixture(); b['branch_ids']['xor1'] = label
            with self.assertRaises(ValueError): a.adapt(original, b, 'xor1')
        original, b = fixture(); b['execution_authorized'] = True
        with self.assertRaises(ValueError): a.adapt(original, b, 'true')

    def test_bad_json_and_event_history_refused(self):
        for value in [float('nan'), (1, 2), {1: 'x'}]:
            with self.assertRaises(ValueError): a.canonical(value)
        original, b = fixture(); original['events'] = []; b['original_state_sha256'] = a.digest(original)
        with self.assertRaises(ValueError): a.adapt(original, b, 'true')


if __name__ == '__main__': unittest.main()
