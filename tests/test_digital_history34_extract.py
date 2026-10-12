"""Prepared event records, never claimed as complete VM-valid World histories."""
import copy
import unittest
from experiments import digital_history34_extract as main
from experiments import digital_history34_independent as independent
from experiments.digital_history33_endpoint import compare, MODES, REFERENCES
from tests.test_digital_history33_endpoint import fixture, metric


def prepared(mode='intact'):
    es=[dict(tick=i,actor=0,decoded=[18,0,0]) for i in range(1,64)]
    es[9].update(decoded=[1,0,0],control=dict(personal_read=dict(own_source_tick=None,original=0,value=0)))
    es[10]['decoded']=[6,0,0]
    es[11].update(decoded=[1,0,0],control=dict(personal_read=dict(own_source_tick=None,original=0,value=0)))
    def act(packet,success):
        t=len(es)+1;es.append(dict(tick=t,actor=0,decoded=[6,0,0],attempt=dict(packet=packet,port=0,success=success)));return t
    def read(origin,value):
        es.append(dict(tick=len(es)+1,actor=0,decoded=[1,0,0],control=dict(personal_read=dict(own_source_tick=origin,original=value,value=1-value if mode=='own_disrupted' else value))))
    origin=act(0,0);read(origin,0)
    for p in range(32):
        origin=act(p,1);read(origin,1);read(origin,1)
    es.append(dict(tick=len(es)+1,actor=0,decoded=[6,0,0]));read(None,0)
    return dict(control_mode=mode,genesis_program=[[18,0,0]],final=dict(events=es))


class ExtractionTests(unittest.TestCase):
    def both(self,row):
        a=main.extract(row);self.assertEqual(a,independent.extract(row));return a

    def refuses(self,row):
        for implementation in (main,independent):
            with self.assertRaises(ValueError):implementation.extract(row)

    def test_completion_cutoff_excludes_last_food_reads(self):
        a=self.both(prepared());self.assertEqual(a['metric']['own_origins'],32)
        self.assertEqual(a['diagnostic']['ignored_post_completion_reads'],3)
        self.assertTrue(a['metric']['both_own_outcomes'])

    def test_duplicates_initial_and_empty_not_extra_opportunities(self):
        a=self.both(prepared());self.assertEqual(a['metric']['food'],32)
        self.assertEqual(a['metric']['own_origins'],32)
        self.assertEqual(a['metric']['paid_work'],19+a['metric']['completion_tick'])

    def test_disrupted_native_is_not_delivered(self):
        a=self.both(prepared('own_disrupted'))
        self.assertEqual(a['diagnostic']['native_distinct_origins_before_cutoff'],32)
        self.assertEqual(a['metric']['own_origins'],0);self.assertFalse(a['metric']['both_own_outcomes'])

    def test_incomplete_diagnostic_is_not_completion(self):
        r=prepared();r['final']['events']=r['final']['events'][:80]
        a=self.both(r);self.assertIsNone(a['metric']['paid_work']);self.assertIsNone(a['metric']['completion_tick'])

    def test_death_before_change_and_post_death_refused(self):
        r=prepared();r['final']['events']=r['final']['events'][:12];r['final']['events'][-1]['death']='prepared'
        self.assertFalse(self.both(r)['metric']['survived64'])
        r['final']['events'].append(dict(tick=13,actor=0,decoded=[18,0,0]));self.refuses(r)

    def test_duplicate_packet_win_refused(self):
        r=prepared();wins=[e for e in r['final']['events'] if e.get('attempt',{}).get('success')==1]
        wins[-1]['attempt']['packet']=wins[0]['attempt']['packet'];self.refuses(r)

    def test_post_completion_origin_is_still_verified(self):
        r=prepared();r['final']['events'][-1]['control']['personal_read']['own_source_tick']=64;self.refuses(r)

    def test_boolean_origin_and_wrong_actor_refused(self):
        r=prepared();r['final']['events'][64]['control']['personal_read']['own_source_tick']=True;self.refuses(r)
        r=prepared();r['final']['events'][64]['actor']=1;self.refuses(r)

    def test_used_channel_and_chronology_refused(self):
        r=prepared();r['genesis_program'][0][0]=9;self.refuses(r)
        r=prepared();r['final']['events'][63]['tick']=True;self.refuses(r)

    def test_independent_positive_and_each_comparator_veto(self):
        a,r=fixture();self.assertEqual(compare(a,r),independent.compare(a,r))
        for role in REFERENCES:
            a,r=fixture();r[role]=metric(99);self.assertEqual(compare(a,r),independent.compare(a,r));self.assertFalse(independent.compare(a,r)['qualified'])
        for mode in MODES[1:]:
            a,r=fixture();a[mode]=metric(100);self.assertEqual(compare(a,r),independent.compare(a,r))

    def test_independent_bill_failure_and_incomplete_veto(self):
        a,r=fixture();r['affine4']=metric(101,formation=19);self.assertEqual(compare(a,r),independent.compare(a,r))
        a,r=fixture();a['intact'].update(completed=False,food=2,fresh=0,completion_tick=None,paid_work=None,terminal_tick=90)
        self.assertEqual(compare(a,r),independent.compare(a,r))

    def test_independent_malformed_inputs_refused(self):
        for mutate in ('bool','missing','formation','unrelated'):
            a,r=fixture()
            if mutate=='bool':a['intact']['paid_work']=True
            elif mutate=='missing':del r['fixed0']
            elif mutate=='formation':a['retained_disabled']['formation']=52;a['retained_disabled']['paid_work']=252
            else:a['own_disrupted']['delivered_own']=True
            for scorer in (compare,independent.compare):
                with self.assertRaises(ValueError):scorer(a,r)


if __name__=='__main__':unittest.main()
