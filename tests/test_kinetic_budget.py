import ast
import copy
from pathlib import Path
import unittest
from experiments import kinetic_budget as worker
from experiments import kinetic_budget_audit as audit


class BudgetTests(unittest.TestCase):
    def test_closed_form_finite_capacity_and_no_natural_worlds(self):
        panel=worker.panel(); proof=audit.inspect(panel)
        self.assertEqual([c['completed_cycles'] for c in panel['cases']],[256,128,85,64,51])
        self.assertEqual(proof['events'],5022)
        self.assertEqual(proof['natural_worlds'],0)
        self.assertFalse(proof['productive_organization_demonstrated'])

    def test_conservative_price_forgery_rejected(self):
        panel=copy.deepcopy(worker.panel())
        event=next(e for e in panel['cases'][0]['events'] if e['action']=='associate')
        event['state']['fuel']+=1; event['state']['waste']-=1; event['state']['heat']-=1
        with self.assertRaisesRegex(ValueError,'Exact reaction prices'): audit.inspect(panel)

    def test_audit_independent_of_producer(self):
        nodes=ast.walk(ast.parse(Path(audit.__file__).read_text(encoding='utf-8')))
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module.startswith('experiments') for n in nodes))
