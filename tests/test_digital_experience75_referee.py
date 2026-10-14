"""Independent literal proof of bounded prepared data, not science admission."""
import copy,sys,unittest
from unittest.mock import patch
from experiments import digital_experience75_controls as controls,digital_experience75_referee as referee,digital_experience75_prepared as prepared,digital_experience75_history as generator
class Referee(unittest.TestCase):
    def test_literal_transition_agrees_for_all_primitives_and_alias_addresses(self):
        for op in controls.OPS:
            for a,b in ((0,1),(1,0),(15,15),(31,31)):
                for zero in (False,True):
                    state=dict(r=[15,7],m=list(range(8)),pc=0,feedback=1);code=[[op,a,b]]
                    self.assertEqual(referee.move(code,state,0,zero,1),controls.step(code,state,0,zero,1))
    def test_full_cold_fixture_resource_proof_both_orientations(self):
        for seed in (95074,95075):
            row=prepared.fixture(seed);proof=referee.audit(row,row['genesis_program'],software=True)
            self.assertEqual((proof['ticks'],proof['energy'],proof['heat'],proof['total_paid_cost'],proof['successes']),(5,23,67,67,1))
            self.assertTrue(proof['software_prepared']);self.assertFalse(proof['learning'])
    def test_software_context_cannot_be_admitted_as_science(self):
        row=prepared.fixture(95074)
        with self.assertRaises(AssertionError):referee.audit(row,row['genesis_program'])
    def test_forgeries_rejected_even_after_hash_recalculation(self):
        original=prepared.fixture(95074)
        for channel in ('energy','feedback','memory','penalty','control','formation'):
            row=copy.deepcopy(original)
            if channel in ('energy','feedback'):row['final']['events'][1]['after'][channel]+=1
            elif channel=='memory':row['final']['events'][1]['after']['memory'][0]=1
            elif channel=='penalty':row['final']['events'][1]['penalty']+=1
            elif channel=='control':row['final']['events'][1]['control']['shadow']['r'][0]=1
            else:row['final']['formation'][0]['energy']=0
            row['hash']=referee.h(row['final'])
            with self.assertRaises(AssertionError):referee.audit(row,row['genesis_program'],software=True)
    def test_expected_program_not_caller_selected_row_only(self):
        row=prepared.fixture(95074);different=copy.deepcopy(row['genesis_program']);different[5][0]=18
        with self.assertRaises(AssertionError):referee.audit(row,different,software=True)
    def test_no_producer_import_in_referee_source(self):
        import ast
        from pathlib import Path
        tree=ast.parse(Path(referee.__file__).read_text(encoding='utf-8'))
        self.assertTrue(all(not isinstance(n,ast.ImportFrom) for n in ast.walk(tree)))
        self.assertEqual({alias.name for n in tree.body if isinstance(n,ast.Import) for alias in n.names},{'hashlib','json'})
    def test_generator_refuses_reserves_and_complete_chunk_denominator(self):
        with patch.object(generator,'World',side_effect=RuntimeError('World reached')):
            for seed in (True,75100,75300,75008):
                with self.assertRaises(AssertionError):generator.batch(seed,'intact',0)
        self.assertEqual(generator.roles(0),[f'candidate{i}' for i in range(8)])
        self.assertEqual(generator.roles(1),[f'candidate{i}' for i in range(8,16)])
        self.assertEqual(len(generator.roles(2)),6)
        for chunk in (True,-1,3):
            with self.assertRaises(AssertionError):generator.roles(chunk)

if __name__=='__main__':unittest.main()
