"""NEW metadata/rejection and AST checks only; all World imports forbidden."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'experiments/digital_eka1_derived_reconstruction_v1.py'
spec = importlib.util.spec_from_file_location('eka1_reconstruction_metadata', PATH)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)  # stdlib-only module load; no World import.


def supplied_metadata():
    original = dict(tick=10, seed=1, mode='mutating', fuel_mode='renewed', inheritance_mode='parent_copy', _dose=8)
    derived = dict(tick=11)
    original_raw = a.canonical(original); derived_raw = a.canonical(derived)
    binding = dict(schema='ORA-EKA1-COMMON-PRE-READ-v1',source_sha256=a.SOURCE_PINS['experiments/digital_pressure71_population.py'],
        common_pre_state_sha256=a.sha(original_raw),actor=1,tick=10,own_turns=2,pc=1,decoded=[1,0,0],original_world_id='supplied-unverified',
        branch_ids={'true':'derived-true','identity_sham':'derived-sham','xor1':'derived-xor1'})
    request = dict(schema='ORA-EKA1-RECONSTRUCT-DERIVED-v1',original_raw_sha256=a.sha(original_raw),derived_raw_sha256=a.sha(derived_raw),binding=binding,
        arm='true',stop_tick=11,configuration=dict(seed=1,mode='mutating',fuel_mode='renewed',inheritance_mode='parent_copy',dose=8))
    return original_raw, derived_raw, request


class ReconstructionMetadata(unittest.TestCase):
    def test_preparation_is_only_metadata_not_a_valid_world_or_authority(self):
        before = set(sys.modules)
        with patch.object(a, 'runtime_sources', side_effect=AssertionError('World runtime forbidden')):
            original, derived = a.prepare(*supplied_metadata())
        self.assertNotIn('entities', original)  # deliberately NOT a lawful World
        self.assertEqual(derived, {'tick':11})
        self.assertFalse(any(x.startswith('experiments.digital_') for x in set(sys.modules)-before))

    def test_duplicate_float_constant_and_raw_hash_mismatch_rejected(self):
        for raw in (b'{"tick":11,"tick":11}', b'{"tick":11.0}', b'{"tick":NaN}'):
            original, unused, request = supplied_metadata();request['derived_raw_sha256']=a.sha(raw)
            with self.assertRaises(ValueError):a.prepare(original,raw,request)
        original, derived, request = supplied_metadata()
        with self.assertRaises(ValueError):a.prepare(original+b' ',derived,request)

    def test_boolean_context_and_impossible_read_boundary_rejected(self):
        for field in ('actor','tick','own_turns','pc'):
            original, derived, request = supplied_metadata();request['binding'][field]=True
            with self.assertRaises(ValueError):a.prepare(original,derived,request)
        for stop in (10,4097,True):
            original, derived, request = supplied_metadata();request['stop_tick']=stop
            with self.assertRaises(ValueError):a.prepare(original,derived,request)

    def test_context_configuration_branch_and_source_mismatch_rejected(self):
        original, derived, baseline = supplied_metadata()
        for change in ('source','config','branch','digest','role'):
            request=copy.deepcopy(baseline)
            if change=='source':request['binding']['source_sha256']='0'*64
            elif change=='config':request['configuration']['dose']=1
            elif change=='branch':request['binding']['branch_ids']['xor1']='derived-true'
            elif change=='digest':request['binding']['common_pre_state_sha256']='0'*64
            else:request['arm']='pass'
            with self.assertRaises(ValueError):a.prepare(original,derived,request)

    def test_ast_reconstruction_runs_original_restore_then_one_read_then_ordinary_suffix(self):
        tree=ast.parse(PATH.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='reconstruct_and_verify')
        text=ast.unparse(fn)
        self.assertLess(text.index('prepare('),text.index('runtime_sources()'))
        self.assertLess(text.index('World.restore(original)'),text.index('paid_read(world'))
        self.assertLess(text.index('paid_read(world'),text.index('while world.tick'))
        calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
        self.assertEqual(sum(isinstance(n.func,ast.Name) and n.func.id=='paid_read' for n in calls),1)
        self.assertEqual(sum(isinstance(n.func,ast.Attribute) and n.func.attr=='restore' for n in calls),1)
        self.assertFalse(any(isinstance(n, ast.Attribute) and n.attr == '__dict__' for n in ast.walk(fn)))
        self.assertIn('canonical(actual) != canonical(claimed)',text)

    def test_ast_world_imports_are_lazy_and_no_cli_or_loader_assignment(self):
        tree=ast.parse(PATH.read_bytes())
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and (n.module or '').startswith('experiments') for n in tree.body))
        self.assertFalse(any(isinstance(n,ast.If) for n in tree.body))
        self.assertNotIn('sys.path',PATH.read_text())
        self.assertNotIn('exec(',PATH.read_text())

    def test_ast_early_extinction_retains_actual_tick_and_no_scientific_authority(self):
        text=PATH.read_text()
        self.assertIn('if not world.step():',text);self.assertIn('break  # Genuine extinction',text)
        for flag in ('native_registration_authenticated=False','original_owner_authenticated=False',
                     'selection_ledger_authenticated=False','execution_authorized=False','scientific_admission=False'):
            self.assertIn(flag,text)

    def test_pinned_runtime_inputs_unchanged_without_importing_them(self):
        for name,digest in a.SOURCE_PINS.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)


if __name__=='__main__':unittest.main()
