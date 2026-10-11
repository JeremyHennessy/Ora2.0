import copy,unittest
from experiments.digital_memory_task import Task
from experiments.digital_memory_task_audit import audit,h

def witness(orientation,mode,stationary=None):
    # Authored software trace generator ONLY. Never installed in an organism.
    t=Task(orientation,mode)
    for _ in range(64):
        cue=t.step('sense')
        if cue is None:break
        remember=t.step('read',0)
        if remember is None:break
        action=cue^(remember%2) if stationary is None else stationary[cue]
        success=t.step('act',action)
        estimate=(remember%2)^int(success==0)
        t.step('write',[0,estimate if stationary is None else 0])
    return t.record()

class MemoryTaskTests(unittest.TestCase):
    def test_independent_generic_positive_and_all_stationary_routes(self):
        for orientation in (0,1):
            result=audit(witness(orientation,'normal'))
            self.assertEqual(result['hits'],63-orientation)
            self.assertEqual((result['instructions'],result['actions']),(256,64))
            self.assertEqual(witness(orientation,'normal')['events'][-1]['op'],'write')
            self.assertFalse(result['organism_learning'])
            for stationary in ((0,0),(0,1),(1,0),(1,1)):
                fixed=audit(witness(orientation,'normal',stationary))
                # Preserve failed admission, do not assert dead controls completed.
                self.assertLessEqual(fixed['hits'],32)
                if stationary in ((0,0),(1,1)):
                    self.assertEqual((fixed['hits'],fixed['instructions']),(32,256))
            disabled=audit(witness(orientation,'memory_disabled'))
            self.assertLess(disabled['instructions'],256)
            self.assertLessEqual(disabled['hits'],32)

    def test_impossible_ancestry_and_energy_refused_even_rehashed(self):
        good=witness(1,'normal')
        bad=copy.deepcopy(good);bad['events'][2]['food']=0
        with self.assertRaises(AssertionError):audit(bad)
        bad=copy.deepcopy(good);bad['final']['energy']+=20;bad['state_hash']=h(bad['final'])
        with self.assertRaises(AssertionError):audit(bad)

    def test_finite_death_and_invalid_operands(self):
        t=Task(1)
        for _ in range(12):t.step('sense')
        self.assertIsNone(t.step('act',1));self.assertFalse(audit(t.record())['actions'])
        for op,arg in (('read',True),('act',2),('write',[0,True]),('write',[8,0])):
            with self.assertRaises(AssertionError):Task(0).step(op,arg)
