"""Prepared exact census and disclosed child-source reachability; zero Worlds."""
import copy
import unittest
from unittest.mock import patch
from experiments import digital_pressure71_census as census
from experiments import digital_pressure71_family as family
from experiments import digital_pressure71_transition as transition
from experiments import digital_pressure71_referee as literal
from tests.test_digital_pressure71_newborn_data import fixture,cold,PROVENANCE


def panel():
    # Includes unrelated g3/g4 births and deaths. No scientific candidate or policy.
    edges=[(0,1,1),(0,2,1),(1,3,2),(2,4,2),(4,5,3),(3,6,3),
           (5,7,4),(6,8,4),(6,9,4)]
    row,summary=fixture(edges,8)
    row['final']['births']=len(edges);row['final']['deaths']=0
    summary['births']=len(edges);summary['deaths']=0
    row['hash']=census.digest(row['final'])
    return row,summary


class CensusTests(unittest.TestCase):
    def test_full_denominators_and_exact_growth(self):
        row,summary=panel();result=census.census_from_replayed(row,summary,3)
        self.assertEqual(result['frame'],dict(root=3,early_total=2,early_lineage=1,late_total=3,late_lineage=2))
        self.assertEqual(result['growth'],[1,6]);self.assertEqual(result['lineage_birth_ids'],[6,8,9])
        self.assertFalse(result['scientific_admission']);self.assertFalse(result['stage_credit'])

    def test_deaths_do_not_remove_births_from_cohorts(self):
        row,summary=panel();tick=len(row['final']['events'])+1
        row['final']['events'].append(dict(tick=tick,actor=6,expiry=dict(actor=6)))
        row['final']['deaths']=summary['deaths']=1;summary['ticks']=tick
        row['hash']=census.digest(row['final'])
        result=census.census_from_replayed(row,summary,3)
        self.assertEqual(result['growth'],[1,6]);self.assertEqual(result['death_records'],[dict(actor=6,tick=tick,cause='execution_budget')])

    def test_zero_cohort_is_undefined_not_zero_fitness(self):
        row,summary=fixture([(0,1,1),(1,2,2)],1)
        row['final'].update(births=2,deaths=0);summary.update(births=2,deaths=0)
        row['hash']=census.digest(row['final'])
        result=census.census_from_replayed(row,summary,2)
        self.assertFalse(result['cohort_opportunity']);self.assertIsNone(result['growth'])

    def test_non_neutral_root_and_forged_summary_refused(self):
        for defect in ('root','summary'):
            row,summary=panel();root=3
            if defect=='root':root=4
            else:summary['birth_edges'][-1]['parent']=5
            with self.assertRaises(AssertionError):census.census_from_replayed(row,summary,root)

    def test_actual_audit_delegate_before_projection(self):
        row,summary=panel()
        envelope=dict(slot_kind='parent',role='sham',branch=row)
        fake=dict(null=False,summary=summary,slot=dict(target=3))
        with patch.object(literal,'audit',return_value=fake) as call:
            result=census.audit_census(envelope,PROVENANCE)
        call.assert_called_once_with(envelope,PROVENANCE)
        self.assertEqual(result['growth'],[1,6])

    def test_disclosed_changed_child_preserves_draws_units_and_all_other_state(self):
        for dose in (1,8):
            row,summary=fixture([(0,1,1),(1,2,2),(2,3,3)],dose)
            slot=family.family_from_audited(row,summary)['child']
            # Authored input-value perturbation for SOFTWARE reachability only.
            # No natural history, paid ancestry, discovered genotype or learner claim.
            w=slot['certificates'][0];w['source_value']=w['effective_source_value']=9
            draw=w['mutation_draw'];w['value']=(9+1+(draw//100)%31)%32 if draw%100<dose else 9
            w['mutated']=draw%100<dose;slot['born_code'][0][0]=w['value']
            state=cold(slot,dose);original=copy.deepcopy(state)
            expected=family.child_source_values(slot['certificates'],dose)
            after,record=transition.transition(state,slot,row['hash'],'inherited_source_control',PROVENANCE)
            independent=literal.transition(state,slot,row['hash'],'inherited_source_control',PROVENANCE)
            self.assertEqual((after,record),independent);self.assertIn(0,record['code_value_mask'])
            self.assertEqual(after['entities']['3']['code'],expected)
            baseline=copy.deepcopy(state);baseline['entities']['3']['code']=expected
            self.assertEqual(after,baseline);self.assertEqual(state,original)

    def test_child_own_mutation_retained_in_prepared_source_control(self):
        row,summary=fixture([(0,1,1),(1,2,2),(2,3,3)],8)
        words=family.family_from_audited(row,summary)['child']['certificates']
        for w in words:w.update(mutation_draw=99,value=w['source_value'],mutated=False)
        words[0].update(source_value=9,effective_source_value=9,mutation_draw=0,value=10,mutated=True)
        self.assertEqual(family.child_source_values(words,8)[0],[5,100])


if __name__=='__main__':unittest.main()
