"""Prepared local traces only; no scientific history or learned policy."""
from tests import test_digital_history36_diagnose as fixtures
from experiments.digital_history46_diagnose import diagnose
from experiments.digital_history46_independent import diagnose as referee

prepared=fixtures.prepared

class LatchAgeTests(fixtures.DiagnosisTests):
    def both(self,row):
        result=diagnose(row);self.assertEqual(result,referee(row))
        self.assertFalse(result['learning']);self.assertFalse(result['stage_credit'])
        return result['reads']

    def test_effect_action_does_not_replace_its_input_latch(self):
        r=self.both(prepared([[6,0,0],[1,0,0],[6,0,0]]))[0]
        self.assertEqual((r['latch_relation'],r['latest_act_before_effect'],r['intervening_act_count']),('latest',1,0))
        self.assertFalse(r['retained_beyond_latch'])

    def test_old_real_feedback_carried_after_another_action(self):
        code=[[6,0,0],[1,0,0],[3,0,0],[4,0,0],[6,0,0],[2,0,0],[6,0,0]]
        r=self.both(prepared(code))[0]
        self.assertEqual((r['origin_tick'],r['effect_tick'],r['latest_act_before_effect'],r['intervening_act_count']),(1,7,5,1))
        self.assertTrue(r['retained_own_before_completion'])
        self.assertEqual(r['latch_relation'],'replaced')
        reset=self.both(prepared(code,'retained_disabled'))[0]
        self.assertFalse(reset['retained_beyond_latch'])

    def test_empty_action_also_replaces_latch(self):
        code=[[6,0,0],[1,0,0],[3,0,0],[4,0,0],[6,0,0],[2,0,0],[6,0,0]]
        row=prepared(code);del row['final']['events'][4]['attempt']
        r=self.both(row)[0]
        self.assertEqual((r['latch_relation'],r['latest_act_before_effect'],r['intervening_act_count']),('replaced',5,1))

    def test_repeated_reads_are_not_new_origins(self):
        rs=self.both(prepared([[6,0,0],[1,0,0],[1,0,0],[6,0,0]]))
        self.assertEqual([r['origin_read_ordinal'] for r in rs],[1,2])
        self.assertEqual([r['repeat_of_own_origin'] for r in rs],[False,True])

    def test_unrelated_and_initial_are_never_own_retention(self):
        for mode in ('intact','own_disrupted'):
            rs=self.both(prepared([[1,0,0],[3,0,0],[4,0,0],[6,0,0],[2,0,0],[6,0,0]],mode))
            self.assertFalse(any(r['retained_beyond_latch'] for r in rs))
