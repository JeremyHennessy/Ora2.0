"""NEW source-only AST checks. Never import the derivative, a World or old tests."""
import ast
import copy
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT/'experiments/digital_pressure71_population.py'
DERIVATIVE = ROOT/'experiments/digital_eka1_paid_read_source_v1.py'


def functions():
    old = ast.parse(ORIGINAL.read_bytes())
    world = next(n for n in old.body if isinstance(n, ast.ClassDef) and n.name == 'World')
    step = next(n for n in world.body if isinstance(n, ast.FunctionDef) and n.name == 'step')
    new = ast.parse(DERIVATIVE.read_bytes())
    paid = next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == 'paid_read_dispatch')
    return step, paid, new


class PaidReadSource(unittest.TestCase):
    def test_original_pin_and_entire_undeclared_transition_AST_unchanged(self):
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
                         'cf22e109878bae6ac6b22e0563c8593f1c93e8ac03296a9ed9cd0cd43e1400de')
        original, paid, unused = functions()
        paid = copy.deepcopy(paid)
        self.assertEqual(ast.unparse(paid.body[0]),
                         'pre_hash, branch_id = verify_context(self, binding, arm)')
        paid.body = paid.body[1:]; paid.name = original.name; paid.args = original.args
        old_read = next(n for n in ast.walk(original) if isinstance(n, ast.If) and ast.unparse(n.test) == 'opcode == 1')
        new_read = next(n for n in ast.walk(paid) if isinstance(n, ast.If) and ast.unparse(n.test) == 'opcode == 1')
        new_read.body = old_read.body
        self.assertEqual(ast.dump(paid, include_attributes=False), ast.dump(original, include_attributes=False))

    def test_hook_in_read_after_ordinary_charge_before_both_final_hashes(self):
        unused, paid, unused_tree = functions()
        text = ast.unparse(paid)
        self.assertLess(text.index("e['energy'] -= 1"), text.index('delivered = truthful'))
        self.assertLess(text.index('delivered = truthful'), text.index("event['vm_state_hash']"))
        self.assertLess(text.index('delivered = truthful'), text.index("event['state_hash']"))
        read = next(n for n in ast.walk(paid) if isinstance(n, ast.If) and ast.unparse(n.test) == 'opcode == 1')
        self.assertEqual(ast.unparse(read.body[1]), "delivered = truthful ^ int(arm == 'xor1')")
        self.assertEqual(ast.unparse(read.body[2]), 'reg[a % 2] = delivered')

    def test_context_does_not_run_or_restore_any_world(self):
        unused, unused_paid, tree = functions()
        context = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'verify_context')
        called = [n.func.attr for n in ast.walk(context) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        self.assertNotIn('step', called); self.assertNotIn('restore', called)
        self.assertIn('snapshot', called)
        self.assertIn("h(world.snapshot()) != digest", ast.unparse(context))

    def test_no_launcher_or_original_restore_replacement_and_no_authority(self):
        unused, unused_paid, tree = functions()
        self.assertFalse(any(isinstance(n, (ast.ClassDef, ast.If)) for n in tree.body))
        self.assertEqual({n.name for n in tree.body if isinstance(n, ast.FunctionDef)},
                         {'verify_context', 'paid_read_dispatch'})
        text = DERIVATIVE.read_text()
        for flag in ('authentic_original_history_verified=False',
                     'derived_checkpoint_authority_granted=False', 'execution_authorized=False'):
            self.assertIn(flag, text)


if __name__ == '__main__':
    unittest.main()
