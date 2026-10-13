"""Prepared constructor-free contract/provenance/denominator regression fixtures."""
import copy,json,unittest
from unittest.mock import patch
from experiments import digital_genotype66 as m
from experiments import digital_genotype66_runner as runner
from experiments import digital_genotype66_world as producer


def proof(seed,source=None,births=3,food=30):
    sources=m.registered_catalog();route,words=m.bound_role(seed,source,sources)
    founder=dict(births=births,food=food,turns=256,censored=False,death_cause='execution_budget')
    measured=dict(founder=founder,primary_endpoint=births,secondary_endpoint=food,
                  projection={},selection=False,causal_inheritance=False,learning=False,stage_credit=False)
    summary=dict(verified=True,seed=seed,route=route,mode='faithful',fuel_mode='renewed',formation_cost=43,
                 genesis_program_hash=m.full.h(words),births=19,turns={'0':256},turnover=dict(
                     founder_expiry_tick=853,post_founder_instructions=3243,maximum_generation=5,
                     post_founder_paid_personal_births=12,post_founder_renewed_food=400,
                     paid_personal_chains=[[1,2,3]],living_descendants=7))
    return dict(seed=seed,source_seed=source,history_hash=m.full.h([seed,words]),summary=summary,measured=measured,stage_credit=False)


def complete():return [proof(seed,source) for source in (None,)+m.SOURCE_SEEDS for seed in m.SEEDS]


class Prepared(unittest.TestCase):
    def setUp(self):
        self.trap=patch.object(producer.GenesisWorld,'__init__',side_effect=AssertionError('World forbidden in prepared tests'))
        self.trap.start();self.addCleanup(self.trap.stop)

    def test_catalog_whole_unscreened_identity(self):
        sources=m.registered_catalog();self.assertEqual(len(sources),16)
        self.assertEqual(sum(r['slot']['newborn_program']==m.ANCESTOR for r in sources.values()),4)
        self.assertTrue(all(not r['fate']['censored'] for r in sources.values()))

    def test_catalog_forgery_missing_or_duplicate_refused(self):
        sources=m.registered_catalog()
        for change in ('words','fate','history','missing'):
            wrong=copy.deepcopy(sources)
            if change=='words':wrong[66000]['slot']['newborn_program'][0]^=1
            elif change=='fate':wrong[66000]['fate']['births']+=1
            elif change=='history':wrong[66000]['history_hash']='wrong'
            else:del wrong[66000]
            with self.assertRaises(AssertionError):m.bound_role(67000,66000,wrong)

    def test_duplicate_genomes_keep_distinct_source_routes(self):
        sources=m.registered_catalog();a,wa=m.bound_role(67000,66002,sources);b,wb=m.bound_role(67000,66006,sources)
        self.assertNotEqual(a,b);self.assertEqual(wa,wb);self.assertEqual(wa,m.ANCESTOR)

    def test_binding_rejects_old_reserved_bool_and_unknown_source(self):
        sources=m.registered_catalog()
        for seed,source in ((1,None),(67100,None),(67300,66000),(True,None),(67000,True),(67000,66008)):
            with self.assertRaises(AssertionError):m.bound_role(seed,source,sources)

    def test_word_domain_refuses_bool_length_or_host_text(self):
        for words in ([True]*27,[0]*26,[32]*27,['__import__']*27):
            with self.assertRaises(AssertionError):producer.words_valid(words)
        producer.words_valid(m.ANCESTOR[:])

    def test_restore_requires_explicit_binding(self):
        with self.assertRaisesRegex(AssertionError,'Explicit paid genesis'):producer.GenesisWorld.restore({})

    def test_audit_provenance_before_full_audit(self):
        route,words=m.bound_role(67000,66000,m.registered_catalog())
        row=dict(seed=67000,route=route,mode='faithful',fuel_mode='renewed',genesis_program=[words[i:i+3] for i in range(0,27,3)],hash='fixture')
        for key,value in [('route','wrong'),('mode','mutating'),('fuel_mode','no_inflow'),('genesis_program',[[0,0,0]]*9)]:
            bad=copy.deepcopy(row);bad[key]=value
            with patch.object(m.full,'audit',side_effect=RuntimeError('must not reach')) as audit:
                with self.assertRaises(AssertionError):m.audit_row(bad,66000)
                audit.assert_not_called()

    def test_full_audit_before_projection_and_invalid_full_refusal(self):
        route,words=m.bound_role(67000,66000,m.registered_catalog())
        row=dict(seed=67000,route=route,mode='faithful',fuel_mode='renewed',genesis_program=[words[i:i+3] for i in range(0,27,3)],hash='fixture')
        with patch.object(m.full,'audit',side_effect=AssertionError('bad VM')),patch.object(m,'project_audited') as project:
            with self.assertRaises(AssertionError):m.audit_row(row,66000)
            project.assert_not_called()
        order=[];summary=dict(genesis_program_hash=m.full.h(words))
        with patch.object(m.full,'audit',side_effect=lambda r:(order.append('full') or summary)),patch.object(m,'project_audited',side_effect=lambda r,s:(order.append('project') or {})):
            m.audit_row(row,66000)
        self.assertEqual(order,['full','project'])

    def test_endpoint_dead_zero_and_censor_retained(self):
        for fate in (dict(turns=3,births=0,food=0,censored=False,death_cause='zero_energy'),dict(turns=200,births=2,food=19,censored=True,death_cause=None)):
            with patch.object(m.genotype_projection,'_project_audited',return_value=dict(actors={'0':fate})):
                r=m.project_audited({},dict(verified=True,formation_cost=43))
            self.assertEqual((r['primary_endpoint'],r['secondary_endpoint']),(fate['births'],fate['food']))
            self.assertEqual(r['founder']['censored'],fate['censored'])

    def test_changed_genesis_tracks_actual_words_and_birth_hash(self):
        words=[18,0,0,17,0,0]+[18,0,0]*7
        row=dict(mode='faithful',genesis_program=[words[i:i+3] for i in range(0,27,3)],final=dict(
            food={},events=[dict(actor=0,tick=0,decoded=[18,0,0],outcome='nop',after=dict(
                energy=11,code=[[v,i] for i,v in enumerate(words)])),
                dict(actor=0,tick=1,decoded=[17,0,0],outcome='halt',death=True)]))
        summary=dict(verified=True,formation_cost=43,genesis_program_hash=m.full.h(words),
                     ticks=2,births=0,deaths=1,successful_food=0,turns={'0':2},turnover=dict(
                     founder_expiry_tick=None,maximum_generation=0))
        result=m.project_audited(row,summary);founder=result['founder']
        self.assertEqual(founder['program_at_birth_hash'],m.full.h(words))
        self.assertEqual(founder['program_at_end_hash'],m.full.h(words))
        self.assertEqual((founder['turns'],founder['death_cause']),(2,'halt'))
        self.assertEqual((result['primary_endpoint'],result['secondary_endpoint']),(0,0))
        # The former ancestor-only ledger cannot follow the first changed NOP.
        with self.assertRaises(AssertionError):m.projection._project_audited(row,summary)

    def test_changed_genesis_hash_mismatch_refused_before_events(self):
        words=[18,0,0]*9
        row=dict(genesis_program=[words[i:i+3] for i in range(0,27,3)])
        with self.assertRaises(AssertionError):
            m.genotype_projection._project_audited(row,dict(verified=True,genesis_program_hash=m.full.h(m.ANCESTOR)))

    def test_whole_ordinary_checks_every_reference(self):
        roles=[proof(seed) for seed in m.SEEDS];roles[0]['summary']['births']=11
        with patch.object(m,'ordinary_gate',wraps=m.ordinary_gate) as gate:
            self.assertFalse(m.ordinary_admission(roles));self.assertEqual(gate.call_count,8)
        with self.assertRaises(AssertionError):m.ordinary_admission(roles[:-1]+[roles[0]])

    def test_complete_cohort_no_pooled_rescue_or_selection(self):
        result=m.cohort(complete());self.assertEqual(len(result['slots']),16)
        self.assertEqual(result['parent_worlds'],8);self.assertEqual(result['candidate_worlds'],128)
        self.assertFalse(any(s['benefit'] for s in result['slots']))
        self.assertFalse(result['selection']);self.assertFalse(result['candidate_promotion'])

    def test_strict_context_food_birth_and_unseen_gate(self):
        roles=complete()
        for r in roles:
            if r['source_seed']==66000:r['measured']['primary_endpoint']=4;r['measured']['founder']['births']=4
        self.assertTrue(m.cohort(roles)['slots'][0]['benefit'])
        roles[-1]['measured']['secondary_endpoint']-=1;roles[-1]['measured']['founder']['food']-=1
        for r in roles:
            if r['source_seed']==66000 and r['seed']==67203:r['measured']['secondary_endpoint']=29;r['measured']['founder']['food']=29
        self.assertFalse(m.cohort(roles)['slots'][0]['benefit'])

    def test_missing_duplicate_or_forged_route_refused(self):
        for wrong in ('missing','duplicate','route','genome'):
            roles=complete()
            if wrong=='missing':roles.pop()
            elif wrong=='duplicate':roles[-1]=copy.deepcopy(roles[0])
            elif wrong=='route':roles[-1]['summary']['route']='wrong'
            else:roles[-1]['summary']['genesis_program_hash']='wrong'
            with self.assertRaises(AssertionError):m.cohort(roles)

    def test_unchanged_full_history_and_measured_identity(self):
        for field in ('history_hash','measured'):
            roles=complete();r=next(p for p in roles if p['source_seed']==66002)
            if field=='history_hash':r[field]='different'
            else:r[field]['projection']={'different':True}
            with self.assertRaises(AssertionError):m.cohort(roles)

    def test_json_transport_preserves_complete_cohort(self):
        roles=complete();self.assertEqual(m.cohort(roles),m.cohort(json.loads(json.dumps(roles))))

    def test_runner_all_references_durable_before_sources(self):
        calls=[];saved=[]
        def run(where,seed,source):
            if source is not None:self.assertEqual(len(saved),1);self.assertEqual(sum(s is None for _,_,s in calls),16)
            calls.append((where,seed,source));return proof(seed,source)
        r=runner.panel(run,lambda receipt:saved.append(copy.deepcopy(receipt)))
        self.assertEqual(len(calls),272);self.assertEqual(r['original_roles'],136)
        self.assertEqual(saved[0]['source_world_calls'],0)

    def test_runner_failure_completes_all_references_no_sources(self):
        calls=[]
        def run(where,seed,source):
            self.assertIsNone(source);calls.append((where,seed));p=proof(seed)
            if seed==67000:p['summary']['births']=11
            return p
        r=runner.panel(run,lambda receipt:None);self.assertEqual(len(calls),16);self.assertIsNone(r['comparison'])

    def test_runner_failed_save_or_replay_disagreement_stops_sources(self):
        for mismatch in (False,True):
            calls=[]
            def run(where,seed,source):
                self.assertIsNone(source);calls.append((where,seed));p=proof(seed)
                if mismatch and where=='restored' and seed==67000:p['history_hash']='different'
                return p
            def save(receipt):raise AssertionError('durable failure')
            with self.assertRaises(AssertionError):runner.panel(run,save)
            self.assertEqual(len(calls),16)


if __name__=='__main__':unittest.main()
