"""Prepared cohort/schedule fixtures; proof-shaped data are not paid history."""
import copy,unittest
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as kernel
from experiments import digital_functional69_runplan as plan
from experiments import digital_functional69_cohort as projection
from tests.test_digital_functional69_measure import pair,PROVENANCE


def fixture(positive=()):
    populations=[];forks=[]
    for seed in plan.SEEDS:
        identity=f'{seed:064x}'
        for mode,inheritance in [('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy')]:
            summary=dict(verified=True,stage_credit=False,seed=seed,mode=mode,inheritance_mode=inheritance,
                births=12,deaths=3,successful_food=50,paid_copy_words=324,mutations=0,
                birth_edges=[dict(tick=10,parent=0,child=1,generation=1),dict(tick=20,parent=1,child=2,generation=2)])
            populations.append(dict(verified=True,stage_credit=False,summary=summary,natural_history_hash=identity,provenance=PROVENANCE))
        for kind in ('parent','child'):
            proofs=pair(kind,food=2 if seed in positive else 1)
            for proof in proofs:proof.update(seed=seed,natural_history_hash=identity)
            forks+=proofs
    return populations,forks


class CohortPlanFixtures(unittest.TestCase):
    def setUp(self):
        self.trap=patch.object(kernel.World,'__init__',side_effect=AssertionError('World forbidden')).start();self.addCleanup(patch.stopall)
    def tearDown(self):self.assertEqual(self.trap.call_count,0)
    def test_frozen_roles_order_and_both_control_domains(self):
        roles=plan.roles();self.assertEqual(len(roles),56)
        self.assertEqual([(r['seed'],r['inheritance_mode']) for r in roles[8:24]],[(s,i) for s in plan.SEEDS for i in ('parent_copy','ancestor_copy')])
        self.assertEqual({r['fork_role'] for r in roles if r.get('slot_kind')=='child'},{'sham','inherited_source_control'})
    def test_all16_reference_pairs_before_any_treatment_and226_bound(self):
        schedule=plan.schedule();self.assertEqual(len(schedule),226)
        self.assertTrue(all(not s['treatment'] for s in schedule[:34]));self.assertTrue(all(s['treatment'] for s in schedule[34:]))
        self.assertEqual(len({(s['role'],s['export'],s['endpoint']) for s in schedule}),226)
    def test_primary_and_unseen_reachability_not_stage_credit(self):
        p,f=fixture((70000,70201));result=projection.cohort(p,f,PROVENANCE)
        self.assertTrue(result['replicated_bounded_functional_contribution']);self.assertEqual(result['qualifying_cases'],dict(primary=1,unseen=1))
        self.assertFalse(result['stage_credit']);self.assertTrue(result['requires_authenticated_full_history'])
        self.assertEqual(result['denominator'],dict(populations=24,families=8,slots=16,continuations=32))
    def test_primary_only_not_pooled_into_unseen_replication(self):
        p,f=fixture((70000,70001,70002,70003));result=projection.cohort(p,f,PROVENANCE)
        self.assertFalse(result['replicated_bounded_functional_contribution']);self.assertEqual(result['qualifying_cases']['unseen'],0)
    def test_duplicate_missing_reserved_and_provenance_refused(self):
        p,f=fixture()
        for a,b in [(p[:-1],f),(p[:-1]+[p[0]],f),(p,f[:-1]),(p,f[:-1]+[f[0]])]:
            with self.assertRaises(AssertionError):projection.cohort(a,b,PROVENANCE)
        for section in ('population','fork'):
            a,b=copy.deepcopy((p,f))
            if section=='population':a[0]['summary']['seed']=70100
            else:b[0]['seed']=70100
            with self.assertRaises(AssertionError):projection.cohort(a,b,PROVENANCE)
        a,b=copy.deepcopy((p,f));b[0]['provenance']=dict(PROVENANCE,source_sha256='d'*64)
        with self.assertRaises(AssertionError):projection.cohort(a,b,PROVENANCE)
    def test_forks_must_bind_correct_natural_history_and_first_actual_family(self):
        p,f=fixture();f[0]['natural_history_hash']='e'*64
        with self.assertRaises(AssertionError):projection.cohort(p,f,PROVENANCE)
        p,f=fixture()
        for proof in f[:2]:proof['slot']['target']=99
        with self.assertRaises(AssertionError):projection.cohort(p,f,PROVENANCE)
    def test_null_child_retained_despite_unrelated_generation_two(self):
        p,f=fixture((70000,70200));natural=p[1]['summary']
        natural['birth_edges'][1]['parent']=99
        for proof in f[2:4]:proof.update(null=True,slot=None,target=None,transition_mask=None)
        result=projection.cohort(p,f,PROVENANCE)
        self.assertTrue(result['slots'][1]['null']);self.assertFalse(result['families'][0]['result']['conditional_functional_contribution'])
        self.assertEqual(len(result['slots']),16)
    def test_noop_censor_tradeoff_and_action_equality_are_preserved_negatives(self):
        for change in ('noop','censor','tradeoff','same_action'):
            p,f=fixture((70000,70200));a,b=f[:2]
            if change=='noop':a['transition_mask']=b['transition_mask']=[]
            elif change=='censor':a['target']['censored']=True
            elif change=='tradeoff':a['target']['births']=0
            else:b['target']['signatures']=copy.deepcopy(a['target']['signatures'])
            result=projection.cohort(p,f,PROVENANCE);self.assertFalse(result['families'][0]['result']['conditional_functional_contribution'])


if __name__=='__main__':unittest.main()
