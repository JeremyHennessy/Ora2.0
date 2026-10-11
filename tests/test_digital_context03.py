import copy,unittest
from experiments.digital_context03 import World,history,h
from experiments.digital_context03_audit import audit

class Context03(unittest.TestCase):
    def test_paid_fixed_routes_and_feedback_are_lawful_not_learning(self):
        for route in ('stationary','port0','port1','parity'):
            row=history(24990,route);m=audit(row)
            for ev in row['final']['events']:
                if 'attempt' in ev:
                    a=ev['attempt'];self.assertEqual(a['success'],int(a['port']==a['target']))
            self.assertFalse(m['learning'])
            if route=='stationary':self.assertGreater(m['births'],0)
            if route=='port1':self.assertEqual(m['successful_food'],0)

    def test_generic_paid_memory_and_self_write_fixture(self):
        row=history(24991,'memory_fixture');audit(row)
        events=row['final']['events']
        self.assertEqual(events[1]['after']['memory'][0],1)
        self.assertEqual(events[2]['after']['registers'][1],1)
        self.assertEqual(events[3]['self_write']['value'],1)
        self.assertEqual(row['final']['heat'],46) #34 formation plus12 body energy
        self.assertEqual(row['final']['constructor_remaining'],94)

    def test_forged_hidden_port_formation_and_checkpoint_refused(self):
        row=history(24990,'port0');audit(row)
        first=next(i for i,e in enumerate(row['final']['events']) if 'attempt' in e)
        for kind in ('target','formation','scheduler'):
            forged=copy.deepcopy(row)
            if kind=='target':forged['final']['events'][first]['attempt']['target']^=1
            if kind=='formation':forged['final']['formation'][0]['energy']=0
            if kind=='scheduler':forged['checkpoint']['last']+=1
            forged['hash']=h(forged['final'])
            with self.assertRaises(AssertionError):audit(forged)
        world=World(24990,'faithful','port0');world.run(64)
        self.assertEqual(World.restore(world.snapshot()).run(1536),world.run(1536))
        forged=copy.deepcopy(row['checkpoint']);forged['formation'][0]['energy']=True
        with self.assertRaises(AssertionError):World.restore(forged)

if __name__=='__main__':unittest.main()
