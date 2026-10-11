import copy,unittest
from experiments.digital_capacity03 import World,history,h
from experiments.digital_capacity03_audit import audit

class Capacity03(unittest.TestCase):
    def test_generic_endpoint_accepts_paid_capacity_and_refuses_impossible(self):
        # Prepared software witnesses; these seeds never enter a science panel.
        for route in ('fixed','padded_fixed'):
            row=history(25180,route);m=audit(row)
            self.assertEqual(row['final']['constructor_remaining'],128-len(row['genesis_program'])*3-16)
            self.assertFalse(m['learning'])
            # Birth reachability is the frozen capacity gate, not an assumed
            # software assertion. The same evaluator admits lawful extinction.
            for kind in ('formation','parentage','checkpoint'):
                forged=copy.deepcopy(row)
                if kind=='formation':forged['final']['formation'][0]['energy']=0
                if kind=='parentage':
                    event=next(e for e in forged['final']['events'] if 'writes' in e)
                    event['writes'][0]['source_unit']+=1
                if kind=='checkpoint':forged['checkpoint']['last']+=1
                forged['hash']=h(forged['final'])
                with self.assertRaises(AssertionError):audit(forged)

    def test_checkpoint_numeric_type_and_canonical_identity(self):
        world=World(25181,'witness');world.run(64)
        state=world.snapshot()
        self.assertEqual(World.restore(state).run(1536),world.run(1536))
        for value in (True,1.0):
            forged=copy.deepcopy(state);forged['formation'][0]['energy']=value
            with self.assertRaises(AssertionError):World.restore(forged)

if __name__=='__main__':unittest.main()
