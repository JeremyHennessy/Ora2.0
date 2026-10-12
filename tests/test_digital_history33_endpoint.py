"""Prepared summaries only: these are not organism histories or viable genomes."""
import copy
import unittest
from experiments.digital_history33_endpoint import compare, contract, MODES, REFERENCES


def metric(t=200, personal=False, formation=55):
    return dict(formation=formation, food=32, fresh=16, own_origins=16 if personal else 0,
                terminal_tick=t, completed=True, survived64=True, delivered_own=personal,
                both_own_outcomes=personal, completion_tick=t, paid_work=formation+t)


def fixture():
    arms={m:metric(100 if m=='intact' else 200, m=='intact') for m in MODES}
    refs={r:metric() for r in REFERENCES}
    return arms, refs


class EndpointTests(unittest.TestCase):
    def test_prepared_positive_is_not_learning(self):
        a,r=fixture(); result=compare(a,r)
        self.assertTrue(result['qualified']); self.assertFalse(result['learning'])
        self.assertFalse(result['stage_credit'])

    def test_death_and_null_completion_never_win(self):
        for mode in MODES:
            a,r=fixture(); a[mode].update(completed=False, food=2, fresh=0,
                completion_tick=None, paid_work=None, terminal_tick=90)
            self.assertIn('incomplete_candidate_or_control_exposure',compare(a,r)['reasons'])

    def test_personal_reads_not_duplicates_or_native_disruption(self):
        a,r=fixture(); a['intact']['own_origins']=15
        self.assertFalse(compare(a,r)['qualified'])
        a,r=fixture(); a['own_disrupted']['delivered_own']=True
        with self.assertRaises(ValueError): compare(a,r)

    def test_every_reference_and_both_controls_count(self):
        for role in REFERENCES:
            a,r=fixture(); r[role]=metric(99)
            self.assertFalse(compare(a,r)['qualified'])
        for mode in MODES[1:]:
            a,r=fixture(); a[mode]=metric(100)
            self.assertFalse(compare(a,r)['qualified'])

    def test_bill_not_latency_alone(self):
        a,r=fixture(); r['affine4']=metric(101,formation=19)
        self.assertFalse(compare(a,r)['qualified'])

    def test_incomplete_fixed_port_reported_not_infinite_gain(self):
        a,r=fixture(); r['fixed0'].update(completed=False,food=0,fresh=0,
            completion_tick=None,paid_work=None,terminal_tick=12,survived64=False)
        result=compare(a,r)
        self.assertTrue(result['qualified']); self.assertEqual(result['incomplete_references'],['fixed0'])
        r['alternating']=copy.deepcopy(r['fixed0'])
        self.assertFalse(compare(a,r)['qualified'])

    def test_malformed_bool_bill_or_missing_cell_refused(self):
        a,r=fixture(); a['intact']['completion_tick']=True
        with self.assertRaises(ValueError): compare(a,r)
        a,r=fixture(); del r['fixed0']
        with self.assertRaises(ValueError): compare(a,r)
        a,r=fixture(); a['intact']['paid_work']=154
        with self.assertRaises(ValueError): compare(a,r)

    def test_complete_neutral_denominator_no_world(self):
        c=contract(); self.assertEqual(c['candidates'],list(range(56)))
        self.assertEqual(c['future_histories'],1608)
        self.assertEqual(set(c['future_fresh_seeds']) & set(c['reserved_unopened_seeds']),set())
        self.assertEqual(c['world_histories_executed'],0)
        self.assertFalse(c['performance_selection'])


if __name__ == '__main__': unittest.main()
