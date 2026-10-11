import copy,json,unittest
from pathlib import Path
from experiments.digital_memory_binding import measure
from experiments.digital_memory_binding_audit import audit,h


class Binding(unittest.TestCase):
    def test_complete_charged_programs(self):
        config=json.loads((Path(__file__).parents[1]/'data/digital-memory-binding01-fixtures.json').read_text())
        for fixture in config['programs']:
            for orientation in (0,1):
                row=measure(fixture['program'],orientation); result=audit(row)
                self.assertEqual(result['instructions'],len(row['events']))
                self.assertEqual(result['formation_cost'],3*len(fixture['program'])+13)
        self.assertGreater(audit(measure(config['programs'][3]['program'],0))['code_writes'],0)

    def test_same_evaluator_refuses_unpaid_or_forged_state(self):
        row=measure([[4,0,0],[6,0,0],[7,0,0]],0); audit(row)
        for target in ('formation','energy','code'):
            forged=copy.deepcopy(row)
            if target=='formation': forged['formation'][0]['energy']=0
            if target=='energy': forged['final']['constructor_remaining']+=1
            if target=='code': forged['final']['code'][0]=10
            forged['state_hash']=h(forged['final'])
            with self.assertRaises(AssertionError): audit(forged)

    def test_typed_finite_program_boundary(self):
        for program in ([],[[True,0,0]],[[32,0,0]],[[0,0]],[[0,0,0]]*33):
            with self.assertRaises(AssertionError): measure(program,0)
        row=measure([[31,0,0]],0)
        self.assertEqual(audit(row)['instructions'],12)


if __name__=='__main__': unittest.main()
