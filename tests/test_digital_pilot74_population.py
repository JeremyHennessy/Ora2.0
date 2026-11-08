"""Prospective adapter source/guard checks; no natural genesis or VM steps."""
import ast
import inspect
import unittest
from types import SimpleNamespace
from experiments import digital_pilot74_population as candidate
from experiments import digital_pressure71_population as historical
from experiments import digital_longitudinal01_population as previous

class Pilot74(unittest.TestCase):
    def test_only_prospective_input_bound_differs(self):
        a=ast.parse(inspect.getsource(candidate.World.input).strip().replace('\n        ','\n    '))
        b=ast.parse(inspect.getsource(previous.World.input).strip().replace('\n        ','\n    '))
        self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
        self.assertEqual(previous.MAX_HORIZON,8192);self.assertEqual(candidate.MAX_HORIZON,10240)
    def test_step_and_historical_restore_retained(self):
        self.assertIs(candidate.World.step,historical.World.step)
        self.assertEqual(candidate.World.restore.__func__,historical.World.restore.__func__)
        self.assertNotIn('restore',candidate.World.__dict__)
    def test_invalid_constructor_scope_refused_before_genesis(self):
        for args,kwargs in [((True,),{}),((4,),{}),((3,'mutating'),{}),((3,),{'dose':1}),((3,),{'dose':True}),((3,),{'inheritance_mode':'ancestor_copy'})]:
            with self.assertRaises(AssertionError):candidate.World.__init__(None,*args,**kwargs)
    def test_only_registered_endpoints_and_forward_ticks(self):
        fixture=SimpleNamespace(tick=8192)
        for horizon in (True,8193,10241,8191):
            with self.assertRaises(AssertionError):candidate.World.run(fixture,horizon)
        fixture.tick=9216
        with self.assertRaises(AssertionError):candidate.World.run(fixture,8192)
    def test_terminal_has_no_continuation(self):
        def forbidden():raise AssertionError('terminal cannot step')
        fixture=SimpleNamespace(tick=10240,step=forbidden,snapshot=lambda:{'fixture':'terminal'})
        self.assertEqual(candidate.World.run(fixture,10240),{'fixture':'terminal'})
    def test_mocked_finite_control_loop(self):
        calls=[];fixture=SimpleNamespace(tick=9216)
        def step():calls.append(fixture.tick);fixture.tick+=1;return True
        fixture.step=step;fixture.snapshot=lambda:{'tick':fixture.tick}
        self.assertEqual(candidate.World.run(fixture,10240),{'tick':10240});self.assertEqual(len(calls),1024)
    def test_mocked_extinction_stops(self):
        fixture=SimpleNamespace(tick=9216,step=lambda:False,snapshot=lambda:{'tick':9216})
        self.assertEqual(candidate.World.run(fixture,10240),{'tick':9216})
if __name__=='__main__':unittest.main()
