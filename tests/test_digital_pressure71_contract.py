"""Synthetic software frames only; not organism candidates or paid evidence."""
import unittest
from experiments.digital_pressure71_contract import cohort, prepared_selection, schedule_counts


class Pressure71PreparedTests(unittest.TestCase):
    def setUp(self):
        self.parent = dict(births=2, food=3, censored=False, signatures=[['ACT', 0, 1]])
        self.parent_control = dict(births=1, food=3, censored=False, signatures=[['ACT', 0, 0]])
        self.child = dict(births=1, food=3, censored=False, signatures=[['MOVE', 2]])
        self.child_control = dict(births=0, food=0, censored=False, signatures=[['MOVE', 0]])
        self.edge = dict(present=True, root_generation=2, child_generation=3,
                         root=2, child=3, child_parent=2, root_tick=100, child_tick=200)
        self.sham = dict(root=2, early_total=4, early_lineage=1, late_total=4, late_lineage=3)
        self.control = dict(root=2, early_total=4, early_lineage=1, late_total=4, late_lineage=1)

    def result(self, **changes):
        values = dict(parent=self.parent, parent_control=self.parent_control,
                      child=self.child, child_control=self.child_control,
                      parent_changed=True, child_source_changed=True,
                      edge=self.edge, sham=self.sham, control=self.control)
        values.update(changes)
        return prepared_selection(**values)

    def test_prepared_reachability_denies_science(self):
        r = self.result()
        self.assertTrue(r['fixture_selection_candidate'])
        self.assertEqual(r['sham_growth'], [1, 2])
        self.assertFalse(r['scientific_acceptance'])
        self.assertFalse(r['stage_credit'])

    def test_schedule_pairs_not_endpoint_records(self):
        self.assertEqual(schedule_counts(), dict(endpoint_records=416, native_calls=418,
                         original_restored_comparison_pairs=208, precharged_record_mib=14976))

    def test_fraction_exact(self):
        ok, value, births = cohort(dict(root=2, early_total=3, early_lineage=1,
                                       late_total=7, late_lineage=3))
        self.assertTrue(ok)
        self.assertEqual([value.numerator, value.denominator], [2, 21])
        self.assertEqual(births, 4)

    def test_zero_denominator_not_assigned_fitness(self):
        r = self.result(control=dict(self.control, late_total=0, late_lineage=0))
        self.assertIsNone(r['control_growth'])
        self.assertFalse(r['fixture_selection_candidate'])

    def test_insufficient_cohort_stays_unqualified(self):
        self.assertFalse(self.result(sham=dict(self.sham, early_total=1))['fixture_selection_candidate'])

    def test_absolute_birth_gain_without_share_growth_fails(self):
        s = dict(self.sham, early_lineage=2, late_total=8, late_lineage=4)
        self.assertFalse(self.result(sham=s)['fixture_selection_candidate'])

    def test_growth_not_greater_than_source_control_fails(self):
        c = dict(self.control, early_lineage=0, late_lineage=3)
        self.assertFalse(self.result(control=c)['fixture_selection_candidate'])

    def test_growth_without_more_descendant_births_fails(self):
        c = dict(self.control, early_total=8, early_lineage=4, late_total=8, late_lineage=4)
        self.assertFalse(self.result(control=c)['fixture_selection_candidate'])

    def test_parent_gain_without_child_contribution_fails(self):
        self.assertFalse(self.result(child_source_changed=False)['fixture_selection_candidate'])

    def test_missing_actual_child_retained(self):
        r = self.result(edge=dict(present=False))
        self.assertTrue(r['missing'])
        self.assertFalse(r['fixture_selection_candidate'])

    def test_censor_and_nonshared_actions_fail(self):
        self.assertFalse(self.result(child=dict(self.child, censored=True))['fixture_selection_candidate'])
        self.assertFalse(self.result(child_control=dict(self.child_control, signatures=[]))['fixture_selection_candidate'])

    def test_wrong_root_or_birth_order_refused(self):
        for edge in (dict(self.edge, child_parent=4), dict(self.edge, child_tick=100),
                     dict(self.edge, root_generation=1), dict(self.edge, root_generation=True)):
            with self.assertRaises(AssertionError):
                self.result(edge=edge)

    def test_noninteger_or_impossible_census_refused(self):
        for bad in (dict(self.sham, early_total=True), dict(self.sham, late_total=4.0),
                    dict(self.sham, late_lineage=5), dict(self.sham, early_lineage=-1)):
            with self.assertRaises(AssertionError):
                self.result(sham=bad)


if __name__ == '__main__':
    unittest.main()
