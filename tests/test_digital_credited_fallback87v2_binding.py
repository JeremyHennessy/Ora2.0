"""One new SOURCE/NUMERIC group; all witnesses explicitly NON-PHYSICS."""
import ast
import copy
from fractions import Fraction
import hashlib
from pathlib import Path
import unittest
from experiments import digital_credited_fallback87_source as old_source
from experiments import digital_credited_fallback87v2_source as source
from experiments import digital_credited_fallback87v2_acceptance as acceptance

def perfect_numeric_witness():
    rows=[]
    for seed in acceptance.PRIMARY+acceptance.UNSEEN:
        index=(acceptance.PRIMARY if seed in acceptance.PRIMARY else acceptance.UNSEEN).index(seed)
        constant=index<2
        for d in acceptance.DESCRIPTORS:
            rows.append(dict(seed=seed,descriptor=list(d),completed=60,
                N=800,fixed_oracle_N=997 if constant else 500,
                E=14 if constant else 10,fixed_oracle_E=71 if constant else -20,
                common=12,correct_intact=12,correct_joint=12 if constant else 10,
                correct_model=10,correct_route=10,correct_misbound=10,
                older_uses=0 if constant else 1,observed_mixed=int(not constant)))
    return rows

class BindingV2Tests(unittest.TestCase):
    def test_separate_contract_ast_and_complete_numeric_endpoints(self):
        root=Path(source.__file__).parent
        for suffix in ('source','world','referee'):
            old=ast.parse((root/f'digital_credited_fallback87_{suffix}.py').read_bytes())
            new=ast.parse((root/f'digital_credited_fallback87v2_{suffix}.py').read_bytes())
            if suffix=='source':
                def strip(tree):
                    tree.body=[n for n in tree.body if not (isinstance(n,ast.Assign) and
                        any(isinstance(t,ast.Name) and t.id in ('VERSION','ADMISSION','CONTRACT_SHA256') for t in n.targets))]
                strip(old);strip(new)
            elif suffix=='world':
                for n in ast.walk(new):
                    if isinstance(n,ast.alias) and n.name=='digital_credited_fallback87v2_source':n.name='digital_credited_fallback87_source'
            else:
                for n in ast.walk(new):
                    if isinstance(n,ast.Constant) and n.value=='CREDITED-FALLBACK87-v2':n.value='CREDITED-FALLBACK87-v1'
            self.assertEqual(ast.dump(old),ast.dump(new))
        self.assertEqual(source.PRIMARY,old_source.PRIMARY)
        self.assertEqual(source.UNSEEN,old_source.UNSEEN)
        self.assertEqual(source.RESERVED,old_source.RESERVED)
        self.assertEqual(source.manifest()['targets_queried'],0)
        contract=root.parent/'docs/DIGITAL-CREDITED-FALLBACK87-PROSPECTIVE-CONTRACT-V2.md'
        # CI checks both exact known exports; actual custody still pins the
        # unmodified registered Windows contract and exact source archive.
        self.assertEqual(source.CONTRACT_SHA256,'8342c880706e5254c045995e3ca79ba09dbb4d0cca0717008214359aceb7e154')
        self.assertIn(hashlib.sha256(contract.read_bytes()).hexdigest(),{
            source.CONTRACT_SHA256,
            'f97b541a6b28edc11834e4b079368222298cee6afa4d99882ff652a0d54abbef'})
        for seed in source.PRIMARY+source.UNSEEN:
            source.admit(seed,source.ADMISSION)
            with self.assertRaises(AssertionError):source.admit(seed,old_source.ADMISSION)
        self.assertEqual(acceptance.tail(12,0),Fraction(1,4096))
        self.assertLessEqual(acceptance.tail(12,0),Fraction(1,180))
        self.assertEqual(acceptance.tail(12,4),Fraction(2517,65536))
        self.assertGreater(acceptance.tail(12,4),Fraction(1,900))
        self.assertEqual(acceptance.tail(0,0),1)
        perfect=perfect_numeric_witness();result=acceptance.interpret(perfect)
        self.assertEqual(result['confirmatory_family_size'],9)
        self.assertFalse(result['execution_admission'])
        self.assertTrue(all(d['arithmetic_mechanistic_paid_choice'] and d['arithmetic_finite_cohort_net_energy'] for d in result['descriptors']))
        self.assertTrue(all(d['joint_sign']==dict(wins=12,losses=0,ties=4,p='1/4096',passes=True) for d in result['descriptors']))
        self.assertTrue(all(d['banks']['primary']['generation_strata']['constant']['E_oracle_gain']<0 for d in result['descriptors']))
        negative=copy.deepcopy(perfect)
        for row in negative:row['E']=row['fixed_oracle_E']-1
        result=acceptance.interpret(negative)
        self.assertTrue(all(d['arithmetic_mechanistic_paid_choice'] and not d['arithmetic_finite_cohort_net_energy'] for d in result['descriptors']))
        null=copy.deepcopy(perfect)
        for row in null:row['correct_joint']=row['correct_intact']
        self.assertFalse(any(d['arithmetic_mechanistic_paid_choice'] for d in acceptance.interpret(null)['descriptors']))
        impossible=copy.deepcopy(perfect)
        for row in impossible:
            bank=source.PRIMARY if row['seed'] in source.PRIMARY else source.UNSEEN
            if bank.index(row['seed'])<2:row['correct_intact']=10
        result=acceptance.interpret(impossible)
        self.assertTrue(all(d['joint_sign']['p']=='2517/65536' and not d['arithmetic_mechanistic_paid_choice'] for d in result['descriptors']))
        for rows in (perfect[:-1],perfect[:-1]+[perfect[0]],perfect+[perfect[0]]):
            with self.assertRaises(AssertionError):acceptance.interpret(rows)
        wrong=copy.deepcopy(perfect);wrong[0]['common']=True
        with self.assertRaises(AssertionError):acceptance.interpret(wrong)
        tree=ast.parse((root/'digital_credited_fallback87v2_acceptance.py').read_bytes())
        self.assertEqual([n.module for n in tree.body if isinstance(n,ast.ImportFrom)],['fractions','math'])
        self.assertFalse(any(isinstance(n,ast.Import) for n in tree.body))
        kernel=ast.parse((root/'digital_memory80.py').read_bytes())
        step=next(n for n in ast.walk(kernel) if isinstance(n,ast.FunctionDef) and n.name=='step')
        fee=next(n.test for n in ast.walk(step) if isinstance(n,ast.If)
            and any(isinstance(x,ast.AugAssign) and isinstance(x.target,ast.Attribute) and x.target.attr=='constructor_remaining' for x in n.body))
        self.assertEqual(ast.dump(fee),ast.dump(ast.parse('self.tick==64',mode='eval').body))

if __name__=='__main__':unittest.main()
