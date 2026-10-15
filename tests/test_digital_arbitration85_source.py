"""Independent source-path checks. No organism, world or target is executed."""
import ast
import unittest
from pathlib import Path
from experiments import digital_arbitration85_source as source


def route_path(code, entry, feedback):
    """Follow only CFG edges for an invented feedback symbol, not VM physics."""
    pc = entry
    path = []
    read_feedback = False
    for _ in range(16):
        op, a, b = code[pc]
        path.append(pc)
        if op == 1:
            read_feedback = True
        if op == 8:
            assert read_feedback and a == 0
            pc = b if feedback == 0 else pc+1
        elif op == 7:
            pc = b
        else:
            pc += 1
        if pc in (1, 6):
            return path, pc
    raise AssertionError('No decision boundary')


class ArbitrationSource(unittest.TestCase):
    def test_all_descriptors_and_only_declared_parameter_words(self):
        manifest = source.manifest()
        self.assertEqual(len(manifest['descriptors']), 12)
        self.assertFalse(manifest['scientific_admission'])
        first = source.programme(2, 0, 'constant')
        for row in manifest['descriptors']:
            code = row['programme']
            self.assertEqual(len(code), 16)
            self.assertTrue(all(t[0] in source.OPS for t in code))
            self.assertTrue(all(type(v) is int and 0 <= v < 32 for t in code for v in t))
            changed = {(i, j) for i in range(16) for j in range(3) if first[i][j] != code[i][j]}
            self.assertLessEqual(changed, {(0, 1), (0, 2), (1, 2)})
            self.assertEqual(row['formation'], 3*len(code)+row['capacity']+8)
            self.assertEqual(row['blank_models'], [0]*row['capacity'])

    def test_actual_paths_update_only_sensed_model_error(self):
        for descriptor in source.DESCRIPTORS:
            code = source.programme(*descriptor)
            for entry in (1, 6):
                for feedback in (0, 1, 2):
                    with self.subTest(descriptor=descriptor, entry=entry, feedback=feedback):
                        path, next_entry = route_path(code, entry, feedback)
                        ops = [code[i][0] for i in path]
                        self.assertEqual(ops.count(6), 1)
                        self.assertEqual(ops.count(1), 1)
                        self.assertEqual(ops.count(20), int(entry == 6 and feedback == 0))
                        self.assertEqual(ops.count(0), int(entry == 6))
                        self.assertEqual(ops.count(19), (2 if feedback == 0 else 1) if entry == 6 else 0)
                        self.assertEqual(next_entry, (7-entry) if feedback == 0 else entry)
                        expected = (4 if feedback == 0 else 5) if entry == 1 else (9 if feedback == 0 else 6)
                        self.assertEqual(len(path), expected)
                        if entry == 6 and feedback == 0:
                            self.assertEqual([code[i] for i in path[-4:]],
                                             [[19, 0, 1], [21, 0, 0], [20, 1, 0], [7, 0, 1]])

    def test_descriptor_refusals_before_any_source_emission(self):
        for descriptor in ((True, 0, 'constant'), (3, 0, 'constant'),
                           (2, True, 'constant'), (2, 2, 'model'),
                           (2, 0, 1), (2, 0, 'oracle')):
            with self.assertRaises(AssertionError):
                source.programme(*descriptor)

    def test_source_has_no_target_or_world_dependency(self):
        tree = ast.parse(Path(source.__file__).read_bytes())
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(isinstance(n, ast.Import) for n in imports))
        self.assertEqual({a.name for n in imports for a in n.names}, {'hashlib', 'json'})
        self.assertEqual(source.manifest()['worlds'], 0)
        self.assertEqual(source.manifest()['targets_queried'], 0)


if __name__ == '__main__':
    unittest.main()
