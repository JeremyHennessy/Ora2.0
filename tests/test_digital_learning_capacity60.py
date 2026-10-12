"""Authored partial-table/software fixtures; World trapped; no registered seed run."""
import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_learning_capacity60 as factory
from experiments import digital_learning_capacity60_interpret as referee
from experiments import digital_informative_exposure23 as substrate
from experiments.digital_informative_exposure23_interpret import body,h

SOURCE=json.loads((Path(__file__).resolve().parents[1]/'docs/DIGITAL-LEARNING-CAPACITY-60-SOURCE.json').read_bytes())
PROGRAMS=SOURCE['programs'];SEMANTICS={}


def table(program,orientation=0,limit=512,late_orientation=None):
    """Mini authored feedback table, not complete VM history or seed-derived law."""
    words=sum(program,[]);s=body(0,None,0,[[v,i] for i,v in enumerate(words)],list(range(30,46)),0)
    remaining=set(range(32));events=[]
    for t in range(1,limit+1):
        op,a,b=program[s['pc']];e=dict(tick=t,actor=0,decoded=[op,a,b],before=h(s));s=copy.deepcopy(s);s['energy']-=1;s['pc']=(s['pc']+1)%10;r=s['registers']
        if op==1:r[a%2]=s['feedback']
        elif op==4:r[a%2]=b%16
        elif op==5:r[a%2]^=r[b%2]
        elif op==6:
            s['feedback']=0;local=sorted(p for p in remaining if p<16 or t>=64)
            if local:
                packet=local[0];target=orientation if t<64 or late_orientation is None else late_orientation
                s['feedback']=int(r[a%2]%2==target);e['attempt']=dict(packet=packet,position=0,port=r[a%2]%2,target=target,success=s['feedback'])
                if s['feedback']:remaining.remove(packet);s['energy']=min(64,s['energy']+20)
        elif op==7:s['pc']=b%10
        elif op==8 and r[a%2]==0:s['pc']=b%10
        if s['energy']==0:e['death']=list(range(46));events.append(e);break
        e['after']=copy.deepcopy(s);events.append(e)
    return events


def summaries():
    rows=[]
    for seed in factory.SEEDS:
        for arm in factory.ARMS:
            bill=100 if arm=='intact' else 130
            rows.append(dict(verified=True,authored_apparatus=True,stage_credit=False,seed=seed,arm=arm,ordinary_admitted=arm=='fixed-exploration',projection=dict(endpoint=dict(bill=bill),possible_history_bridges=[dict(scope='possible_only')],trials=[dict(phase='released',informative=True)])))
    return rows


class LearningCapacity60(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.trap=patch.object(substrate.World,'__init__',side_effect=AssertionError('World forbidden in prepared fixtures'));cls.trap.start()
    @classmethod
    def tearDownClass(cls):cls.trap.stop();print('\nSEMANTICS:'+json.dumps(SEMANTICS,sort_keys=True,separators=(',',':')),flush=True)
    def project(self,arm='intact',orientation=0,limit=512,late=None):
        p=referee.project(PROGRAMS[arm],table(PROGRAMS[arm],orientation,limit,late));SEMANTICS[self._testMethodName]=dict(full_semantic_hash=h(p),first_food=p['first_food_tick'],endpoint=p['endpoint'],trial_count=len(p['trials']),read_count=len(p['reads']),bridge_count=len(p['possible_history_bridges']),death=p['death_tick'],cap_loss=p['cap_loss']);return p
    def test_01_frozen_bank(self):self.assertEqual(set(factory.bank(SOURCE)),set(factory.ARMS));SEMANTICS[self._testMethodName]=factory.SOURCE_HASH
    def test_02_tampered_source_refused(self):
        source=copy.deepcopy(SOURCE);source['programs']['intact'][0][0]=18
        with self.assertRaises(AssertionError):factory.bank(source)
        SEMANTICS[self._testMethodName]='SOURCE_REFUSED'
    def test_03_reserves_refused_before_world(self):
        for seed in (60100,60300,True):
            with self.assertRaises(AssertionError):factory.generate(seed,'intact',SOURCE)
        SEMANTICS[self._testMethodName]='RESERVES_UNOPENED'
    def test_04_unknown_arm_refused(self):
        with self.assertRaises(AssertionError):factory.generate(60000,'selected-winner',SOURCE)
        SEMANTICS[self._testMethodName]='ARM_REFUSED'
    def test_05_alias_ambiguity_refused(self):
        with patch.dict(substrate.PROGRAMS,{'duplicate-a':PROGRAMS['intact'],'duplicate-b':PROGRAMS['intact']}):
            with self.assertRaises(AssertionError):factory.generate(60000,'intact',SOURCE)
        SEMANTICS[self._testMethodName]='AMBIGUITY_REFUSED'
    def test_06_alias_cleanup_on_fixture_refusal(self):
        before=h(substrate.PROGRAMS)
        with patch.object(substrate,'history',side_effect=RuntimeError('No World fixture')):
            with self.assertRaises(RuntimeError):factory.generate(60000,'intact',SOURCE)
        self.assertEqual(h(substrate.PROGRAMS),before);SEMANTICS[self._testMethodName]='ALIAS_RESTORED_NO_WORLD'
    def test_07_paid_worst_cold_route(self):
        p=self.project(orientation=1,limit=9);self.assertEqual(p['first_food_tick'],9);self.assertEqual(table(PROGRAMS['intact'],1,9)[-1]['after']['energy'],23)
    def test_08_paid_best_cold_route(self):
        p=self.project(limit=1);self.assertEqual(p['first_food_tick'],1);self.assertEqual(table(PROGRAMS['intact'],0,1)[0]['after']['energy'],31)
    def test_09_fixed_exploration_worst_route(self):
        p=self.project('fixed-exploration',1,6);self.assertEqual(p['first_food_tick'],6);self.assertEqual(table(PROGRAMS['fixed-exploration'],1,6)[-1]['after']['energy'],26)
    def test_10_wrong_constant_cold_death(self):
        p=self.project('fixed0',1);self.assertEqual(p['death_tick'],12);self.assertIsNone(p['endpoint']);self.assertFalse(p['survived64'])
    def test_11_empty_feedback_not_information(self):
        p=self.project(limit=63);self.assertTrue(any(r['origin'] is None for r in p['reads']));self.assertTrue(all(r['feedback']==0 for r in p['reads'] if r['origin'] is None))
    def test_12_repeated_failed_packet_not_new_information(self):
        p=self.project(orientation=1,limit=3);self.assertEqual([t['informative'] for t in p['trials']],[True,False,False])
    def test_13_release_timing_and_real_ports(self):
        p=self.project('fixed-exploration',0);self.assertTrue(p['survived64']);self.assertEqual(p['cold_ports'],[0,1]);self.assertTrue(all(x['tick']>=64 for x in p['released_acquisitions']));self.assertTrue(all(16<=v<32 for v in p['released_real_trial_packets']))
    def test_14_full_endpoint_bill_includes_cold_and_cap_losses(self):
        p=self.project();self.assertIsNotNone(p['endpoint']);self.assertEqual(p['endpoint']['bill'],46+p['endpoint']['tick']);self.assertGreater(p['endpoint']['cap_loss'],0)
    def test_15_incomplete_is_null_not_zero_bill(self):
        p=self.project(limit=1);self.assertIsNone(p['endpoint']);self.assertFalse(p['learning'])
    def test_16_paid_boundary_cuts_retention(self):
        values={a:table(PROGRAMS[a],1,15)[-1]['after']['registers'][0] for a in ('intact','cache-cleared','cache-disrupted')}
        self.assertEqual(values,{'intact':1,'cache-cleared':0,'cache-disrupted':0});SEMANTICS[self._testMethodName]=values
    def test_17_feedback_disabled_never_reads(self):
        p=self.project('feedback-disabled',1);self.assertEqual(p['reads'],[]);self.assertEqual(p['possible_history_bridges'],[])
    def test_18_fixed_impossible_bridge_witness(self):
        p=self.project('fixed-exploration',1,late=0);self.assertEqual(p['reads'],[]);self.assertEqual(p['possible_history_bridges'],[])
    def test_19_unused_channel_tamper_refused(self):
        events=table(PROGRAMS['intact'],0,1);events[0]['after']['memory'][0]=1
        with self.assertRaises(AssertionError):referee.project(PROGRAMS['intact'],events)
        SEMANTICS[self._testMethodName]='CHANNEL_REFUSED'
    def test_20_generic_integrity_precedes_projection(self):
        e=dict(version=factory.VERSION,source_hash=factory.SOURCE_HASH,authored_apparatus=True,arm='intact',history=dict(seed=60000,mode='faithful',genesis_program=PROGRAMS['intact']))
        with patch.object(referee,'audit',side_effect=AssertionError('integrity')),patch.object(referee,'project',side_effect=RuntimeError('too early')) as p:
            with self.assertRaises(AssertionError):referee.interpret(e,SOURCE)
            p.assert_not_called()
        SEMANTICS[self._testMethodName]='GENERIC_FIRST'
    def test_21_complete_panel_pending_causal_review(self):
        result=referee.compare(summaries());self.assertTrue(all(g['all_pairs_strict'] for g in result['groups'].values()));self.assertFalse(result['causal_learning_accepted']);SEMANTICS[self._testMethodName]=result
    def test_22_missing_or_duplicate_panel_refused(self):
        rows=summaries()
        for wrong in (rows[:-1],rows[:-1]+rows[:1]):
            with self.assertRaises(AssertionError):referee.compare(wrong)
        SEMANTICS[self._testMethodName]='FULL_DENOMINATOR_REFUSED'
    def test_23_unseen_negative_not_pooled_away(self):
        rows=summaries();next(r for r in rows if r['seed']==60200 and r['arm']=='intact')['projection']['endpoint']['bill']=999
        result=referee.compare(rows);self.assertTrue(result['groups']['primary']['all_pairs_strict']);self.assertFalse(result['groups']['unseen']['all_pairs_strict']);SEMANTICS[self._testMethodName]=result
    def test_24_null_controls_and_ordinary_failure(self):
        rows=summaries();next(r for r in rows if r['seed']==60000 and r['arm']=='cache-cleared')['projection']['endpoint']=None
        result=referee.compare(rows);self.assertFalse(result['groups']['primary']['all_pairs_strict']);SEMANTICS[self._testMethodName]=result
        next(r for r in rows if r['seed']==60200 and r['arm']=='fixed-exploration')['ordinary_admitted']=False
        with self.assertRaises(AssertionError):referee.compare(rows)


if __name__=='__main__':
    import sys
    if len(sys.argv)==2:
        method=sys.argv.pop();assert method in ('direct','independent')
        if method=='independent':
            from experiments.digital_diagnosis59_origins_independent import trace
            referee.trace=trace
    unittest.main()
