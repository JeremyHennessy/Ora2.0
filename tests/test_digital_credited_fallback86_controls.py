"""NON-PHYSICS boundary/READ probes only. Never construct or step a World."""
import ast
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_credited_fallback86_controls as adapter
from experiments import digital_credited_fallback86_control_referee as literal
from experiments import digital_credited_fallback86_source as source


class Controls(unittest.TestCase):
    def test_all_completed_boundaries_once_after_paid_branch(self):
        for q, route in source.DESCRIPTORS:
            for control in source.CONTROLS:
                for completed in (0, 47, 48, 59):
                    for previous, entry in source.BOUNDARIES:
                        runtime = adapter.Runtime(route, control)
                        runtime.completed = completed
                        runtime.dispatch_pc = previous
                        event = dict(after=dict(pc=entry, energy=83))
                        completion = runtime.after(event)
                        self.assertEqual(completion['completed'], completed + 1)
                        self.assertEqual(completion['energy'], 83)
                        entity = dict(pc=entry, memory=[0]*q, registers=[7,11], feedback=2)
                        ordinary = copy.deepcopy(entity)
                        evidence = runtime.before(entity)
                        independent = copy.deepcopy(ordinary)
                        expected = literal.boundary_before(independent,
                            (previous, entry), completed+1, source.ENTRIES[route], control)
                        self.assertEqual(evidence, expected)
                        self.assertEqual(entity, independent)
                        self.assertEqual({k:v for k,v in entity.items() if k!='pc'},
                                         {k:v for k,v in ordinary.items() if k!='pc'})
                        self.assertIsNone(runtime.before(entity))
                        self.assertEqual(runtime.completed, completed+1)
                        self.assertEqual(runtime.after(dict(death=dict(cause='energy'))), None)

    def test_header_unfinished_and_invalid_boundary_refusals(self):
        runtime = adapter.Runtime('fallback0', 'history_disabled')
        for pc, entry in ((0,1),(3,4),(10,12),(14,15)):
            runtime.dispatch_pc=pc
            self.assertIsNone(runtime.after(dict(after=dict(pc=entry,energy=1))))
            self.assertEqual(runtime.completed,0)
        runtime.pending=(5,1)
        with self.assertRaises(AssertionError):runtime.before(dict(pc=True))
        with self.assertRaises(AssertionError):runtime.before(dict(pc=6))
        for route, control in ((True,'intact'),('model',True),('model','foreign')):
            with self.assertRaises(AssertionError):adapter.Runtime(route,control)
        runtime.pending=None;runtime.dispatch_pc=5
        with self.assertRaises(AssertionError):runtime.after(dict(after=dict(pc=True,energy=1)))

    def test_all_reads_and_physical_store_feedback_preservation(self):
        for q, route in source.DESCRIPTORS:
            for control in source.CONTROLS:
                for completed in (47,48,59):
                    for pc in (7,12):
                        for index in range(16):
                            for values in ([0]*q,[15]*q,list(range(q))):
                                runtime=adapter.Runtime(route,control)
                                runtime.completed=completed;runtime.dispatch_pc=pc
                                memory=adapter.ModelView(values,runtime)
                                entity=dict(memory=list(values),registers=[11,index])
                                expected=literal.model_value(entity,pc,completed,control)
                                self.assertEqual(runtime.read(memory,index),expected)
                                self.assertEqual(memory[index%q],expected['value'])
                                self.assertEqual(list(memory),values)
                                self.assertEqual(json.loads(json.dumps(memory)),values)
                                memory[index%q]=9
                                self.assertEqual(list.__getitem__(memory,index%q),9)
                                self.assertEqual(entity['registers'],[11,index])
        runtime=adapter.Runtime('model','intact');runtime.dispatch_pc=6
        with self.assertRaises(AssertionError):runtime.read([0,0],0)
        runtime.dispatch_pc=7
        with self.assertRaises(AssertionError):runtime.read([0,0],True)

    def test_stop_does_not_consume_another_boundary(self):
        world=object.__new__(adapter.World)
        runtime=adapter.Runtime('fallback0','fallback_misbound')
        runtime.completed=60;runtime.pending=(5,1)
        world.entities={0:dict(pc=1)};world.tick=301
        adapter._RUNTIME[world]=runtime
        with patch.object(adapter.engine.World,'step',side_effect=AssertionError('No paid dispatch')):
            self.assertFalse(world.step())
        self.assertEqual(world.entities[0]['pc'],1)
        self.assertEqual(runtime.pending,(5,1))
        self.assertEqual(world.control_ledger(),[])
        with self.assertRaises(RuntimeError):world.run()
        del adapter._RUNTIME[world]

    def test_literal_independence_and_unchanged_paid_operations(self):
        root=Path(__file__).resolve().parents[1]/'experiments'
        old=ast.parse((root/'digital_memory80_referee.py').read_text())
        new=ast.parse((root/'digital_credited_fallback86_control_referee.py').read_text())
        self.assertEqual([ast.unparse(n) for n in new.body if isinstance(n,(ast.Import,ast.ImportFrom))],
                         ['import hashlib','import json'])
        def functions(tree):
            return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(tree)
                    if isinstance(n,ast.FunctionDef) and n.name!='audit'}
        old_functions=functions(old);new_functions=functions(new)
        for name, body in old_functions.items():self.assertEqual(new_functions[name],body,name)
        def opcode_arms(tree):
            return {ast.unparse(n.test):ast.dump(ast.Module(body=n.body,type_ignores=[]),include_attributes=False)
                    for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test).startswith('op == ')}
        prior=opcode_arms(old);current=opcode_arms(new)
        self.assertEqual(set(prior),set(current))
        for arm, body in prior.items():
            if arm!='op == 19':self.assertEqual(current[arm],body,arm)
        engine=ast.parse((root/'digital_memory80.py').read_text())
        cls=next(n for n in engine.body if isinstance(n,ast.ClassDef) and n.name=='World')
        self.assertEqual(len([n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='step']),1)


if __name__=='__main__':unittest.main()
