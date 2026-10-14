"""Prepared schedule/gate receipts only. No World, paid history or bank query."""
import copy
import unittest
from unittest.mock import patch
from experiments import digital_pressure71_admission as admission
from experiments import digital_pressure71_runplan as runplan

def summary(seed):
    # Authored reachability data, not a naturally produced/reference-paid route.
    tuples=[(0,1,1),(0,2,1),(1,3,2),(2,4,2),(3,5,3),(4,6,3),
            (5,7,4),(6,8,4),(3,9,3),(5,10,4),(7,11,5),(8,12,5)]
    edges=[dict(parent=p,child=c,generation=g,tick=100*i,parent_personal_food=1,
                write_ids=list(range(27*(i-1),27*i))) for i,(p,c,g) in enumerate(tuples,1)]
    return dict(verified=True,seed=seed,mode='faithful',inheritance_mode='parent_copy',
        route='ancestor',fuel_mode='renewed',formation_cost=43,
        genesis_program_hash=admission.digest(admission.ANCESTOR),dose=8,horizon=4096,
        software_only=False,ticks=4096,births=12,birth_edges=edges,
        turnover=dict(founder_expiry_tick=853,post_founder_instructions=3243,
            maximum_generation=5,post_founder_paid_personal_births=4,
            post_founder_renewed_food=1,living_descendants=1,
            paid_personal_chains=[[1,3,5],[2,4,6],[1,3,9]]))

def receipt():
    rows=[dict(export=e,seed=s,dose=8,raw_sha256='c'*64,proof_sha256='d'*64)
          for e in runplan.EXPORTS for s in admission.SEEDS]
    return dict(version=admission.VERSION,source_sha256='a'*64,configuration_sha256='b'*64,
        references=16,treatment_worlds=0,original_restored_equal=True,all_paid_gates=True,
        native_children=34,raw_proof_pairs=16,reference_receipts=rows,
        reference_bundle_sha256=admission.digest(rows))


class RunnerBoundaryTests(unittest.TestCase):
    def test_fixed_role_and_endpoint_counts(self):
        roles=runplan.roles();calls=runplan.schedule()
        self.assertEqual(len(roles),104);self.assertEqual(len(calls),418)
        self.assertEqual(sum(r['kind']=='population' for r in roles),40)
        self.assertEqual(sum(r['kind']=='fork' for r in roles),64)
        self.assertEqual(len({r['name'] for r in roles}),104)
        self.assertEqual(sum(r['endpoint']=='raw' for r in calls),208)

    def test_all16_ordinary_endpoints_before_first_treatment(self):
        calls=runplan.schedule();self.assertFalse(any(r['treatment'] for r in calls[:34]))
        self.assertTrue(all(r['treatment'] for r in calls[34:]))
        self.assertEqual(calls[0]['endpoint'],calls[1]['endpoint'])
        self.assertEqual({r['export'] for r in calls[2:34]},set(runplan.EXPORTS))

    def test_forks_bind_same_seed_dose_parent_copy_natural(self):
        roles={r['name']:r for r in runplan.roles()}
        for role in roles.values():
            self.assertIn(role['seed'],admission.SEEDS)
            self.assertNotIn(role['seed'],tuple(range(74100,74104))+tuple(range(74300,74304)))
            if role['kind']=='fork':
                natural=roles[role['natural_role']]
                self.assertEqual((natural['seed'],natural['dose'],natural['mode'],natural['inheritance_mode']),
                                 (role['seed'],role['dose'],'mutating','parent_copy'))

    def test_prepared_whole_paid_shape_and_all16_evaluation(self):
        original=[summary(s) for s in admission.SEEDS];restored=copy.deepcopy(original)
        actual=admission.ordinary_gate
        with patch.object(admission,'ordinary_gate',wraps=actual) as call:
            self.assertTrue(admission.ordinary_admission(original,restored))
            self.assertEqual(call.call_count,16)
        original[0]['turnover']['living_descendants']=0;restored=copy.deepcopy(original)
        with patch.object(admission,'ordinary_gate',wraps=actual) as call:
            self.assertFalse(admission.ordinary_admission(original,restored))
            self.assertEqual(call.call_count,16)

    def test_unchanged70_numeric_failures_remain_failures(self):
        for field,value in [('post_founder_instructions',127),('maximum_generation',2),
                            ('post_founder_paid_personal_births',0),('post_founder_renewed_food',0),
                            ('living_descendants',0),('paid_personal_chains',[])]:
            row=summary(admission.SEEDS[0]);row['turnover'][field]=value
            self.assertFalse(admission.ordinary_gate(row),field)

    def test_other_lineage_g4_does_not_rescue_neutral_first_child(self):
        row=summary(admission.SEEDS[0])
        for edge in row['birth_edges']:
            if edge['child'] in (7,10):edge['parent']=6
        self.assertFalse(admission.ordinary_gate(row))

    def test_missing_later_cohort_cannot_pass(self):
        row=summary(admission.SEEDS[0])
        row['birth_edges']=row['birth_edges'][:7]
        for target in range(8,13):
            row['birth_edges'].append(dict(parent=0,child=target,generation=1,
                tick=target*100,parent_personal_food=1,
                write_ids=list(range(27*(target-1),27*target))))
        row['turnover']['paid_personal_chains']=row['turnover']['paid_personal_chains'][:2]
        row['turnover']['maximum_generation']=4
        self.assertFalse(admission.ordinary_gate(row))

    def test_scope_seed_dose_and_boolean_fields_refused(self):
        for key,value in [('seed',74100),('seed',71000),('seed',True),('dose',1),
                          ('dose',True),('horizon',512),('software_only',True),('formation_cost',True)]:
            row=summary(admission.SEEDS[0]);row[key]=value
            with self.assertRaises(AssertionError):admission.ordinary_gate(row)

    def test_edge_generation_reuse_and_fake_personal_chain_refused(self):
        for defect in ('generation','write','chain'):
            row=summary(admission.SEEDS[0])
            if defect=='generation':row['birth_edges'][6]['generation']=3
            elif defect=='write':row['birth_edges'][1]['write_ids']=row['birth_edges'][0]['write_ids']
            else:row['turnover']['paid_personal_chains']=[[1,4,6]]
            with self.assertRaises(AssertionError):admission.ordinary_gate(row)

    def test_duplicate_missing_or_unequal_reference_set_refused(self):
        original=[summary(s) for s in admission.SEEDS]
        for defect in ('duplicate','missing','unequal'):
            restored=copy.deepcopy(original)
            if defect=='duplicate':restored[-1]=copy.deepcopy(restored[0])
            elif defect=='missing':restored.pop()
            else:restored[-1]['turnover']['living_descendants']=0
            with self.assertRaises(AssertionError):admission.ordinary_admission(original,restored)

    def test_prepared_receipt_schema_bindings_only(self):
        self.assertTrue(admission.require_durable_admission(receipt(),'a'*64,'b'*64))
        for key,value in [('references',True),('treatment_worlds',1),('native_children',33),
                          ('all_paid_gates',1),('source_sha256','e'*64),('raw_proof_pairs',15)]:
            row=receipt();row[key]=value
            with self.assertRaises(AssertionError):admission.require_durable_admission(row,'a'*64,'b'*64)

    def test_rehashed_duplicate_or_reserve_receipt_refused(self):
        for defect in ('duplicate','reserve','dose'):
            row=receipt()
            if defect=='duplicate':row['reference_receipts'][-1]=copy.deepcopy(row['reference_receipts'][0])
            elif defect=='reserve':row['reference_receipts'][-1]['seed']=74300
            else:row['reference_receipts'][-1]['dose']=1
            row['reference_bundle_sha256']=admission.digest(row['reference_receipts'])
            with self.assertRaises(AssertionError):admission.require_durable_admission(row,'a'*64,'b'*64)

    def test_raw_and_proof_mutation_and_fork_need_bound_receipt(self):
        provenance=dict(source_sha256='a'*64,configuration_sha256='b'*64)
        for kind in ('population','population_ref','fork','fork_ref'):
            request=dict(seed=admission.SEEDS[0],dose=1,kind=kind,mode='mutating',
                inheritance_mode='parent_copy',slot_kind='child',fork_role='inherited_source_control')
            with self.assertRaises(AssertionError):admission.admit(request,provenance)
            self.assertTrue(admission.admit(request,provenance,receipt()))
            bad=receipt();bad['treatment_worlds']=1
            with self.assertRaises(AssertionError):admission.admit(request,provenance,bad)

    def test_ordinary_metadata_and_early_membership_guard(self):
        provenance=dict(source_sha256='a'*64,configuration_sha256='b'*64)
        for kind in ('population','population_ref'):
            request=dict(seed=admission.SEEDS[0],dose=8,kind=kind,mode='faithful',inheritance_mode='parent_copy')
            self.assertFalse(admission.admit(request,provenance))
            for key,value in [('seed',74300),('dose',1),('dose',True),('inheritance_mode','ancestor_copy')]:
                bad=dict(request);bad[key]=value
                with self.assertRaises(AssertionError):admission.admit(bad,provenance)


if __name__=='__main__':unittest.main()
