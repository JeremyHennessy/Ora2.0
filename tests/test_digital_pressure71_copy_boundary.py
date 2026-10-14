"""Registered software1/2 witnesses only; no primary/reserve/learner candidate."""
import ast
import copy
import json
from pathlib import Path
import unittest
from experiments import digital_sharedlineage68_population as old
from experiments import digital_pressure71_population as new
from experiments import digital_pressure71_natural_referee as referee


class Pressure71CopyBoundaryTests(unittest.TestCase):
    rows = {}
    proofs = {}
    rejected = {}

    @classmethod
    def setUpClass(cls):
        for seed in (1, 2):
            for mode, inheritance in (('faithful', 'parent_copy'),
                                      ('mutating', 'parent_copy'), ('mutating', 'ancestor_copy')):
                for dose in (1, 8):
                    key = f'{seed}-{mode}-{inheritance}-{dose}'
                    cls.rows[key] = new.history(seed, mode=mode, inheritance_mode=inheritance,
                                                dose=dose, horizon=512, software_only=True)

    def reject(self, label, row):
        self.rejected[label] = row
        with self.assertRaises(AssertionError):
            referee.audit(row)

    def test_all_fixed_software_histories_literal_replay(self):
        for row in self.rows.values():
            proof = referee.audit(row)
            self.proofs[f"{row['seed']}-{row['mode']}-{row['inheritance_mode']}-{row['dose']}"] = proof
            self.assertTrue(proof['verified'])
            self.assertTrue(proof['software_only'])
            self.assertFalse(proof['scientific_admission'])
            self.assertFalse(proof['stage_credit'])
            self.assertEqual(proof['dose'], row['dose'])
            self.assertEqual(proof['ticks'], row['final']['tick'])

    def test_frozen_step_changes_only_copy_argument(self):
        root = Path(__file__).parents[1] / 'experiments'
        def step(path):
            tree = ast.parse(path.read_text())
            cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'World')
            return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'step')
        a = step(root / 'digital_sharedlineage68_population.py')
        b = step(root / 'digital_pressure71_population.py')
        calls = [n for n in ast.walk(b) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'copy_result']
        self.assertEqual(len(calls), 1)
        self.assertEqual(ast.dump(calls[0].args.pop()), ast.dump(ast.parse('self.dose', mode='eval').body))
        self.assertEqual(ast.dump(a), ast.dump(b))

    def test_literal_replay_has_no_producer_import(self):
        path = Path(referee.__file__)
        imports = [n for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(isinstance(n, ast.Import) and all(a.name in ('hashlib', 'json') for a in n.names) for n in imports))

    def test_dose8_all_physical_operations_match_frozen68(self):
        for seed in (1, 2):
            for mode, inheritance in (('faithful', 'parent_copy'), ('mutating', 'parent_copy'), ('mutating', 'ancestor_copy')):
                a = old.World(seed, mode, inheritance_mode=inheritance)
                b = new.World(seed, mode, inheritance_mode=inheritance, dose=8)
                for _ in range(512):
                    active_a, active_b = a.step(), b.step()
                    self.assertEqual(active_a, active_b)
                    state_b = b.snapshot(False)
                    self.assertEqual(state_b.pop('_dose'), 8)
                    self.assertEqual(a.snapshot(False), state_b)
                    if not active_a:
                        break
                    strip = lambda e: {k: v for k, v in e.items() if k not in ('vm_state_hash', 'state_hash')}
                    self.assertEqual(strip(a.events[-1]), strip(b.events[-1]))
                    self.assertEqual(a.events[-1]['state_hash'], old.h(state_b))

    def test_dose_one_is_subset_of_eight_same_draw_source_jump(self):
        small = large = 0
        for seed in (1, 2):
            for write_id in range(128):
                index = write_id % 27
                p = (3 * index + 7) % 32
                a = new.copy_result(seed, write_id, p, index, 'mutating', 'parent_copy', 1)
                b = new.copy_result(seed, write_id, p, index, 'mutating', 'parent_copy', 8)
                self.assertEqual(b, old.copy_result(seed, write_id, p, index, 'mutating', 'parent_copy'))
                self.assertEqual(a[:2], b[:2])
                if a[2] != a[0]:
                    small += 1
                    self.assertEqual(a[2], b[2])
                large += b[2] != b[0]
        self.assertGreater(small, 0)
        self.assertGreater(large, small)

    def test_ancestor_effective_source_uses_same_index(self):
        for index in range(27):
            a = new.copy_result(1, index, 31, index, 'mutating', 'ancestor_copy', 1)
            self.assertEqual(a[0], old.ANCESTOR_WORDS[index])

    def test_faithful_doses_have_same_physics_and_bill(self):
        a = new.World(1, dose=1)
        b = new.World(1, dose=8)
        for _ in range(128):
            self.assertEqual(a.step(), b.step())
            x, y = a.snapshot(False), b.snapshot(False)
            x.pop('_dose'); y.pop('_dose')
            self.assertEqual(x, y)

    def test_dose_bound_and_immutable(self):
        for value in (True, False, 1.0, '1', 0, 2, 9):
            with self.assertRaises(AssertionError):
                new.World(1, dose=value)
        world = new.World(1, dose=1)
        with self.assertRaises(AttributeError):
            world._dose = 8
        with self.assertRaises(AttributeError):
            world.dose = 8

    def test_serialized_checkpoint_continuation_exact(self):
        for dose in (1, 8):
            row = self.rows[f'1-mutating-parent_copy-{dose}']
            state = json.loads(json.dumps(row['checkpoint']))
            world = new.World.restore(state)
            self.assertEqual(world.dose, dose)
            self.assertEqual(world.run(512), row['final'])

    def test_changed_dose_identity_rejected(self):
        row = copy.deepcopy(self.rows['1-mutating-parent_copy-8'])
        row['dose'] = 1
        self.reject('changed-dose', row)

    def test_changed_copy_certificate_rejected(self):
        row = copy.deepcopy(self.rows['1-mutating-parent_copy-1'])
        event = next(e for e in row['final']['events'] if e.get('writes'))
        event['writes'][0]['mutation_draw'] += 100
        row['hash'] = new.h(row['final'])
        self.reject('changed-copy-draw', row)

    def test_rehashed_ledger_repair_rejected(self):
        row = copy.deepcopy(self.rows['1-faithful-parent_copy-8'])
        row['final']['heat'] += 1
        row['hash'] = new.h(row['final'])
        self.reject('rehashed-ledger', row)

    def test_truncated_scientific_and_false_software_extent_rejected(self):
        row = copy.deepcopy(self.rows['1-faithful-parent_copy-8'])
        row['software_only'] = False
        self.reject('scientific-short-horizon', row)
        row = copy.deepcopy(self.rows['1-faithful-parent_copy-8'])
        row['horizon'] = 64
        self.reject('events-beyond-declared-horizon', row)
        row = copy.deepcopy(self.rows['1-faithful-parent_copy-8'])
        row['horizon'] = 4096; row['software_only'] = False
        self.reject('scientific-unfinished-live-history', row)

    def test_software_primary_or_reserve_scope_refused_before_query(self):
        for seed in (74000, 74100, 74200, 74300):
            with self.assertRaises(AssertionError):
                new.history(seed, horizon=512, software_only=True)
        row = copy.deepcopy(self.rows['1-faithful-parent_copy-8'])
        row['seed'] = 74000
        self.reject('software-primary-label', row)

    def test_checkpoint_dose_corruption_refused(self):
        state = copy.deepcopy(self.rows['1-mutating-parent_copy-1']['checkpoint'])
        state['_dose'] = 9
        with self.assertRaises(AssertionError):
            new.World.restore(state)


if __name__ == '__main__':
    unittest.main()
