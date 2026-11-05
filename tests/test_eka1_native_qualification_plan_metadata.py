"""New preparation metadata only. Never imports organism/replay modules."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('eka1_plan',ROOT/'tools/eka1_native_qualification_plan.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Plan(unittest.TestCase):
    def setUp(self):self.plan=json.loads((ROOT/'data/eka1-native-authentication-qualification-plan-20261026.json').read_text())
    def test_caps_count_all_roles_and_restore_work(self):
        r=m.validate(self.plan)
        self.assertEqual(r['maximum_native_roles'],14)
        self.assertEqual(r['maximum_dispatches'],262144)
        self.assertEqual(r['sequential_wall_including_closure_seconds'],2940)
    def test_no_missing_role_or_panel(self):
        for key in ('roles','panels'):
            p=copy.deepcopy(self.plan);p[key].pop()
            with self.assertRaises(ValueError):m.validate(p)
    def test_preparation_never_authenticates_original(self):
        r=m.validate(self.plan)
        self.assertFalse(r['actual_original_authenticated']);self.assertFalse(r['native_execution_authorized'])
        self.assertEqual(len(r['missing_external_proofs']),10)
    def test_no_self_signed_proof_or_execution_flag(self):
        for key in ('execution_authorized','scientific_admission'):
            p=copy.deepcopy(self.plan);p[key]=True
            with self.assertRaises(ValueError):m.validate(p)
        p=copy.deepcopy(self.plan);p['external_proofs']['original_owner_grant']='a'*64
        with self.assertRaises(ValueError):m.validate(p)
    def test_bool_and_budget_extension_rejected(self):
        for value in (True,121):
            p=copy.deepcopy(self.plan);p['caps']['user_cpu_seconds_per_role']=value
            with self.assertRaises(ValueError):m.validate(p)
    def test_dose_loss_and_selected_seed_rejected(self):
        p=copy.deepcopy(self.plan);p['dose_slots']=[8]
        with self.assertRaises(ValueError):m.validate(p)
        p=copy.deepcopy(self.plan);p['seed']=1
        with self.assertRaises(ValueError):m.validate(p)
    def test_no_retry_permission(self):
        self.plan['retry_policy']='RETRY'
        with self.assertRaises(ValueError):m.validate(self.plan)


if __name__=='__main__':unittest.main()
