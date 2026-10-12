import copy, unittest
from experiments.digital_source32_admission import manifest, opportunities
from experiments.digital_admission_roles24 import prepared_records

def prepared(mode='intact'):
    record=prepared_records()[0]['record']; events=[]
    acts={a['tick']:a for a in record['actions']}; reads={r['tick']:r for r in record['reads']}
    for t in range(1,100):
        e=dict(tick=t,actor=0,decoded=[18,0,0])
        if t in acts:e.update(decoded=[6,0,0],attempt=acts[t]['attempt'])
        if t in reads:
            r=reads[t]; e.update(decoded=[1,0,0],control=dict(personal_read=dict(own_source_tick=r['source_tick'],original=r['value'],value=1-r['value'] if mode=='own_disrupted' else r['value'])))
        events.append(e)
    return dict(control_mode=mode,final=dict(events=events))

class SourceAdmissionTests(unittest.TestCase):
    def test_complete_unselected_denominator_and_ancestry(self):
        m=manifest(); self.assertEqual(m['total_histories'],402); self.assertEqual(m['candidate_histories'],336)
        self.assertEqual([c['candidate_id'] for c in m['candidates']],list(range(56)))
        self.assertEqual(len({c['program_sha256'] for c in m['candidates']}),56)
        self.assertTrue(all(len(c['external_mutations'])==2 and not c['birth'] for c in m['candidates']))
        self.assertEqual(len(m['references']),11); self.assertFalse(m['performance_selection']); self.assertEqual(m['world_histories_executed'],0)
    def test_reactive_personal_reachability_is_not_cold_criterion(self):
        x=opportunities(prepared()); self.assertTrue(x['native_reactive_reachability']); self.assertTrue(x['delivered_own_reactive_reachability'])
        self.assertFalse(x['ordinary_exploration']); self.assertEqual(x['distinct_post_own_attempts'],17); self.assertFalse(x['learning'])
    def test_unrelated_samples_never_count_as_delivered_own_history(self):
        x=opportunities(prepared('own_disrupted')); self.assertTrue(x['native_reactive_reachability']); self.assertFalse(x['delivered_own_reactive_reachability'])
    def test_repeated_latch_is_one_opportunity(self):
        row=prepared(); e=row['final']['events'][98]; e.update(decoded=[1,0,0],control=copy.deepcopy(row['final']['events'][97]['control']))
        self.assertEqual(opportunities(row)['distinct_post_own_attempts'],17)
    def test_wrong_own_origin_refused(self):
        row=prepared(); row['final']['events'][65]['control']['personal_read']['own_source_tick']=67
        with self.assertRaises(AssertionError):opportunities(row)
    def test_boolean_outcome_refused(self):
        row=prepared(); row['final']['events'][65]['control']['personal_read']['original']=False
        with self.assertRaises(AssertionError):opportunities(row)
    def test_death_before_boundary_is_not_cold_survival(self):
        row=prepared(); row['final']['events']=row['final']['events'][:12]; row['final']['events'][-1]['death']=[]
        x=opportunities(row); self.assertFalse(x['cold_survival']); self.assertFalse(x['native_reactive_reachability'])
    def test_empty_attempt_resets_origin(self):
        row=prepared(); row['final']['events'][64].pop('attempt'); row['final']['events'][65]['control']['personal_read'].update(own_source_tick=None,original=0,value=0)
        x=opportunities(row); self.assertEqual(x['empty_or_initial_reads'],1); self.assertFalse(x['native_reactive_reachability'])
