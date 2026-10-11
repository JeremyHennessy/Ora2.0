import copy,unittest
from experiments.digital_release07 import World,history,h
from experiments.digital_release07_audit import audit

class Release07(unittest.TestCase):
    def test_fresh_stock_is_inaccessible_then_released_at_finite_cost(self):
        world=World(25689,route='alternating');world.run(63)
        self.assertTrue(set(range(16,32))<=set(world.food))
        fuel,heat=world.constructor_remaining,world.heat;world.step()
        self.assertEqual(world.constructor_remaining,fuel-16)
        self.assertGreaterEqual(world.heat,heat+17)
        self.assertEqual(world.events[-1]['release']['energy'],16)
        row=history(25689,'alternating');audit(row)
        for kind in ('release','checkpoint'):
            bad=copy.deepcopy(row)
            if kind=='release':next(e for e in bad['final']['events'] if 'release' in e)['release']['energy']=0
            else:bad['checkpoint']['formation'][0]['energy']=True
            bad['hash']=h(bad['final'])
            with self.assertRaises(AssertionError):audit(bad)

    def test_checkpoint_continuation_retains_stock_boundary(self):
        world=World(25689,route='alternating');world.run(63);state=world.snapshot()
        self.assertEqual(World.restore(state).run(512),world.run(512))
        state=world.snapshot();self.assertEqual(World.restore(state).snapshot(),state)

if __name__=='__main__':unittest.main()
