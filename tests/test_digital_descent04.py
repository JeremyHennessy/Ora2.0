import copy,unittest
from experiments.digital_descent04 import World,history,h,ANCESTOR
from experiments.digital_descent04_audit import audit

class Descent04(unittest.TestCase):
    def test_paid_positive_and_impossible_use_same_endpoint(self):
        # Historical ordinary-route software fixture; outside primary/reserves.
        row=history(25190);m=audit(row)
        self.assertGreater(m['descendant_births'],0)
        for kind in ('formation','ancestry','checkpoint'):
            bad=copy.deepcopy(row)
            if kind=='formation':bad['final']['formation'][0]['energy']=0
            if kind=='ancestry':next(e for e in bad['final']['events'] if 'birth' in e)['birth']['write_ids'][0]+=1
            if kind=='checkpoint':bad['checkpoint']['last']+=1
            bad['hash']=h(bad['final'])
            with self.assertRaises(AssertionError):audit(bad)
        disabled=audit(history(25190,'copy_disabled'))
        self.assertEqual(disabled['births'],0)

    def test_variation_and_genotype_checkpoint_are_interpreted_data(self):
        row=history(25170,'mutating');audit(row)
        world=World(25170,'mutating');world.run(64);state=world.snapshot()
        self.assertEqual(World.restore(state).run(1536),world.run(1536))
        for value in (True,1.0):
            bad=copy.deepcopy(state);bad['formation'][0]['energy']=value
            with self.assertRaises(AssertionError):World.restore(bad)
        for value in (-1,32,'shell',True):
            program=copy.deepcopy(ANCESTOR);program[0][0]=value
            with self.assertRaises(AssertionError):World(25170,program=program)

if __name__=='__main__':unittest.main()
