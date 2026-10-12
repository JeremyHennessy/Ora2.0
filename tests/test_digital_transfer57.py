import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_transfer57 as t


class Transfer57PreparedTests(unittest.TestCase):
    """Closed manifest, synthetic paid joins and mocked producer; no World runs."""
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((Path(__file__).parents[1]/'docs/DIGITAL-TRANSFER-57-SOURCE.json').read_bytes())['summary']
        from experiments import digital_informative_exposure23 as substrate
        trap=patch.object(substrate,'World',side_effect=AssertionError('World forbidden in prepared software verification'))
        trap.start();cls.addClassCleanup(trap.stop)

    def ordinary(self,seed=57000):
        return dict(verified=True,seed=seed,arm='withheld',source=None,source_manifest_hash=t.SOURCE_HASH,mode='faithful',formation_cost=43,
                    remote_food=1,births=2,paid_copy_words=54,descendant_food=1,resource_then_birth=1,first_birth_tick=70,successful_food=10,site1_food=0)

    def panel(self):
        rows=[dict(summary=self.ordinary(seed)) for seed in t.SEEDS]
        for source in t.ROSTER:
            _,origin=t.choice('retained',source,self.manifest)
            for seed in t.SEEDS:rows.append(dict(summary=dict(self.ordinary(seed),arm='retained',source=origin,successful_food=11,site1_food=1)))
        return rows

    def test_frozen_manifest_and_all_eight_sources(self):
        self.assertEqual(len(t.source_bank(self.manifest)),8)
        for source in t.ROSTER:self.assertEqual(len(t.choice('retained',source,self.manifest)[0]),9)

    def test_manifest_tamper_refused(self):
        changed=copy.deepcopy(self.manifest);changed['roster'][0]['program'][0][0]^=1
        with self.assertRaises(AssertionError):t.source_bank(changed)

    def test_non_enrolled_source_and_boolean_identity_refused(self):
        for source in ((55000,1),(True,1)):
            with self.assertRaises(AssertionError):t.choice('retained',source,self.manifest)

    def test_withheld_is_shared_baseline(self):
        self.assertEqual(t.choice('withheld',None,self.manifest),(t.PROGRAM,None))
        with self.assertRaises(AssertionError):t.choice('withheld',t.ROSTER[0],self.manifest)

    def test_reserve_seed_refused_before_producer(self):
        with self.assertRaises(AssertionError):t.generate(57100,'withheld',None,self.manifest)

    def test_registry_cleanup_after_mock_failure(self):
        from experiments import digital_informative_exposure23 as substrate
        before=copy.deepcopy(substrate.PROGRAMS)
        with patch.object(substrate,'history',side_effect=RuntimeError('mock only')):
            with self.assertRaises(RuntimeError):t.generate(57000,'withheld',None,self.manifest)
        self.assertEqual(before,substrate.PROGRAMS)

    def test_existing_identical_program_uses_unique_route(self):
        from experiments import digital_informative_exposure23 as substrate
        before=copy.deepcopy(substrate.PROGRAMS);substrate.PROGRAMS['prepared_alias']=copy.deepcopy(t.PROGRAM)
        try:
            with patch.object(substrate,'history',return_value={'mock':'no World'}) as mock:
                result=t.generate(57001,'withheld',None,self.manifest)
                mock.assert_called_once_with(57001,'prepared_alias','faithful')
                self.assertEqual(result['history'],{'mock':'no World'})
            self.assertNotIn(t.ROUTE,substrate.PROGRAMS)
        finally:substrate.PROGRAMS.clear();substrate.PROGRAMS.update(before)

    def test_ambiguous_registry_refused(self):
        from experiments import digital_informative_exposure23 as substrate
        before=copy.deepcopy(substrate.PROGRAMS)
        try:
            for name in ('prepared_a','prepared_b'):substrate.PROGRAMS[name]=copy.deepcopy(t.PROGRAM)
            with self.assertRaises(AssertionError):t.generate(57000,'withheld',None,self.manifest)
        finally:substrate.PROGRAMS.clear();substrate.PROGRAMS.update(before)

    def test_ordinary_whole_lifecycle_gate(self):
        self.assertTrue(t.ordinary_gate(self.ordinary()))
        for key in ('remote_food','descendant_food','resource_then_birth','births','paid_copy_words','first_birth_tick'):
            failed=self.ordinary();failed[key]=0;self.assertFalse(t.ordinary_gate(failed))
        failed=self.ordinary();failed['births']=True;self.assertFalse(t.ordinary_gate(failed))

    def test_complete_four_pair_gate(self):
        panel=t.compare(self.panel());self.assertTrue(all(e['provisional_assisted_resource_benefit'] for e in panel['entries']))
        self.assertEqual((panel['unique_histories'],panel['shared_references'],panel['independent_context_pairs']),(72,8,4))
        self.assertFalse(panel['stage_credit']);self.assertFalse(panel['evolution'])

    def test_one_failed_pair_excludes_source(self):
        rows=self.panel();rows[8]['summary'].update(successful_food=8,site1_food=0)
        result=t.compare(rows);self.assertFalse(result['entries'][0]['provisional_assisted_resource_benefit'])

    def test_total_food_without_site1_benefit_excluded(self):
        rows=self.panel()
        for row in rows[8:]:row['summary']['site1_food']=0
        self.assertFalse(any(e['provisional_assisted_resource_benefit'] for e in t.compare(rows)['entries']))

    def test_missing_or_duplicate_history_refused(self):
        with self.assertRaises(AssertionError):t.compare(self.panel()[:-1])
        rows=self.panel();rows[-1]=copy.deepcopy(rows[-2])
        with self.assertRaises(AssertionError):t.compare(rows)

    def test_failed_ordinary_reference_refuses_panel(self):
        rows=self.panel();rows[0]['summary']['descendant_food']=0
        with self.assertRaises(AssertionError):t.compare(rows)

    def test_reserved_or_boolean_count_refused(self):
        for changes in ({'seed':57100},{'successful_food':True}):
            rows=self.panel();rows[8]['summary'].update(changes)
            with self.assertRaises(AssertionError):t.compare(rows)

    def state(self):
        return t.body(0,None,0,[[v,i] for i,v in enumerate(sum(t.PROGRAM,[]))],list(range(27,43)),0)

    def test_terminal_halt_and_dead_denominator(self):
        state=self.state();event=dict(tick=1,actor=0,decoded=[17,0,0],before=t.h(state),death=[])
        p=t.census(t.PROGRAM,[event])['actors'][0]
        self.assertEqual((p['alive'],p['halt_heat'],p['instructions'],p['endpoint_body_hash']),(False,11,1,None))
        with self.assertRaises(AssertionError):t.census(t.PROGRAM,[event,dict(event,tick=2)])

    def test_cap_loss_and_empty_act(self):
        state=self.state();after=copy.deepcopy(state);after['energy']=31
        first=dict(tick=1,actor=0,decoded=[6,0,0],before=t.h(state),after=after,attempt=dict(packet=0,position=0,success=1))
        events=[first]
        for tick in range(2,5):
            before=copy.deepcopy(after);after=copy.deepcopy(before);after['energy']=min(64,before['energy']-1+20)
            events.append(dict(tick=tick,actor=0,decoded=[6,0,0],before=t.h(before),after=after,attempt=dict(packet=tick-1,position=0,success=1)))
        before=copy.deepcopy(after);after=copy.deepcopy(before);after['energy']-=1
        events.append(dict(tick=5,actor=0,decoded=[6,0,0],before=t.h(before),after=after))
        p=t.census(t.PROGRAM,events)['actors'][0]
        self.assertEqual((p['cap_loss'],p['actions'],p['attempts_by_site'][0]),(24,5,4))

    def test_noop_selfwrite_excludes_stable_site1(self):
        state=self.state();after=copy.deepcopy(state);after.update(energy=11,pos=1)
        move=dict(tick=1,actor=0,decoded=[13,0,0],before=t.h(state),after=after)
        before=copy.deepcopy(after);after=copy.deepcopy(before);after['energy']=10
        write=dict(tick=2,actor=0,decoded=[9,0,0],before=t.h(before),after=after,self_write=dict(old=4,value=4))
        before=copy.deepcopy(after);after=copy.deepcopy(before);after['energy']=29
        act=dict(tick=3,actor=0,decoded=[6,0,0],before=t.h(before),after=after,attempt=dict(packet=32,position=1,success=1))
        result=t.census(t.PROGRAM,[move,write,act])
        self.assertEqual((result['stable_site1_food'],result['site1_after_selfwrite_food']),(0,1))

    def paid_birth(self):
        state=self.state();events=[];ids=[];nursery=[];packet=0
        for tick in range(1,15):
            before=copy.deepcopy(state);state=copy.deepcopy(before);state['energy']-=1
            event=dict(tick=tick,actor=0,before=t.h(before))
            if tick in (1,5,9):
                state['energy']+=20;event.update(decoded=[6,0,0],attempt=dict(packet=packet,position=0,success=1));packet+=1
            elif tick in (13,14):event['decoded']=[18,0,0]
            else:
                event['decoded']=[10,0,0];state['energy']-=3;writes=[]
                for index in range(len(nursery),len(nursery)+3):
                    value,unit=state['code'][index];writes.append(dict(write_id=index,index=index,tick=tick,unit=43+index,value=value,source_unit=unit,source_value=value,mutated=False))
                nursery.extend(writes);state['nursery']=copy.deepcopy(nursery);ids.extend(w['write_id'] for w in writes);event['writes']=writes
            event['after']=copy.deepcopy(state);events.append(event)
        child=t.body(1,0,1,[[w['value'],w['unit']] for w in nursery],list(range(70,86)),0)
        events.append(dict(tick=15,actor=0,decoded=[12,0,0],before=t.h(state),death=[],birth=dict(child=child,startup_energy=12,write_ids=ids)))
        return events

    def test_paid_child_zero_actions_and_parent_terminal(self):
        c=t.census(t.PROGRAM,self.paid_birth());self.assertEqual((c['actors'][0]['alive'],c['actors'][1]['alive'],c['actors'][1]['instructions'],c['paid_words']),(False,True,0,27))
        self.assertEqual(c['actors'][1]['food_by_site'],[0]*4)

    def test_unpaid_or_duplicate_birth_certificate_refused(self):
        for value in (999,1):
            events=self.paid_birth();events[-1]['birth']['write_ids'][0]=value
            with self.assertRaises(AssertionError):t.census(t.PROGRAM,events)

    def test_child_startup_or_generation_refused(self):
        for key in ('energy','generation'):
            events=self.paid_birth();events[-1]['birth']['child'][key]=0
            with self.assertRaises(AssertionError):t.census(t.PROGRAM,events)

    def test_wrong_genesis_and_source_rejected_before_audit(self):
        env=dict(version=t.VERSION,arm='withheld',source=None,source_manifest_hash=t.SOURCE_HASH,history=dict(seed=57000,mode='faithful',genesis_program=[[0,0,0]]))
        with self.assertRaises(AssertionError):t.interpret(env,self.manifest)

    def test_arithmetic_mismatch_rejected(self):
        state=self.state();after=copy.deepcopy(state);after['energy']=12
        with self.assertRaises(AssertionError):t.census(t.PROGRAM,[dict(tick=1,actor=0,decoded=[18,0,0],before=t.h(state),after=after)])
