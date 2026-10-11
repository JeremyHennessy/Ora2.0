import copy,unittest
from experiments.digital_ecosystem02 import World,history,h
from experiments.digital_ecosystem02_audit import audit

class Ecosystem02(unittest.TestCase):
    def test_paid_births_and_disabled_copy_same_evaluator(self):
        for mode in ('faithful','copy_disabled','mutating'):
            row=history(24790,mode);m=audit(row)
            if mode=='faithful':self.assertGreater(m['births'],0)
            if mode=='copy_disabled':self.assertEqual(m['births'],0)
            self.assertGreater(m['successful_food'],0)

    def test_forged_formation_parentage_and_balances_refused(self):
        row=history(24790,'faithful');audit(row)
        birth=next(i for i,e in enumerate(row['final']['events']) if 'birth' in e)
        for kind in ('formation','parent','energy'):
            forged=copy.deepcopy(row)
            if kind=='formation':forged['final']['events'][birth]['birth']['state_formation'][0]['energy']=0
            if kind=='parent':forged['final']['events'][birth]['birth']['child']['parent']=999
            if kind=='energy':forged['final']['constructor_remaining']+=1
            forged['hash']=h(forged['final'])
            with self.assertRaises(AssertionError):audit(forged)

    def test_checkpoint_continuation_is_executed_history(self):
        world=World(24790,'faithful');world.run(64);state=world.snapshot()
        self.assertEqual(World.restore(state).run(1536),world.run(1536))
        for key in ('last','next_id','writes'):
            forged=copy.deepcopy(state);forged[key]+=1
            with self.assertRaises(AssertionError):World.restore(forged)
        with self.assertRaises(AssertionError):World(True)

    def test_nonzero_birth_position_is_a_paid_state_value(self):
        world=World(24791,'faithful')
        # Authored software fixture intervention only, never a population history:
        # pay one external position-cell write from existing body energy.
        parent=world.entities[0];parent['pos']=3;parent['energy']-=1;world.heat+=1
        world.check()
        while not world.births:self.assertTrue(world.step())
        birth=world.events[-1]['birth'];child=birth['child']
        self.assertEqual(child['pos'],3)
        self.assertEqual(birth['state_formation'][14],dict(unit=child['state_units'][14],value=3,energy=1))
        self.assertEqual(sum(cell['energy'] for cell in birth['state_formation']),16)

if __name__=='__main__':unittest.main()
