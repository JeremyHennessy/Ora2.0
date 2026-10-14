"""Prepared non-learning fixtures only; registered environments are forbidden."""
import copy
import unittest
from unittest.mock import patch
from experiments import digital_cognitive76_source as source
from experiments import digital_cognitive76_controls as controls
from experiments import digital_cognitive76_world as world
from experiments.digital_cognitive76_prepared import fixture
from experiments.digital_cognitive76_referee import audit, move

def local(): return dict(r=[3,1],m=[0]*8,pc=0,feedback=1)

class Cognitive76(unittest.TestCase):
    def test_not_all_four_bit_values_and_operand_aliases(self):
        for value in range(16):
            for a in (0,1,30,31):
                s=local();s['r'][a%2]=value
                out=move([[21,a,31]],s,1,False,0)
                self.assertEqual(out['r'][a%2],value^15)
                self.assertEqual(out['r'][1-a%2],s['r'][1-a%2])
    def test_source_full_unscreened_ancestry(self):
        bank=source.manifest();self.assertEqual(bank,source.manifest())
        self.assertEqual([r['sample_id'] for r in bank['candidates']],list(range(16)))
        for row in bank['candidates']:
            self.assertEqual(len(row['draws']),4);self.assertIsNone(row['parent'])
            self.assertFalse(row['performance_selection']);self.assertFalse(row['resampling'])
            self.assertEqual(row['program_sha256'],source.digest(row['program']))
            for draw in row['draws']:
                self.assertEqual(draw['sha256'],source.digest(['cognitive76-source',76,row['sample_id'],draw['slot'],draw['field']]))
            self.assertEqual(row['program'][15],[19,0,1])
            self.assertEqual(row['program'][18],[20,1,0])
    def test_equal_formation_and_blank_state(self):
        for p in source.programmes().values():
            self.assertEqual(len(p),20);self.assertEqual(3*len(p)+16,76)
            self.assertEqual(p[:5],source.PREFIX)
    def test_compiler_refuses_channels_outside_prediction_abi(self):
        for atoms in ([[[21,1,0],[18,0,0]]],):
            with self.assertRaises(ValueError):source.compile_atoms(atoms)
        for atoms in ([[21,1,0],[18,0,0]],[[20,0,0],[18,0,0]],[[21,0,True],[18,0,0]]):
            with self.assertRaises(ValueError):source.compile_atoms(atoms)
    def test_model_disabled_keeps_truthful_feedback_pc_registers(self):
        before=local();after=move([[20,1,0]],before,1,False,0)
        result,annotation=controls.Control([[20,1,0]],before,'model_disabled',95076).apply(before,after)
        self.assertEqual(result['m'],[0]*8)
        for key in ('r','pc','feedback'):self.assertEqual(result[key],after[key])
        self.assertTrue(annotation['rewrites'])
    def test_misbound_preserves_native_value_but_changes_origin_binding(self):
        before=local();before['m'][:2]=[2,4]
        after=move([[20,1,0]],before,1,False,0)
        result,_=controls.Control([[20,1,0]],before,'history_misbound',95076).apply(before,after)
        self.assertEqual(result['m'][:2],[3,4])
        for key in ('r','pc','feedback'):self.assertEqual(result[key],after[key])
    def test_typed_control_refusals(self):
        for code in ([[21,0,True]],[[22,0,0]],[[21,-1,0]]):
            with self.assertRaises(ValueError):controls.Control(code,local(),'intact',95076)
        bad=local();bad['r'][0]=True
        with self.assertRaises(ValueError):controls.Control([[21,0,0]],bad,'intact',95076)
    def test_first_choice_overwrites_ephemeral_channels(self):
        p=source.references()['fixed_cognitive'];s=local();s['pc']=5;s['r']=[15,15];s['m'][:2]=[2,7]
        s=move(p,s,0,False,1);s=move(p,s,0,False,1)
        self.assertEqual(s['r'],[7,1]);self.assertEqual(s['pc'],7)
    def test_no_registered_or_reserve_context_in_prepared_tests(self):
        with patch.object(world,'h',side_effect=RuntimeError('context reached')):
            for seed in (True,77500,77700,77408,-1):
                with self.assertRaises(AssertionError):world.World(seed)
    def test_actual_nonlearning_paid_cycles_independently_proved(self):
        with patch.object(world.World,'__init__',side_effect=RuntimeError('scientific genesis forbidden')):
            for seed,ticks,energy,heat in ((95076,11,37,91),(95077,18,26,102)):
                row=fixture(seed);proof=audit(row,source.references()['fixed_cognitive'],software=True)
                self.assertEqual((proof['ticks'],proof['energy'],proof['heat']),(ticks,energy,heat))
                self.assertEqual(row['final']['entities']['0']['memory'],[0]*8)
                self.assertEqual(proof['successes'],2);self.assertEqual(proof['formation_cost'],76)
    def test_controls_do_not_repair_nonlearning_reference(self):
        for seed in (95076,95077):
            rows=[fixture(seed,m) for m in controls.MODES]
            for row in rows:audit(row,source.references()['fixed_cognitive'],software=True)
            physical=[[(e['decoded'],e.get('attempt'),e['after']) for e in r['final']['events']] for r in rows]
            self.assertEqual(physical[0],physical[1]);self.assertEqual(physical[0],physical[2])
    def test_referee_rejects_rehashed_wrong_physics(self):
        row=fixture(95077);row=copy.deepcopy(row)
        next(e for e in row['final']['events'] if e['tick']>5 and 'attempt' in e)['attempt']['target']^=1
        row['hash']=world.h(row['final'])
        with self.assertRaises(AssertionError):audit(row,source.references()['fixed_cognitive'],software=True)

if __name__=='__main__':unittest.main()
