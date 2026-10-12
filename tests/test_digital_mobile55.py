import copy,unittest
from unittest.mock import patch
from experiments.digital_mobile55 import PROGRAM,census,ordinary_gate,replicated_contexts,words,interpret


class Mobile55PreparedFixtures(unittest.TestCase):
    """Synthetic paid joins, not valid World histories or discovered genomes."""
    def code(self,novel=True,start=100):
        values=sum(PROGRAM,[])
        if novel:values[20]=1
        return [[value,start+i] for i,value in enumerate(values)]
    def paid(self,tick,actor,parent_code,child_code,start):
        writes=[dict(write_id=start+i,tick=tick,index=i,unit=cell[1],value=cell[0],source_unit=parent_code[i][1],source_value=parent_code[i][0],mutated=cell[0]!=parent_code[i][0]) for i,cell in enumerate(child_code)]
        return dict(tick=tick,actor=actor,decoded=[10,0,0],after=dict(code=parent_code),writes=writes)
    def birth(self,tick,actor,child,generation,parent_code,child_code,start):
        return dict(tick=tick,actor=actor,decoded=[12,0,0],after=dict(code=parent_code),birth=dict(write_ids=list(range(start,start+27)),startup_energy=12,child=dict(id=child,parent=actor,generation=generation,energy=12,code=child_code)))
    def food(self,tick,actor,code,site=1,success=1):
        return dict(tick=tick,actor=actor,decoded=[6,0,0],after=dict(code=code),attempt=dict(position=site,success=success))
    def events(self,novel=True):
        a=self.code(False,0);p=self.code(novel,100);c=self.code(novel,200)
        return [self.paid(1,0,a,p,0),self.birth(2,0,1,1,a,p,0),self.food(3,1,p),self.paid(4,1,p,c,27),self.birth(5,1,2,2,p,c,27),self.food(6,2,c)]
    def count(self,events):return census(events)['transmitted_function_associations']
    def test_exact_paid_temporal_join(self):self.assertEqual(self.count(self.events()),1)
    def test_ancestor_site1_not_novel(self):self.assertEqual(census(self.events(False))['novel_site1_actors'],0)
    def test_site2_is_supplied_behavior(self):
        e=self.events();e[2]['attempt']['position']=2;e[5]['attempt']['position']=2;self.assertEqual(self.count(e),0)
    def test_failed_act_not_function(self):
        e=self.events();e[5]['attempt']['success']=0;self.assertEqual(self.count(e),0)
    def test_empty_act_not_personal_attempt(self):
        e=self.events();del e[5]['attempt'];self.assertEqual(self.count(e),0);self.assertEqual(census(e)['actors'][2]['actions'],1)
    def test_parent_only_insufficient(self):self.assertEqual(self.count(self.events()[:-1]),0)
    def test_child_only_insufficient(self):
        e=self.events();del e[2];self.assertEqual(self.count(e),0)
    def test_parent_later_success_not_retroactive(self):
        e=self.events();food=e.pop(2);food['tick']=7;e.append(food);self.assertEqual(self.count(e),0)
    def test_child_program_mismatch(self):
        e=self.events();child=self.code(False,200);e[3]=self.paid(4,1,self.code(),child,27);e[4]['birth']['child']['code']=child;e[5]['after']['code']=child;self.assertEqual(self.count(e),0)
    def test_parent_noop_write_before_birth_excludes(self):
        e=self.events();e[3]['self_write']=dict(old=1,value=1);self.assertEqual(self.count(e),0)
    def test_child_noop_write_before_success_excludes(self):
        e=self.events();e[5]['self_write']=dict(old=1,value=1);self.assertEqual(self.count(e),0)
    def test_later_child_write_keeps_earlier_observation(self):
        e=self.events();e.append(dict(tick=7,actor=2,decoded=[9,0,0],after=dict(code=self.code(True,200)),self_write=dict(old=1,value=1)));self.assertEqual(self.count(e),1)
    def test_unpaid_birth_refused(self):
        e=self.events();e[4]['birth']['write_ids'][0]=999
        with self.assertRaises(AssertionError):census(e)
    def test_foreign_certificate_refused(self):
        e=self.events();e[4]['birth']['write_ids'][0]=0
        with self.assertRaises(AssertionError):census(e)
    def test_paid_value_unit_join_refused(self):
        e=self.events();e[4]['birth']['child']['code']=copy.deepcopy(e[4]['birth']['child']['code']);e[4]['birth']['child']['code'][0][1]=999
        with self.assertRaises(AssertionError):census(e)
    def test_startup_refused(self):
        e=self.events();e[4]['birth']['startup_energy']=0
        with self.assertRaises(AssertionError):census(e)
    def test_duplicate_identity_refused(self):
        e=self.events();e[4]['birth']['child']['id']=1
        with self.assertRaises(AssertionError):census(e)
    def test_foreign_actor_refused(self):
        e=self.events();e[5]['actor']=99
        with self.assertRaises(AssertionError):census(e)
    def test_death_and_zero_resource_denominator_retained(self):
        e=self.events()[:-1];e.append(dict(tick=6,actor=2,decoded=[17,0,0],death=[]));c=census(e);self.assertEqual((len(c['actors']),len(c['deaths']),c['actors'][2]['food_by_site'],c['actors'][2]['alive']),(3,1,[0,0,0,0],False))
    def test_dead_actor_cannot_act(self):
        e=self.events();e[5]['death']=[];e.append(self.food(7,2,self.code(True,200)))
        with self.assertRaises(AssertionError):census(e)
    def test_boolean_word_and_certificate_refused(self):
        p=self.code();p[0][0]=True
        with self.assertRaises(AssertionError):words(p)
        e=self.events();e[0]['writes'][0]['write_id']=True
        with self.assertRaises(AssertionError):census(e)
    def test_orientation_is_not_replication(self):
        self.assertFalse(replicated_contexts([(55000,'mutating',1),(55001,'mutating',1)])['replicated_association'])
        self.assertTrue(replicated_contexts([(55000,'mutating',1),(55002,'mutating',1)])['replicated_association'])
    def test_duplicate_or_reserve_observation_refused(self):
        for rows in ([(55000,'mutating',1)]*2,[(55100,'mutating',1)]):
            with self.assertRaises(AssertionError):replicated_contexts(rows)
    def test_ordinary_gate_is_full_lifecycle(self):
        s=dict(seed=55000,mode='faithful',formation_cost=43,remote_food=1,births=2,paid_copy_words=54,descendant_food=1,resource_then_birth=1,first_birth_tick=70)
        self.assertTrue(ordinary_gate(s))
        for key in ('descendant_food','resource_then_birth','remote_food'):
            failed=dict(s);failed[key]=0;self.assertFalse(ordinary_gate(failed))
        failed=dict(s);failed['births']=True;self.assertFalse(ordinary_gate(failed))
    def test_experiment_identity_refused_before_generic_audit(self):
        for seed,route,program in ((55100,'mobile55',PROGRAM),(55000,'mobile54',PROGRAM),(55000,'mobile55',[[0,0,0]])):
            with self.assertRaises(AssertionError):interpret(dict(seed=seed,mode='faithful',route=route,genesis_program=program))
    def test_all_paid_changes_transmitted_or_retained(self):
        c=census(self.events());self.assertEqual(c['mutated_words'],c['transmitted_mutated_words']+c['untransmitted_mutated_words'])
        self.assertEqual((c['paid_words'],len(c['edges'])),(54,2))
    def test_registry_restored_even_when_mock_history_fails(self):
        from experiments import digital_informative_exposure23 as substrate
        from experiments.digital_mobile55 import generate
        original=copy.deepcopy(substrate.PROGRAMS)
        def prepared_history(*args):
            self.assertEqual(args,(55000,'mobile55','faithful'));self.assertEqual(substrate.PROGRAMS['mobile55'],PROGRAM)
            raise RuntimeError('prepared mock, no World')
        with patch.object(substrate,'history',side_effect=prepared_history):
            with self.assertRaises(RuntimeError):generate(55000,'faithful')
        self.assertEqual(substrate.PROGRAMS,original)
    def test_foreign_source_unit_refused(self):
        e=self.events();e[0]['writes'][0]['source_unit']=999
        with self.assertRaises(AssertionError):census(e)
