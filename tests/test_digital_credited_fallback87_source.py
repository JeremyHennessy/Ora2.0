"""SOURCE-ONLY fixtures; no World construction, step or scientific label query."""
import ast
import copy
import inspect
from pathlib import Path
import unittest
from experiments import digital_credited_fallback87_source as source
from experiments import digital_credited_fallback87_world as world
from experiments import digital_credited_fallback87_referee as literal
from experiments import digital_credited_fallback86_control_referee as old_literal

class Source87Tests(unittest.TestCase):
    def test_neutral_registry_and_costs(self):
        m=source.manifest()
        self.assertEqual(len(source.roster()),51)
        self.assertEqual(len(m['descriptors']),9)
        self.assertEqual([d['formation'] for d in m['descriptors']],[73]*3+[75]*3+[79]*3)
        self.assertEqual([d['formation'] for d in m['references'].values()],[22,22,22,25,25,31])
        self.assertEqual([source.programme(r) for r in source.FIXED],list(literal.REFERENCE_PROGRAMMES))
        for r in source.FIXED:
            self.assertFalse({2,3,19,20}&{t[0] for t in source.programme(r)})
        self.assertFalse(m['scientific_execution_admitted'])
        self.assertEqual(m['targets_queried'],0)

    def test_typed_admission_and_no_reserve_query(self):
        for seed in source.PRIMARY+source.UNSEEN:
            source.admit(seed,source.ADMISSION)  # registry permission is not a query
            with self.assertRaises(AssertionError):source.admit(seed)
        for seed in (True,2100080,1009300,-1,*source.RESERVED):
            for admission in (None,source.ADMISSION):
                with self.assertRaises(AssertionError):source.admit(seed,admission)
        for packet in (True,-1,1.0):
            with self.assertRaises(AssertionError):source.target_mask(source.SOFTWARE[0],packet)

    def test_namespace_code_and_no_mutation(self):
        def function(value):return value+1
        before=dict(function.__globals__)
        bound=world.bind(function,object())
        self.assertIs(bound.__code__,function.__code__)
        self.assertEqual(bound.__defaults__,function.__defaults__)
        self.assertIsNot(bound.__globals__,function.__globals__)
        self.assertEqual(bound.__globals__['SOFTWARE'],source.SEEDS)
        self.assertEqual(function.__globals__,before)
        self.assertEqual(bound(2),3)

    def test_reference_full_branch_boundaries(self):
        for descriptor in source.FIXED:
            rt=world.ReferenceRuntime(descriptor);finish=rt.finish
            for pc,op,after,expected in ((0,7,finish,0),(2,6,3,0),(3,8,finish,0),(4,7,finish,1)):
                rt.before({'pc':pc})
                result=rt.after({'decoded':[op,0,finish],'after':{'pc':after,'energy':7}})
                self.assertEqual(rt.completed,expected)
                self.assertEqual(result is not None,bool(expected))
            rt.before({'pc':4})
            self.assertIsNone(rt.after({'decoded':[7,0,finish],'death':{'cause':'energy'}}))
            self.assertEqual(rt.completed,1)

    def test_independent_known_label_and_physics_ast(self):
        for i,seed in enumerate(source.SOFTWARE):
            for p in (0,47,48,99):
                expected=((0,255,90,165),(0,255,165,90))[int(p>=48)][i]
                self.assertEqual(source.target_mask(seed,p),expected)
                self.assertEqual(literal.label_mask(seed,p),expected)
        old=ast.parse(inspect.getsource(old_literal.audit));new=ast.parse(inspect.getsource(literal.audit))
        for name in ('newborn','charge','packet','write','conserved'):
            get=lambda tree:next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name==name)
            self.assertEqual(ast.dump(get(old)),ast.dump(get(new)))
        def operation(tree,number):
            return next(x.body for x in ast.walk(tree) if isinstance(x,ast.If)
                and ast.dump(x.test)==ast.dump(ast.parse('op=='+str(number),mode='eval').body))
        for number in (0,1,2,3,4,5,7,8,10,12,19,20,21):
            self.assertEqual([ast.dump(x) for x in operation(old,number)],
                             [ast.dump(x) for x in operation(new,number)])
        for name in ('boundary_before','model_value','boundary_after','digest','duplicate'):
            self.assertEqual(ast.dump(ast.parse(inspect.getsource(getattr(old_literal,name)))),
                             ast.dump(ast.parse(inspect.getsource(getattr(literal,name)))))

    def test_source_and_import_boundary(self):
        tree=ast.parse(inspect.getsource(literal))
        self.assertEqual([n.names[0].name for n in tree.body if isinstance(n,ast.Import)],['hashlib','json'])
        self.assertFalse(any(isinstance(n,ast.ImportFrom) for n in ast.walk(tree)))
        root=Path(source.__file__).parent
        kernel=(root/'digital_memory80.py').read_bytes()
        import hashlib
        self.assertEqual(hashlib.sha256(kernel).hexdigest(),'1826b33893321d1a7a603ccef690e13b92ed16f26d6e6c093f14a45ca367e104')
        # Import and manifest create no cached map or acquired policy knowledge.
        self.assertFalse({'MAPS','LABELS','WINNER','TARGET_GENOME'}&set(source.__dict__))
        self.assertEqual(len(source.manifest()['descriptors']),9)

if __name__=='__main__':unittest.main()
