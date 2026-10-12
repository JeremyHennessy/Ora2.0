import unittest
from experiments.digital_history_controls27 import Control,batch
from experiments.digital_history_controls27_reconstruct import update

class ControlTests(unittest.TestCase):
    def test_truthful_zero_is_personal_history_and_clock_is_preserved(self):
        c=Control('retained_disabled',27090);e=dict(registers=[0,1],memory=[0,1]+[0]*6)
        c.sr=[0,1];c.sm[1]=1
        c.apply(e,dict(decoded=[6,0,0],tick=2,attempt=dict(success=0)))
        x=c.apply(e,dict(decoded=[1,0,0],tick=3))
        self.assertEqual(x['register_tags'][0],[2])
        x=c.apply(e,dict(decoded=[6,0,0],tick=4,attempt=dict(success=1)))
        self.assertEqual(len(x['rewrites']),1)
        self.assertEqual(e['memory'][1],1);self.assertEqual(e['registers'][1],1)
        self.assertEqual(c.origin,4)

    def test_empty_reset_has_no_personal_origin(self):
        c=Control('intact',27090);e=dict(registers=[0,0],memory=[0]*8)
        c.apply(e,dict(decoded=[6,0,0],tick=1))
        x=c.apply(e,dict(decoded=[1,0,0],tick=2))
        self.assertEqual(x['register_tags'],[[],[]]);self.assertIsNone(x['substitution']['own_source_tick'])

    def test_independent_operator_agrees_and_shadows_do_not_alias(self):
        import copy
        for mode in ('intact','retained_disabled','own_disrupted'):
            c=Control(mode,27090);aux=dict(r=[0,0],m=[0]*8,rt=[set(),set()],mt=[set() for _ in range(8)],origin=None,reads=0)
            e=dict(registers=[1,0],memory=[0]*8);other=copy.deepcopy(e)
            for tick,op in enumerate(([4,1,1],[6,0,0],[1,0,0],[3,1,0],[2,0,1],[5,0,1],[6,0,0]),1):
                ev=dict(tick=tick,decoded=list(op))
                if op[0]==6:ev['attempt']=dict(success=1)
                self.assertEqual(c.apply(e,ev),update(aux,other,ev,mode,27090));self.assertEqual(e,other)
            self.assertIsNot(c.tr[0],c.tr[1]);self.assertIsNot(c.tm[0],c.tm[1])

    def test_unregistered_controls_refused(self):
        for seed,group,mode in ((True,'candidates','intact'),(26900,'references','intact'),(27090,'candidates','winner')):
            with self.assertRaises(ValueError):batch(seed,group,mode)
