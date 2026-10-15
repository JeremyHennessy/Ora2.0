"""Invented receipt arithmetic only. No World, label map or scientific outcome."""
import copy
from fractions import Fraction
import unittest

from experiments.digital_inheritance83_acceptance import (
    PRIMARY, UNSEEN, ARMS, interpret, paired_sign, common_opportunities,
)


def invented_metric(seed, mode, useful=False):
    episodes = []
    if useful:
        for session, q in enumerate((2, 4, 8), 1):
            episodes.append(dict(actor=0, session=session, proposed=q,
                                 header_write_id=session, paid_child=2 if q == 8 else None,
                                 child_fitness=int(q == 8), score=3 if q == 8 else 0))
    return dict(seed=seed, mode=mode, finite_horizon=16384, R=2 if useful else 0,
                functional_children=[1, 2] if useful else [],
                changed_functional_children=[1, 2] if useful else [], episodes=episodes,
                gate0_episodes=len(episodes), S_denominator=max(1, len(episodes)),
                S_numerator=3 if useful else 0,
                proposal_counts={str(q): int(useful) for q in (2, 4, 8)},
                accepted_uniform_proposals=3 if useful else 0,
                captured=0, paid_actor_cost=0, living_energy=112, births=2 if useful else 0,
                deaths=0, paid_dispatches=0, retained_operating_surplus=0,
                physics_validator=False, new_worlds=0, selection_accepted=False,
                actual_offered_packets=[[1, 0, 'admitted']],
                actual_served_opportunities=[[1, 0, []]])


def invented_receipts(positive=True):
    return [dict(seed=s, metrics=[invented_metric(s, a, positive and a == 'variation')
                                 for a in ARMS]) for s in PRIMARY + UNSEEN]


class AcceptanceArithmetic(unittest.TestCase):
    def test_complete_positive_numeric_fixture_is_never_execution_admission(self):
        r = interpret(invented_receipts())
        self.assertTrue(r['registered_numeric_criteria_met'])
        self.assertTrue(r['scientific_acceptance_requires_external_custody'])
        self.assertFalse(r['execution_admission'])
        self.assertFalse(r['new_own_history_learning_attribution'])
        self.assertEqual(r['complete_original_cells'], 80)
        for b in r['banks'].values():
            self.assertEqual(b['contrasts']['S_inheritance_disabled'], dict(numerator=8, denominator=1))
        self.assertEqual(r['paired_sign_tests']['R_no_variation']['p'], dict(numerator=1, denominator=65536))

    def test_complete_null_retains_all_ties_and_fails(self):
        r = interpret(invented_receipts(False))
        self.assertFalse(r['registered_numeric_criteria_met'])
        for sign in r['paired_sign_tests'].values():
            self.assertEqual((sign['ties'], sign['nonzero'], sign['p']),
                             (16, 0, dict(numerator=1, denominator=1)))

    def test_exact_sign_threshold_and_losses(self):
        self.assertTrue(paired_sign([1]*6 + [0]*10)['passes'])  # 1/64 <= 1/60
        self.assertFalse(paired_sign([1]*5 + [0]*11)['passes'])  # 1/32 > 1/60
        self.assertEqual(paired_sign([1]*7 + [-1] + [0]*8)['p'], dict(numerator=9, denominator=256))
        self.assertFalse(paired_sign([-1]*16)['passes'])

    def test_missing_duplicate_reserve_and_software_denominators_refused(self):
        fixtures = []
        rows = invented_receipts(); fixtures.append(rows[:-1])
        rows = invented_receipts(); rows[-1] = copy.deepcopy(rows[0]); fixtures.append(rows)
        for invalid in (1009000, 2140080):
            rows = invented_receipts(); rows[0]['seed'] = invalid; fixtures.append(rows)
        rows = invented_receipts(); rows[0]['metrics'].pop(); fixtures.append(rows)
        rows = invented_receipts(); rows[0]['metrics'][1] = copy.deepcopy(rows[0]['metrics'][0]); fixtures.append(rows)
        for rows in fixtures:
            with self.subTest(rows=len(rows)), self.assertRaises(AssertionError): interpret(rows)

    def test_episode_score_binding_and_cost_forgery_refusals(self):
        changes = (
            lambda m: m.update(S_numerator=999),
            lambda m: m.update(S_denominator=1),
            lambda m: m.update(gate0_episodes=2),
            lambda m: m.update(accepted_uniform_proposals=2),
            lambda m: m['proposal_counts'].update({'4': 0}),
            lambda m: m['episodes'][2].update(paid_child=None),
            lambda m: m['episodes'][2].update(header_write_id=None),
            lambda m: m['episodes'][1].update(session=1),
            lambda m: m['episodes'][1].update(header_write_id=1),
            lambda m: m.update(living_energy=113),
            lambda m: m.update(retained_operating_surplus=1),
            lambda m: m.update(changed_functional_children=[999]),
            lambda m: m.update(R=True),
        )
        for i, change in enumerate(changes):
            rows = invented_receipts(); change(rows[0]['metrics'][0])
            with self.subTest(forgery=i), self.assertRaises(AssertionError): interpret(rows)

    def test_unseen_failure_cannot_be_pooled_away(self):
        rows = invented_receipts()
        for receipt in rows[8:]:
            receipt['metrics'] = [invented_metric(receipt['seed'], a) for a in ARMS]
        r = interpret(rows)
        self.assertFalse(r['registered_numeric_criteria_met'])
        self.assertTrue(all(r['banks']['primary']['criteria'].values()))
        self.assertFalse(r['banks']['unseen']['criteria']['positive_fitness_and_proposal_contrasts'])

    def test_actual_opportunities_preserve_rejection_lineage_and_multiplicity(self):
        a = invented_metric(PRIMARY[0], 'variation')
        b = copy.deepcopy(a)
        a['actual_offered_packets'] += [[2, 1, 'external_rejected'], [2, 1, 'external_rejected']]
        b['actual_offered_packets'] += [[2, 1, 'admitted']]
        b['actual_served_opportunities'] = [[1, 0, [1]]]
        r = common_opportunities([a, b])
        self.assertEqual(r['common_offered_packet_cue'], 2)
        self.assertEqual(r['common_admitted_packet_cue'], 1)
        self.assertEqual(r['common_served_packet_cue_lineage'], 0)
        self.assertEqual(r['offered_by_arm'], [3, 2])


if __name__ == '__main__':
    unittest.main()
