"""Inert synthetic code/record fixtures only; no interpreter or World imports."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.eka_one_shot_recognizer import inspect_birth_bindings, recognize_values


def fixture_values(port=0):
    feedback = 1 - port
    # Existing accepted layout as inert DATA. Never installed in an organism.
    rows = [(6, port, 0), (1, feedback, 0), (8, feedback, 4),
            (7, 0, 5), (4, port, 1), (6, port, 0),
            (10, 0, 0), (12, 0, 0), (7, 0, 5)]
    return [value for row in rows for value in row]


def fixture_birth(values=None):
    values = fixture_values() if values is None else values
    copies = []
    for group in range(9):
        tick = 5 + group * 7
        writes = []
        for index in range(group * 3, group * 3 + 3):
            writes.append(dict(index=index, tick=tick, write_id=index,
                               unit=100 + index, value=values[index],
                               source_unit=27 + index, source_value=values[index],
                               effective_source='parent_copy',
                               effective_source_value=values[index],
                               mutation_draw=8, mutated=False))
        copies.append(dict(actor=0, tick=tick, decoded=[10, 0, 0],
                           outcome='executed', writes=writes))
    state_units = list(range(127, 143))
    child = dict(id=1, parent=0, generation=1, pos=2, pc=0, cue=0,
                 feedback=0, inbox=None, energy=12, registers=[0, 0],
                 memory=[0] * 8, nursery=[], state_units=state_units,
                 code=[[value, 100 + i] for i, value in enumerate(values)])
    birth = dict(child=child, write_ids=list(range(27)), release_energy=2,
                 startup_energy=12,
                 state_formation=[dict(unit=unit, value=2 if i == 14 else 0,
                                       energy=1) for i, unit in enumerate(state_units)])
    return dict(actor=0, tick=70, decoded=[12, 0, 0],
                outcome='executed', birth=birth), copies


class CodeRecognitionTests(unittest.TestCase):
    def test_cold_nonempty_feedback_identifies_both_targets(self):
        # Source Boolean proof, not an instruction interpreter or paid lifetime.
        for port in (0, 1):
            for target in (0, 1):
                values = fixture_values(port)
                roles = recognize_values(values)
                self.assertNotEqual(roles['port_register'], roles['feedback_register'])
                first_port = 0  # Source newborn registers are both zero.
                feedback = int(first_port == target)
                chosen = first_port if feedback else values[14] % 16
                self.assertEqual(chosen % 2, target)

    def test_both_register_orientations(self):
        for port in (0, 1):
            result = recognize_values(fixture_values(port))
            self.assertEqual(result['port_register'], port)
            self.assertEqual(result['feedback_register'], 1 - port)

    def test_every_single_word_alias_against_accepted_origin_classes(self):
        all_values = set(range(32))
        for port in (0, 1):
            registers = {value for value in all_values if value % 2 == port}
            other = all_values - registers
            jump4 = {value for value in all_values if value % 9 == 4}
            jump5 = {value for value in all_values if value % 9 == 5}
            classes = [({6}, registers, all_values), ({1}, other, all_values),
                       ({8}, other, jump4), ({7}, all_values, jump5),
                       ({4}, registers, {1, 17}), ({6}, registers, all_values),
                       ({10}, all_values, all_values),
                       ({12}, all_values, all_values), ({7}, all_values, jump5)]
            for index in range(27):
                for value in range(32):
                    values = fixture_values(port)
                    values[index] = value
                    with self.subTest(port=port, index=index, value=value):
                        self.assertEqual(recognize_values(values) is not None,
                                         value in classes[index // 3][index % 3])

    def test_simultaneous_aliases(self):
        for port in (0, 1):
            values = fixture_values(port)
            for index in (1, 4, 7, 13, 16):
                values[index] += 30
            values[8], values[11], values[26] = 31, 23, 14
            values[14] = 17
            for index in (2, 5, 10, 20, 22, 23, 25):
                values[index] = 31
            self.assertIsNotNone(recognize_values(values))

    def test_unused_feedback_fixed_port_overwrite_and_bad_loop(self):
        # Each destroys one required data/control dependency.
        for index, value in ((3, 18), (3, 4), (4, 0), (8, 5),
                             (14, 0), (16, 1), (24, 18), (26, 0)):
            values = fixture_values()
            values[index] = value
            with self.subTest(index=index, value=value):
                self.assertIsNone(recognize_values(values))

    def test_no_broadening_to_other_odd_set_values(self):
        for odd in (3, 5, 7, 9, 11, 13, 15, 19, 21, 23, 25, 27, 29, 31):
            values = fixture_values()
            values[14] = odd
            self.assertIsNone(recognize_values(values))

    def test_malformed_words_are_refused(self):
        for invalid in ([], fixture_values()[:-1], tuple(fixture_values())):
            with self.assertRaises(ValueError):
                recognize_values(invalid)
        for index in range(27):
            for invalid in (True, False, -1, 32, 1.0, '1'):
                values = fixture_values()
                values[index] = invalid
                with self.assertRaises(ValueError):
                    recognize_values(values)


class BirthBindingTests(unittest.TestCase):
    def test_consistent_fixture_never_authenticates_ancestry(self):
        birth, copies = fixture_birth()
        birth['verified'] = True
        result = inspect_birth_bindings(birth, copies)
        self.assertIsNotNone(result['code_match'])
        self.assertTrue(result['local_copy_binding_consistent'])
        self.assertFalse(result['ancestry_authenticated'])
        self.assertEqual(result['registered_eligibility'], 'NOT_EVALUATED')

    def test_consistent_nonlearner_is_not_a_code_match(self):
        values = fixture_values()
        values[3] = 4  # SET replaces READ.
        birth, copies = fixture_birth(values)
        self.assertIsNone(inspect_birth_bindings(birth, copies)['code_match'])

    def test_bad_copy_bindings_and_mutation_records_are_refused(self):
        cases = [('actor', 1), ('tick', 70)]
        for key, value in cases:
            birth, copies = fixture_birth()
            copies[0][key] = value
            with self.assertRaises(ValueError):
                inspect_birth_bindings(birth, copies)
        for key, value in (('index', 1), ('write_id', 1), ('unit', 101),
                           ('effective_source', 'ancestor_copy'),
                           ('effective_source_value', 31), ('mutation_draw', 0),
                           ('mutated', True), ('value', 31), ('source_unit', 100)):
            birth, copies = fixture_birth()
            copies[0]['writes'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                inspect_birth_bindings(birth, copies)

    def test_material_and_initial_state_are_refused(self):
        for field, value in (('energy', 64), ('feedback', 1), ('pc', 5),
                             ('registers', [False, 0]), ('memory', [False] * 8),
                             ('nursery', [{}]), ('state_units', [100] * 16)):
            birth, copies = fixture_birth()
            birth['birth']['child'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                inspect_birth_bindings(birth, copies)
        birth, copies = fixture_birth()
        birth['birth']['state_formation'][0]['energy'] = True
        with self.assertRaises(ValueError):
            inspect_birth_bindings(birth, copies)

    def test_missing_copy_or_reused_write_is_refused(self):
        birth, copies = fixture_birth()
        with self.assertRaises(ValueError):
            inspect_birth_bindings(birth, copies[:-1])
        birth['birth']['write_ids'][1] = 0
        with self.assertRaises(ValueError):
            inspect_birth_bindings(birth, copies)

    def test_malformed_decoded_instructions_are_refused(self):
        for decoded in ([12], [12.0, 0, 0], [12, False, 0], [12, 0, 32]):
            birth, copies = fixture_birth()
            birth['decoded'] = decoded
            with self.assertRaises(ValueError):
                inspect_birth_bindings(birth, copies)
        birth, copies = fixture_birth()
        copies[0]['decoded'] = [10, False, 0]
        with self.assertRaises(ValueError):
            inspect_birth_bindings(birth, copies)

    def test_refused_or_missing_outcomes_are_refused(self):
        for outcome in ('division_refused', 'copy_refused', None):
            birth, copies = fixture_birth()
            birth['outcome'] = outcome
            with self.assertRaises(ValueError):
                inspect_birth_bindings(birth, copies)
            birth, copies = fixture_birth()
            copies[0]['outcome'] = outcome
            with self.assertRaises(ValueError):
                inspect_birth_bindings(birth, copies)

    def test_valid_mutation_arithmetic_still_does_not_authenticate_draw(self):
        birth, copies = fixture_birth()
        word = copies[0]['writes'][0]
        word.update(source_value=5, effective_source_value=5,
                    mutation_draw=0, mutated=True)  # Synthetic5->6.
        result = inspect_birth_bindings(birth, copies)
        self.assertIsNotNone(result['code_match'])
        self.assertFalse(result['ancestry_authenticated'])


if __name__ == '__main__':
    unittest.main()
