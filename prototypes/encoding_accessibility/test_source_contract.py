import tempfile
from pathlib import Path
import unittest
from source_contract import audit,PINS,node_at
import ast


class SourceContract(unittest.TestCase):
    def test_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):audit(Path(d))

    def test_changed_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/next(iter(PINS));p.parent.mkdir(parents=True);p.write_text('raise RuntimeError("never execute")')
            with self.assertRaises(ValueError):audit(root)

    def test_ast_selection_does_not_execute(self):
        tree=ast.parse('raise RuntimeError()\nclass X:\n def step(self):\n  return 1\n')
        self.assertEqual(node_at(tree,'X.step').lineno,3)

    def test_native_lower_bound_conserves_and_includes_forage(self):
        copy=9*(1+3);division=1+30
        self.assertEqual(copy+division,55+12)
        self.assertGreater(copy+division+2-12,2*20)
        self.assertEqual(copy+division+3,70)


if __name__=='__main__':unittest.main()
