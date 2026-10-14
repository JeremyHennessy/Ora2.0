"""Prepared domain/refusal witnesses only; no sampled population or paid truth."""
import ast
import copy
import inspect
from pathlib import Path
import unittest
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as kernel
from experiments import digital_functional69_admission as old
from experiments import digital_functional69_scientific_child as old_child
from experiments import digital_functional70_admission as admission
from experiments import digital_functional70_scientific_child as child
from experiments import digital_functional70_runplan as plan
from experiments import digital_functional70_cohort as cohort
from tests.test_digital_functional69_measure import pair,PROVENANCE


def summary(seed):
    return dict(verified=True,seed=seed,mode='faithful',inheritance_mode='parent_copy',route='ancestor',formation_cost=43,
        genesis_program_hash=admission.h(admission.ANCESTOR_WORDS),fuel_mode='renewed',births=12,
        turnover=dict(founder_expiry_tick=100,post_founder_instructions=128,maximum_generation=3,
            post_founder_paid_personal_births=1,post_founder_renewed_food=1,living_descendants=1,
            paid_personal_chains=[{'prepared':True}]))


def fixture(positive=()):
    populations=[];forks=[]
    for seed in admission.SEEDS:
        identity=f'{seed:064x}'  # Invented fixture ID, never resource/mutation hash.
        for mode,inheritance in [('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy')]:
            s=dict(verified=True,stage_credit=False,seed=seed,mode=mode,inheritance_mode=inheritance,
                births=12,deaths=3,successful_food=50,paid_copy_words=324,mutations=0,
                birth_edges=[dict(tick=10,parent=0,child=1,generation=1),dict(tick=20,parent=1,child=2,generation=2)])
            populations.append(dict(verified=True,stage_credit=False,summary=s,natural_history_hash=identity,provenance=PROVENANCE))
        for kind in ('parent','child'):
            proofs=pair(kind,food=2 if seed in positive else 1)
            for proof in proofs:proof.update(seed=seed,natural_history_hash=identity)
            forks+=proofs
    return populations,forks


class FreshDomainFixtures(unittest.TestCase):
    def setUp(self):
        self.trap=patch.object(kernel.World,'__init__',side_effect=AssertionError('World forbidden')).start()
        self.addCleanup(patch.stopall)
        self.request=dict(seed=71000,kind='population',mode='faithful',inheritance_mode='parent_copy')
        self.receipt=dict(PROVENANCE,references=16,treatment_worlds=0,all_paid_gates=True,original_restored_equal=True)
    def tearDown(self):self.assertEqual(self.trap.call_count,0)
    def test_fresh_and_old_domains_are_disjoint_and_old_rejects_fresh(self):
        self.assertTrue(set(admission.SEEDS).isdisjoint(old.SEEDS))
        for seed in admission.SEEDS:
            self.assertFalse(child.admit(dict(self.request,seed=seed),PROVENANCE))
            with self.assertRaises(AssertionError):old_child.admit(dict(self.request,seed=seed),PROVENANCE)
        self.assertEqual(old.SEEDS,(70000,70001,70002,70003,70200,70201,70202,70203))
    def test_old_science_reserves_software_and_coercions_refused(self):
        for seed in old.SEEDS+tuple(range(71100,71104))+tuple(range(71300,71304))+(1,2,True,71000.0,'71000'):
            with self.assertRaises(AssertionError):child.admit(dict(self.request,seed=seed),PROVENANCE)
            with self.assertRaises(AssertionError):admission.ordinary_gate(summary(seed))
    def test_ordinary_route_semantics_identical_ast(self):
        self.assertEqual(ast.dump(ast.parse(inspect.getsource(old.ordinary_gate)),include_attributes=False),
                         ast.dump(ast.parse(inspect.getsource(admission.ordinary_gate)),include_attributes=False))
        for seed in admission.SEEDS:self.assertTrue(admission.ordinary_gate(summary(seed)))
    def test_all16_evaluated_before_failed_aggregation(self):
        rows=[summary(s) for s in admission.SEEDS];rows[0]['births']=0
        with patch.object(admission,'ordinary_gate',wraps=admission.ordinary_gate) as gate:
            self.assertFalse(admission.ordinary_admission(rows,copy.deepcopy(rows)))
            self.assertEqual(gate.call_count,16)
    def test_every_lifecycle_shortfall_stays_failed(self):
        for field,value in [('founder_expiry_tick',None),('post_founder_instructions',127),('maximum_generation',2),
            ('post_founder_paid_personal_births',0),('post_founder_renewed_food',0),('living_descendants',0),('paid_personal_chains',[])]:
            s=summary(71000);s['turnover'][field]=value;self.assertFalse(admission.ordinary_gate(s))
        s=summary(71000);s['births']=11;self.assertFalse(admission.ordinary_gate(s))
    def test_duplicate_missing_and_changed_export_receipts_refused(self):
        rows=[summary(s) for s in admission.SEEDS]
        self.assertTrue(admission.ordinary_admission(rows,list(reversed(copy.deepcopy(rows)))))
        for other in (rows[:-1],rows[:-1]+[rows[0]]):
            with self.assertRaises(AssertionError):admission.ordinary_admission(rows,other)
        other=copy.deepcopy(rows);other[0]['births']=13
        with self.assertRaises(AssertionError):admission.ordinary_admission(rows,other)
    def test_treatment_requires_current_source_config_exact_integer16_zero(self):
        r=dict(self.request,mode='mutating')
        with self.assertRaises(AssertionError):child.admit(r,PROVENANCE)
        for field,value in [('source_sha256','d'*64),('configuration_sha256','d'*64),('references',15),('references',True),
                            ('treatment_worlds',1),('treatment_worlds',False),('all_paid_gates',False),('original_restored_equal',False)]:
            with self.assertRaises(AssertionError):child.admit(r,PROVENANCE,dict(self.receipt,**{field:value}))
        self.assertTrue(child.admit(r,PROVENANCE,self.receipt))
    def test_control_and_referee_channels_share_no_cross_slot_roles(self):
        for kind in ('fork','fork_ref'):
            for slot,control in [('parent','ancestor_value_control'),('child','inherited_source_control')]:
                for role in ('sham',control):
                    r=dict(seed=71203,kind=kind,slot_kind=slot,fork_role=role)
                    with self.assertRaises(AssertionError):child.admit(r,PROVENANCE)
                    self.assertTrue(child.admit(r,PROVENANCE,self.receipt))
                wrong='inherited_source_control' if slot=='parent' else 'ancestor_value_control'
                with self.assertRaises(AssertionError):child.admit(dict(r,fork_role=wrong),PROVENANCE,self.receipt)
        self.assertFalse(child.admit(dict(self.request,kind='population_ref'),PROVENANCE))
        self.assertTrue(child.admit(dict(self.request,kind='population_ref',mode='mutating'),PROVENANCE,self.receipt))
    def test_incomplete_source_refused_before_hash_or_producer(self):
        with patch.object(child,'sha',side_effect=AssertionError('Hash forbidden')) as hashes:
            with self.assertRaises(AssertionError):child.verify_source(Path.cwd(),{})
            names=ast.literal_eval(ast.parse(inspect.getsource(child.verify_source)).body[0].body[0].value.generators[0].iter)
            pins={'experiments/'+n+'.py':'a'*64 for n in names}
            for missing in ('digital_functional70_scientific_child','digital_functional70_admission','digital_functional69_measure'):
                with self.assertRaises(AssertionError):child.verify_source(Path.cwd(),{k:v for k,v in pins.items() if k!='experiments/'+missing+'.py'})
            self.assertEqual(hashes.call_count,0)
    def test_foreign_module_origin_refused(self):
        with patch.object(kernel,'__file__',str(Path.cwd()/'foreign.py')):
            with self.assertRaises(AssertionError):child.module_origins(Path.cwd())
    def test_all_paid_roles_precede_treatment_and_no_fresh_seed_aliases(self):
        schedule=plan.schedule();self.assertEqual(len(schedule),226)
        self.assertTrue(all(not r['treatment'] for r in schedule[:34]))
        self.assertTrue(all(r['treatment'] for r in schedule[34:]))
        self.assertEqual(len({(r['role'],r['export'],r['endpoint']) for r in schedule}),226)
        roles=plan.roles();self.assertEqual(len(roles),56)
        self.assertEqual({r['seed'] for r in roles},set(admission.SEEDS))
        self.assertEqual([(r['seed'],r['inheritance_mode']) for r in roles[8:24]],
                         [(s,i) for s in admission.SEEDS for i in ('parent_copy','ancestor_copy')])
    def test_prepared_both_bank_reachability_keeps_measurement69_and_assay70(self):
        p,f=fixture((71000,71200));result=cohort.cohort(p,f,PROVENANCE)
        self.assertTrue(result['replicated_bounded_functional_contribution'])
        self.assertEqual(result['version'],'DIGITAL-FUNCTIONAL-CONFIRMATION-70-v1')
        self.assertFalse(result['stage_credit']);self.assertFalse(result['learning']);self.assertFalse(result['selection'])
        self.assertTrue(result['scientific_acceptance_pending_independent_interpretation'])
        self.assertEqual(result['denominator'],dict(populations=24,families=8,slots=16,continuations=32))
    def test_single_bank_effect_not_replicated_or_pooled(self):
        for positive in (admission.PRIMARY,admission.UNSEEN):
            p,f=fixture(positive);self.assertFalse(cohort.cohort(p,f,PROVENANCE)['replicated_bounded_functional_contribution'])
    def test_null_child_preserved_despite_unrelated_generation_two(self):
        p,f=fixture((71000,71200));p[1]['summary']['birth_edges'][1]['parent']=99
        for proof in f[2:4]:proof.update(null=True,slot=None,target=None,transition_mask=None)
        result=cohort.cohort(p,f,PROVENANCE)
        self.assertTrue(result['slots'][1]['null']);self.assertEqual(len(result['slots']),16)
        self.assertFalse(result['families'][0]['result']['conditional_functional_contribution'])
    def test_wrong_population_identity_and_first_family_refused(self):
        for field,value in [('natural_history_hash','e'*64),('seed',70000),('seed',71100),('provenance',dict(PROVENANCE,configuration_sha256='d'*64))]:
            p,f=fixture();f[0][field]=value
            with self.assertRaises(AssertionError):cohort.cohort(p,f,PROVENANCE)
        p,f=fixture()
        for proof in f[:2]:proof['slot']['target']=99
        with self.assertRaises(AssertionError):cohort.cohort(p,f,PROVENANCE)
    def test_noop_tradeoff_censor_and_same_action_stay_negative(self):
        for kind in ('noop','tradeoff','censor','same_action'):
            p,f=fixture((71000,71200));a,b=f[:2]
            if kind=='noop':a['transition_mask']=b['transition_mask']=[]
            elif kind=='tradeoff':a['target']['births']=0
            elif kind=='censor':a['target']['censored']=True
            else:b['target']['signatures']=copy.deepcopy(a['target']['signatures'])
            self.assertFalse(cohort.cohort(p,f,PROVENANCE)['families'][0]['result']['conditional_functional_contribution'])
    def test_cohort_duplicates_and_incomplete_denominators_refused(self):
        p,f=fixture()
        for a,b in [(p[:-1],f),(p[:-1]+[p[0]],f),(p,f[:-1]),(p,f[:-1]+[f[0]])]:
            with self.assertRaises(AssertionError):cohort.cohort(a,b,PROVENANCE)


if __name__=='__main__':unittest.main()
