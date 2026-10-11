import copy,unittest
from experiments.digital_route02 import World,history,h
from experiments.digital_route02_audit import audit
from experiments.digital_ecosystem02 import World as Original

class Route02(unittest.TestCase):
    def test_stationary_configuration_preserves_exact_original_law(self):
        original=Original(24890,'faithful');configured=World(24890,'faithful','stationary')
        self.assertEqual(original.run(1536),configured.run(1536))
        audit(history(24890,'stationary','faithful'))

    def test_paid_mobile_history_and_birth_null_same_evaluator(self):
        for mode in ('faithful','copy_disabled'):
            row=history(24891,'mobile',mode);metrics=audit(row)
            self.assertGreater(metrics['remote_food'],0)
            if mode=='copy_disabled':self.assertEqual(metrics['births'],0)
            # This is a software witness, not a scientific gate or seed screen.
            if mode=='faithful':self.assertGreater(metrics['births'],0)
            self.assertEqual(row['final']['constructor_remaining'],94)

    def test_impossible_ancestry_formation_and_genesis_refused(self):
        row=history(24891,'mobile','faithful');audit(row)
        birth=next(i for i,e in enumerate(row['final']['events']) if 'birth' in e)
        for kind in ('genesis','formation','parent'):
            forged=copy.deepcopy(row)
            if kind=='genesis':forged['genesis_program'][-1][0]=7
            if kind=='formation':forged['final']['events'][birth]['birth']['state_formation'][14]['energy']=0
            if kind=='parent':forged['final']['events'][birth]['birth']['child']['parent']=999
            forged['hash']=h(forged['final'])
            with self.assertRaises(AssertionError):audit(forged)

    def test_mobile_checkpoint_configuration_and_scheduler_not_free(self):
        world=World(24891,'faithful','mobile');world.run(64);state=world.snapshot()
        self.assertEqual(World.restore(state).run(1536),world.run(1536))
        for key in ('last','next_id','writes'):
            forged=copy.deepcopy(state);forged[key]+=1
            with self.assertRaises(AssertionError):World.restore(forged)

if __name__=='__main__':unittest.main()
