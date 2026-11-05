"""NEW metadata/ancestry/selection predicate/AST checks; no World replay."""
import ast
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'experiments/digital_eka1_selection_replay_v1.py'
spec = importlib.util.spec_from_file_location('eka1_selection_metadata_only', PATH)
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)


def request():
    return dict(schema='ORA-EKA1-ORIGINAL-SELECTION-REPLAY-v1',original_raw_sha256='a'*64,
        assignment_id='synthetic-metadata-not-World',assigned_stop_tick=4096,
        configuration=dict(seed=0,mode='mutating',fuel_mode='renewed',inheritance_mode='parent_copy',dose=1))


class SelectionMetadata(unittest.TestCase):
    def test_both_strata_request_metadata_only(self):
        for dose in (1,8):
            value=request();value['configuration']['dose']=dose
            self.assertEqual(s.request_metadata(value)['dose'],dose)

    def test_no_shortened_horizon_or_boolean_identity(self):
        for horizon in (4095,4097,True):
            value=request();value['assigned_stop_tick']=horizon
            with self.assertRaises(ValueError):s.request_metadata(value)
        value=request();value['configuration']['seed']=True
        with self.assertRaises(ValueError):s.request_metadata(value)

    def test_no_nonordinary_lineage_or_extra_outcome_selector(self):
        for key,value in [('mode','faithful'),('inheritance_mode','ancestor_copy'),('fuel_mode','no_inflow'),('dose',True)]:
            row=request();row['configuration'][key]=value
            with self.assertRaises(ValueError):s.request_metadata(row)
        row=request();row['fitness']=100
        with self.assertRaises(ValueError):s.request_metadata(row)

    def test_birth_chain_no_orphans_reused_ids_or_wrong_generation(self):
        registry={0:(None,0)}
        s.extend_ancestry(registry,0,dict(id=1,parent=0,generation=1))
        s.extend_ancestry(registry,1,dict(id=2,parent=1,generation=2))
        self.assertEqual(registry[2],(1,2))
        for actor,child in [(3,dict(id=4,parent=3,generation=1)),(0,dict(id=1,parent=0,generation=1)),
                            (1,dict(id=3,parent=1,generation=1)),(0,dict(id=True,parent=0,generation=1)),
                            (1,dict(id=3,parent=True,generation=2))]:
            with self.assertRaises(ValueError):s.extend_ancestry(registry,actor,child)

    def test_eligibility_ignores_feedback_success_and_fitness(self):
        base=dict(born=True,ordinary_mutating_ancestry=True,tick=2047,forage=dict(packet=64,success=0),feedback=0)
        self.assertTrue(s.earned_read(base))
        base['feedback']=1;base['forage']['success']=1;base['fitness']=-100
        self.assertTrue(s.earned_read(base))
        for field,value in [('born',False),('ordinary_mutating_ancestry',False),('forage',None),('tick',2048)]:
            row=base.copy();row[field]=value;self.assertFalse(s.earned_read(row))
        row=base.copy();row['forage']=dict(packet=None);self.assertFalse(s.earned_read(row))
        row['forage']=dict(packet=63);self.assertFalse(s.earned_read(row))

    def test_ast_one_genesis_and_whole_replay_before_selector(self):
        tree=ast.parse(PATH.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='replay_original_selection')
        text=ast.unparse(fn)
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='World' for n in ast.walk(fn)),1)
        self.assertLess(text.index('parse_checkpoint('),text.index('runtime_sources()'))
        self.assertLess(text.index('canonical(actual) !='),text.index('selector.select_first(rows)'))
        loops=[n for n in ast.walk(fn) if isinstance(n,ast.While)]
        self.assertEqual(len(loops),1);self.assertNotIn('selected',ast.unparse(loops[0].test))
        self.assertLess(text.index('world.snapshot()'),text.index('world.step()'))
        self.assertNotIn('__dict__',text)
        self.assertIn("'ancestor'",text)

    def test_ast_imports_are_lazy_and_no_authority_or_zeroing(self):
        tree=ast.parse(PATH.read_bytes());text=PATH.read_text()
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and (n.module or '').startswith('experiments') for n in tree.body))
        self.assertFalse(any(isinstance(n,ast.If) for n in tree.body))
        for marker in ['actual_world_outcomes_zeroed=False','native_registration_authenticated=False',
                       'original_owner_authenticated=False','physical_raw_custody_authenticated=False',
                       'execution_authorized=False','scientific_admission=False']:
            self.assertIn(marker,text)
        self.assertIn("tick=world.tick+1",text)
        self.assertIn("selected_context['tick']-1",text)

    def test_bound_metadata_dependencies_without_executing_them(self):
        for name,digest in s.INPUT_PINS.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)


if __name__=='__main__':unittest.main()
