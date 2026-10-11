import copy,unittest
from experiments.digital_opportunity06 import history,h,World
from experiments.digital_opportunity06_audit import audit

class Opportunity06(unittest.TestCase):
    def test_generic_interpreter_refuses_impossible_rehashed_records(self):
        row=history(25589,'alternating');m=audit(row)
        self.assertGreater(m['successful_food'],0)
        for kind in ('stock','checkpoint'):
            bad=copy.deepcopy(row)
            if kind=='stock':bad['final']['heat']+=20
            else:bad['checkpoint']['formation'][0]['energy']=True
            bad['hash']=h(bad['final'])
            with self.assertRaises(AssertionError):audit(bad)

    def test_failed_attempt_retains_resource_but_pays_instruction(self):
        row=history(25589,'alternating');audit(row)
        failed=next(e for e in row['final']['events'] if 'attempt' in e and not e['attempt']['success'])
        state=World(25589,route='alternating')
        while state.tick<failed['tick']-1:state.step()
        stock=len(state.food);heat=state.heat;energy=state.entities[0]['energy']
        state.step();self.assertEqual(len(state.food),stock)
        self.assertEqual(state.heat,heat+1);self.assertEqual(state.entities[0]['energy'],energy-1)

if __name__=='__main__':unittest.main()
