"""Frozen 24 named prepared cases. No World or scientific seed execution.

These authored partial witnesses cover domains and evaluator reachability.
Complete raw histories, restored exports and physical recorder fixtures remain
separate required qualification steps; this suite alone grants no admission.
"""
import json
import unittest
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as producer
from experiments import digital_sharedlineage68_transition as transition
from experiments import digital_sharedlineage68_fork_interpret as referee
from experiments import digital_sharedlineage68_world as wrapper
from experiments import evidence_write_grant68 as grant
from test_digital_sharedlineage68_components import PreparedComponents as C
from test_digital_sharedlineage68_transition_components import PreparedTransitionComponents as T,prepared,summary,PROVENANCE
from experiments import digital_sharedlineage68_admission as admission
from experiments import digital_sharedlineage68_observe as observer
from test_digital_sharedlineage68_observe_components import PreparedObservationComponents as O
from test_digital_sharedlineage68_boundary_independence import IndependentBoundary as B


class FrozenPrepared(unittest.TestCase):
    def setUp(self):
        trap=patch.object(producer.World,'__init__',side_effect=AssertionError('Prepared suite prohibits World'))
        self.spy=trap.start();self.addCleanup(trap.stop)
        self.addCleanup(lambda:self.assertEqual(self.spy.call_count,0))

    def chronological_neutral_slots(self):
        state,slot=prepared();words=slot['certificates']
        writes=[dict(w) for w in words]
        for w in writes:w.pop('actor')
        child=transition.clone(state['entities'][1])
        events=[dict(actor=0,tick=27,writes=writes),dict(actor=0,tick=40,birth=dict(child=child,write_ids=list(range(27))),state_hash='d'*64)]
        # A later, higher scoring newborn cannot replace the first chronological slot.
        later=transition.clone(child);later.update(id=3,energy=64)
        events.append(dict(actor=0,tick=41,birth=dict(child=later,write_ids=list(range(27))),state_hash='e'*64))
        final=dict(events=events);row=dict(seed=1,mode='mutating',inheritance_mode='parent_copy',final=final,hash=transition.h(final))
        slots=transition.slots_from_audited(row,dict(seed=1,verified=True))
        self.assertEqual(slots[1]['target'],1);self.assertEqual(slots[1]['tick'],40)
        self.assertIsNone(slots[2]);self.assertEqual(slots[1]['certificates'],words)

    def paid_endpoint_gate(self):
        self.assertTrue(admission.ordinary_gate(summary(69000)))
        for key,value in [('founder_expiry_tick',None),('post_founder_instructions',127),
                          ('maximum_generation',2),('post_founder_paid_personal_births',0),
                          ('post_founder_renewed_food',0),('paid_personal_chains',[]),('living_descendants',0)]:
            candidate=summary(69000);candidate['turnover'][key]=value
            self.assertFalse(admission.ordinary_gate(candidate),key)

    def null_noop_retention(self):
        T.test_sham_exact_and_noop_retained(self)
        natural=dict(inheritance_mode='parent_copy',mode='mutating',fuel_mode='renewed',route='ancestor',
            genesis_program=[transition.ANCESTOR_WORDS[i:i+3] for i in range(0,27,3)])
        # Disclosed full-audit/roster stubs test NULL control flow, not ancestry proof.
        with (patch.object(wrapper.natural_full,'audit',return_value={'verified':True}),
              patch.object(wrapper,'slots_from_audited',return_value={1:None,2:None})):
            result=wrapper.history(natural,1,'ancestor_value_control',PROVENANCE)
        self.assertIsNone(result['branch']);self.assertIsNone(result['transition'])
        self.assertEqual(result['generation'],1)

    def temporal_selfwrite_certificates(self):
        T.test_temporal_certificate_refusals(self)
        O.test_temporal_transmission_not_division_hash(self)
        state,slot=prepared()
        # Source values differ from the literal ancestor; the actual COPY-time
        # source, not division-time/source-genome substitution, binds each word.
        before,record=referee.transition(state,slot,'c'*64,'sham',PROVENANCE)
        self.assertEqual(record['certificates'],slot['certificates'])
        bad=transition.clone(slot);bad['certificates'][0]['source_value']=(bad['certificates'][0]['source_value']+1)%32
        with self.assertRaises(AssertionError):referee.transition(state,bad,'c'*64,'sham',PROVENANCE)

    def altered_boundary(self,key,value):
        state,slot=prepared();after,record=referee.transition(state,slot,'c'*64,'ancestor_value_control',PROVENANCE)
        bad=transition.clone(after)
        if key in ('last','tick','free'):bad[key]=value
        elif key=='unit':transition.actor_record(bad['entities'],1)['code'][0][1]=value
        else:transition.actor_record(bad['entities'],1)[key]=value
        forged=transition.clone(record);forged.update(after_hash=transition.h(bad),after_code=transition.clone(transition.actor_record(bad['entities'],1)['code']))
        expected,binding=referee.transition(state,slot,'c'*64,'ancestor_value_control',PROVENANCE)
        with self.assertRaises(AssertionError):assert bad==expected and forged==binding

    def clock_scheduler_tamper(self):
        self.altered_boundary('tick',41);self.altered_boundary('last',1)

    def material_unit_tamper(self):
        self.altered_boundary('unit',511);self.altered_boundary('free',[])

    def energy_tamper(self):self.altered_boundary('energy',13)

    def full_before_partial(self):
        T.test_full_audit_precedes_selection_and_world(self)
        O.test_full_replay_before_projection(self)

    def sham_equality(self):
        T.test_sham_exact_and_noop_retained(self)
        B.test_shared_helper_unavailable_and_valid_parity(self)

    def raw_restored_identity(self):
        state,slot=prepared();value=dict(state=state,slot=slot,provenance=PROVENANCE)
        original=grant.canonical(value).encode('ascii')
        restored=grant.canonical(json.loads(original)).encode('ascii')
        self.assertEqual(original,restored)
        self.assertEqual(grant.digest(value),grant.digest(json.loads(restored)))
        altered=json.loads(restored);altered['state']['heat']+=1
        self.assertNotEqual(grant.digest(value),grant.digest(altered))

    def censored_endpoints_representation_scope(self):
        T.test_endpoint_includes_death_and_censor(self)
        O.test_representation_exact_all_parents(self)
        O.test_zero_offspring_undefined(self)
        O.test_strategy_requires_shared_action_difference(self)
        O.test_actual_material_refusal_predicates(self)
        # Authored proof-roster reachability ONLY: no full history is asserted.
        populations=[];forks=[]
        for seed in admission.SEEDS:
            for mode,inheritance in [('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy')]:
                s=summary(seed);s.update(mode=mode,inheritance_mode=inheritance)
                populations.append(dict(verified=True,stage_credit=False,provenance=PROVENANCE,
                    summary=s,history_hash='c'*64,projection=dict(actors={'0':dict(id=0)},material_competition=[],endpoint_tick=4096)))
            for generation in (1,2):
                for role in ('sham','ancestor_value_control'):
                    forks.append(dict(verified=True,stage_credit=False,provenance=PROVENANCE,
                        seed=seed,generation=generation,role=role,natural_history_hash='c'*64,slot=None,null=True))
        result=observer.cohort(populations,forks,PROVENANCE)
        self.assertEqual(len(result['neutral_slots']),16)
        self.assertTrue(all(s['null'] and not s['candidate'] for s in result['neutral_slots']))
        self.assertFalse(result['whole_inheritance_benefit']);self.assertFalse(result['sustained_evolution'])
        for malformed in (populations[:-1],populations+[populations[0]]):
            with self.assertRaises(AssertionError):observer.cohort(malformed,forks,PROVENANCE)


CASES={
 'mode_domain':C.test_mode_domain,'word_domain':C.test_word_domain,
 'parent_effective_source':C.test_parent_effective_source,'reset_effective_source':C.test_reset_effective_source,
 'draw_and_value':C.test_draw_and_value,'cold_startup_units':C.test_cold_startup_units,
 'paid_endpoint_gate':FrozenPrepared.paid_endpoint_gate,
 'all_eight_references_exports':T.test_all_sixteen_gates_and_failure,
 'durable_zero_treatment_refusal':T.test_durable_receipt_strict_types,
 'chronological_neutral_slots':FrozenPrepared.chronological_neutral_slots,
 'null_noop_retention':FrozenPrepared.null_noop_retention,
 'temporal_selfwrite_certificates':FrozenPrepared.temporal_selfwrite_certificates,
 'complete_parent_expiration':T.test_complete_post_expiration_hash,
 'clock_scheduler_tamper':FrozenPrepared.clock_scheduler_tamper,
 'material_unit_tamper':FrozenPrepared.material_unit_tamper,'energy_tamper':FrozenPrepared.energy_tamper,
 'second_intervention':T.test_second_intervention_refused,
 'source_configuration_provenance':T.test_external_provenance_refused,
 'canonical_identity':B.test_independent_cold_start_and_identity_refusals,
 'full_before_partial':FrozenPrepared.full_before_partial,'sham_equality':FrozenPrepared.sham_equality,
 'raw_restored_identity':FrozenPrepared.raw_restored_identity,
 'bounded_write_grant_refusals':C.test_grant_prewrite_domain_refusals,
 'censored_endpoints_representation_scope':FrozenPrepared.censored_endpoints_representation_scope}
for name,method in CASES.items():setattr(FrozenPrepared,'test_'+name,method)


def load_tests(loader,tests,pattern):
    # Imported component TestCases are reused as methods, not counted again.
    suite=loader.loadTestsFromTestCase(FrozenPrepared)
    assert suite.countTestCases()==24
    return suite


if __name__=='__main__':unittest.main()
