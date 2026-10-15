"""Admission/unchanged paid kernel regressions; no World genesis or targets."""
import ast
import inspect
import textwrap
import unittest
from unittest.mock import patch
from experiments import digital_inheritance83_world as new
from experiments import digital_inheritance83_referee as referee
from experiments import digital_memory80 as old


class Inheritance83SourceTests(unittest.TestCase):
    def test_default_scientific_and_reserved_calls_refuse_before_target(self):
        def forbidden(*args,**kwargs):
            raise RuntimeError('Target lookup happened before admission')
        with patch.object(new,'h',forbidden),patch.object(referee.hashlib,'sha256',forbidden):
            for seed in new.PRIMARY+new.UNSEEN+tuple(range(1009000,1009008))+tuple(range(1009200,1009208)):
                with self.assertRaisesRegex(AssertionError,'unregistered context'):
                    new.World(seed)
                with self.assertRaisesRegex(AssertionError,'unregistered context'):
                    referee.audit({},seed=seed,mode='variation',max_population=8,expansion_tick=1536,program=old.programme(2),horizon=16384)
            for seed in range(1009000,1009008):
                with self.assertRaisesRegex(AssertionError,'unregistered context'):
                    new.admit(seed,new.ADMISSION)

    def test_paid_kernel_and_programme_are_unchanged(self):
        for q in (2,4,8):self.assertEqual(old.programme(q),new.programme(q))
        def tree(method):return ast.dump(ast.parse(textwrap.dedent(inspect.getsource(method))),include_attributes=False)
        for name in ('body','effective','check','snapshot','packet','input','debit','finish_copy','copy','draw','divide','remove','run'):
            self.assertEqual(tree(getattr(old.World,name)),tree(getattr(new.World,name)),name)
        source=textwrap.dedent(inspect.getsource(new.World.step))
        calls=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='model_read']
        self.assertEqual(2,len(calls),'Both direct/indexed LOAD must use the intervention boundary')


if __name__=='__main__':unittest.main()
