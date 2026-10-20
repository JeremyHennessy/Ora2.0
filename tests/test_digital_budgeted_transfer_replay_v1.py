"""New independent replay/falsifier qualification, no primary population."""
import copy
import unittest
from experiments.digital_budgeted_transfer_v1 import Fixture,SOFTWARE_ONLY
from experiments.digital_budgeted_transfer_replay_v1 import replay,verify
from tests.test_digital_budgeted_transfer_v1 import WITNESS,FIXED

class ReplayTests(unittest.TestCase):
    def run_checked(self,code,**kw):
        f=Fixture(copy.deepcopy(code),admission=SOFTWARE_ONLY,**kw)
        result=f.run_fixture()
        self.assertTrue(verify(code,f.mask,f.order,f.mode,f.budget,f.rows,result,f.world.snapshot()))
        return f,result

    def test_reference_truth_table_controls_and_order(self):
        for mask in range(16):
            for mode in ('intact','memory_disabled','history_disrupted'):
                self.run_checked(WITNESS,mask=mask,mode=mode,order=(2,0,3,1,5,7,4,6))

    def test_allowed_instruction_semantics_and_unit_billing(self):
        code=[[7,4,1],[4,0,3],[4,1,1],[3,1,0],[2,0,1],[5,0,1],
              [8,0,9],[24,0,1],[25,0,10],[19,0,1],[20,1,0],[0,1,0],[6,0,0],[1,0,0],[7,0,1]]
        for mode in ('intact','memory_disabled','history_disrupted'):
            self.run_checked(code,mask=9,mode=mode)
        # Wrong branch/PC/write/read, not merely answer checking.
        f,result=self.run_checked(code,mask=6)
        bad=copy.deepcopy(f.world.snapshot());bad['entities']['0']['memory'][0]^=1
        with self.assertRaises(ValueError):verify(code,6,f.order,f.mode,f.budget,f.rows,result,bad)

    def test_exhaustion_and_partial_terminal_cost(self):
        f,result=self.run_checked([[7,2,1],[7,0,1]])
        self.assertEqual(result['stop'],'death')
        self.assertEqual(result['completed'],0)
        self.assertEqual(f.world.tick,200)
        # Authored negative fixture: always wrong on map0; seventh action
        # pays only its last1 energy. No price reduction or energy injection.
        code=[[7,2,1],[0,1,0],[4,0,1],[25,5,5],[7,0,6],[4,0,0]]
        code += [[7,0,i+1] for i in range(6,25)] + [[6,0,0],[7,0,1]]
        f,result=self.run_checked(code,mask=0)
        self.assertEqual(result['stop'],'death')
        self.assertEqual(f.world.events[-1]['penalty'],1)
        self.assertEqual(result['completed'],7)
        self.run_checked(FIXED,budget=20)
        self.run_checked([[7,2,1],[7,0,1]],budget=83)

    def test_reject_forged_vm_resource_control_and_missing_rows(self):
        f,result=self.run_checked(WITNESS,mask=5,mode='history_disrupted')
        original=f.world.snapshot()
        for field in ('pc','register','memory','energy','food','lease','constructor','scheduler','input','hash','death','intervention','row','reason','missing'):
            world=copy.deepcopy(original);rows=copy.deepcopy(f.rows);res=copy.deepcopy(result)
            e=world['entities'].get('0')
            if field=='pc':e['pc']=(e['pc']+1)%len(WITNESS)
            elif field=='register':e['registers'][0]^=1
            elif field=='memory':e['memory'][0]^=1
            elif field=='energy':e['energy']-=1
            elif field=='food':world['food'].pop(next(iter(world['food'])))
            elif field=='lease':world['leases']['999']=0
            elif field=='constructor':world['constructor_remaining']-=1
            elif field=='scheduler':world['last']=1
            elif field=='input':world['admitted']+=1
            elif field=='hash':world['events'][0]['state_hash']='0'*64
            elif field=='death':world['deaths']+=1
            elif field=='intervention':next(x for x in rows if x['intervention'])['intervention']['delivered']=1
            elif field=='row':rows.pop()
            elif field=='reason':res['stop']='death'
            else:res['planned'].pop()
            with self.subTest(field=field):
                with self.assertRaises(ValueError):verify(WITNESS,5,f.order,f.mode,f.budget,rows,res,world)

    def test_restore_rejects_rehashed_illegal_state(self):
        from experiments.digital_budgeted_transfer_replay_v1 import digest
        f=Fixture(WITNESS,mask=9,admission=SOFTWARE_ONLY)
        for _ in range(18): self.assertTrue(f.step())
        sealed=f.snapshot()
        sealed['payload']['world']['entities']['0']['registers'][0]^=1
        sealed['sha256']=digest(sealed['payload'])
        with self.assertRaises(ValueError):Fixture.restore(sealed,admission=SOFTWARE_ONLY)

    def test_no_producer_import_in_independent_interpreter(self):
        import ast
        from pathlib import Path
        import experiments.digital_budgeted_transfer_replay_v1 as module
        tree=ast.parse(Path(module.__file__).read_text())
        imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertEqual([alias.name for n in imports for alias in getattr(n,'names',[])],['hashlib','json'])

if __name__=='__main__':unittest.main()
