"""Offline binding/source closure fixtures; no replay/native imports or calls."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('offline_binding', ROOT/'tools/eka1_owner_binding_preflight.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PLAN = ROOT/'data/eka1-owner-binding-preflight-v1.json'
OWNER = 'existing-EKA323-owner-PROSPECTIVE-LABEL-ONLY'


class OwnerBindingChecks(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN.read_text())
        self.frozen = json.loads((ROOT/module.FROZEN_PLAN).read_text())

    def validate(self):
        return module.validate(self.plan, expected_owner=OWNER, frozen=self.frozen)

    def test_consistent_unassigned_is_always_not_ready(self):
        result = module.inspect(self.plan, root=ROOT, expected_owner=OWNER)
        self.assertEqual(result['status'], 'NOT_READY')
        self.assertEqual(result['raw_source_files_checked'], 11)
        for key in ('actual_ledger_bound', 'process_birth_hooks_integrated',
                    'executed_code_authenticated', 'native_execution_authorized',
                    'scientific_admission'):
            self.assertIs(result[key], False)

    def test_alternate_owner_ledger_assignment_binding_refused(self):
        for key, value in [('owner_id', 'other-owner'),
                           ('ledger_file_identity', 'per-role-fresh-file'),
                           ('assignment_registry_sha256', '0'*64),
                           ('original_owner_grant_sha256', '0'*64)]:
            with self.subTest(key=key):
                original = copy.deepcopy(self.plan)
                self.plan['binding'][key] = value
                with self.assertRaises(ValueError): self.validate()
                self.plan = original

    def test_per_role_ledger_or_binding_change_refused(self):
        for key, value in [('binding_sha256', '0'*64),
                           ('ledger_file_identity', 'fresh-second-ledger'),
                           ('dose', True)]:
            original = copy.deepcopy(self.plan)
            self.plan['roles'][7][key] = value
            with self.assertRaises(ValueError): self.validate()
            self.plan = original

    def test_missing_duplicate_extra_roles_refused(self):
        for roles in (self.plan['roles'][:-1], self.plan['roles']+[self.plan['roles'][0]],
                      [self.plan['roles'][0]]*14):
            original = self.plan['roles']; self.plan['roles'] = roles
            with self.assertRaises(ValueError): self.validate()
            self.plan['roles'] = original

    def test_global_cap_multiplication_bool_and_extensions_refused(self):
        for name, value in [('process_births_total', 56*14),
                            ('geneses_per_input', 32*7),
                            ('dispatches_per_genesis', 4097), ('concurrency', True)]:
            original = copy.deepcopy(self.plan)
            self.plan['caps'][name] = value
            with self.assertRaises(ValueError): self.validate()
            self.plan = original

    def test_self_issued_authority_and_missing_closure_refused(self):
        for key in ('execution_authorized', 'scientific_admission'):
            self.plan[key] = True
            with self.assertRaises(ValueError): self.validate()
            self.plan[key] = False
        self.plan['external_proofs']['independent_admission'] = 'self-issued'
        with self.assertRaises(ValueError): self.validate()
        self.plan['external_proofs']['independent_admission'] = None
        del self.plan['source_pins']['tools/eka1_cumulative_reservations.py']
        with self.assertRaises(ValueError): self.validate()

    def test_repinned_law_wrapper_or_ledger_refused(self):
        for name in ('experiments/digital_pressure71_population.py',
                     'experiments/digital_eka1_selection_replay_v1.py',
                     'tools/eka1_cumulative_reservations.py'):
            old = self.plan['source_pins'][name]
            self.plan['source_pins'][name] = '0'*64
            with self.assertRaises(ValueError): self.validate()
            self.plan['source_pins'][name] = old

    def test_changed_source_or_namespace_initializer_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            names = set(self.plan['source_pins']) | {module.FROZEN_PLAN}
            for name in names:
                target = root/name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT/name).read_bytes())
            target = root/'tools/eka1_cumulative_reservations.py'
            original = target.read_bytes(); target.write_bytes(original+b'\n# changed')
            with self.assertRaises(ValueError): module.inspect(self.plan, root=root, expected_owner=OWNER)
            target.write_bytes(original)
            (root/'tools/__init__.py').write_text('# unexpected initializer')
            with self.assertRaises(ValueError): module.inspect(self.plan, root=root, expected_owner=OWNER)

    def test_no_native_module_imported(self):
        self.assertFalse(any(n.startswith('experiments.digital_') for n in sys.modules))


if __name__ == '__main__': unittest.main()
