"""Prepared partial-state witnesses only: no World, paid-history or admission claim."""
import unittest
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as producer
from experiments import digital_sharedlineage68_transition as t
from experiments import digital_sharedlineage68_admission as admission
from experiments import digital_sharedlineage68_world as wrapper
from experiments import digital_sharedlineage68_fork_interpret as fork

PROVENANCE=dict(source_sha256='a'*64,configuration_sha256='b'*64)

def prepared():
    # Authored partial witness deliberately lacks a genesis/event replay.
    words=[]
    for index,ancestor in enumerate(t.ANCESTOR_WORDS):
        source=(ancestor+7)%32;identity=index
        draw=int(t.h([1,'mutation',identity])[:16],16)
        value=(source+1+(draw//100)%31)%32 if draw%100<8 else source
        words.append(dict(write_id=identity,index=index,actor=0,tick=index+1,
            source_unit=index,source_value=source,effective_source='parent_copy',
            effective_source_value=source,unit=100+index,value=value,
            mutation_draw=draw,mutated=value!=source))
    code=[[w['value'],w['unit']] for w in words]
    child=t.body(1,0,1,code,list(range(127,143)),2)
    state=dict(seed=1,mode='mutating',fuel_mode='renewed',inheritance_mode='parent_copy',
        tick=40,last=0,entities={1:child},turns={0:256,1:0},events=[],
        free=list(range(143,512)),heat=200,expiry_records=[dict(actor=0,turns=256)])
    slot=dict(target=1,parent=0,generation=1,tick=40,certificates=words,
        born_code=t.clone(code),post_step_hash=t.h({k:v for k,v in state.items() if k!='events'}))
    return state,slot

def summary(seed):
    return dict(verified=True,seed=seed,mode='faithful',inheritance_mode='parent_copy',
        route='ancestor',formation_cost=43,genesis_program_hash=t.h(t.ANCESTOR_WORDS),
        fuel_mode='renewed',births=12,turnover=dict(founder_expiry_tick=100,
        post_founder_instructions=128,maximum_generation=3,
        post_founder_paid_personal_births=1,post_founder_renewed_food=1,
        paid_personal_chains=[[1,2,3]],living_descendants=1))

class PreparedTransitionComponents(unittest.TestCase):
    def setUp(self):
        self.trap=patch.object(producer.World,'__init__',side_effect=AssertionError('Prepared tests prohibit World'))
        self.spy=self.trap.start();self.addCleanup(self.trap.stop)
        self.addCleanup(lambda:self.assertEqual(self.spy.call_count,0))

    def test_only_code_values_change(self):
        state,slot=prepared();before=t.clone(state)
        after,record=t.transition(state,slot,'c'*64,'ancestor_value_control',PROVENANCE)
        self.assertEqual(t.clone(state),before)
        expected=t.clone(state)
        for i,cell in enumerate(t.actor_record(expected['entities'],1)['code']):cell[0]=t.ANCESTOR_WORDS[i]
        self.assertEqual(after,expected)
        self.assertEqual(record['code_value_mask'],[i for i,c in enumerate(slot['born_code']) if c[0]!=t.ANCESTOR_WORDS[i]])
        self.assertTrue(t.validate_transition(state,after,record,slot,'c'*64,'ancestor_value_control',PROVENANCE))

    def test_sham_exact_and_noop_retained(self):
        state,slot=prepared()
        after,record=t.transition(state,slot,'c'*64,'sham',PROVENANCE)
        self.assertEqual(after,t.clone(state));self.assertEqual(record['before_hash'],record['after_hash'])
        # Seeded witness with source words chosen to yield literal ancestor words.
        for i,w in enumerate(slot['certificates']):
            draw=w['mutation_draw'];delta=1+(draw//100)%31 if draw%100<8 else 0
            w.update(source_value=(t.ANCESTOR_WORDS[i]-delta)%32,effective_source_value=(t.ANCESTOR_WORDS[i]-delta)%32,
                value=t.ANCESTOR_WORDS[i],mutated=delta!=0)
            state['entities'][1]['code'][i][0]=t.ANCESTOR_WORDS[i]
        slot['born_code']=t.clone(state['entities'][1]['code'])
        slot['post_step_hash']=t.h({k:v for k,v in state.items() if k!='events'})
        after,record=t.transition(state,slot,'c'*64,'ancestor_value_control',PROVENANCE)
        self.assertEqual(after,t.clone(state));self.assertEqual(record['code_value_mask'],[])

    def test_temporal_certificate_refusals(self):
        for key,value in [('source_value',32),('source_unit',True),('effective_source','ancestor_copy'),
                          ('mutation_draw',True),('mutation_draw',0),('mutated',0),('tick',40),('index',1),('actor',1)]:
            state,slot=prepared();slot['certificates'][0][key]=value
            with self.assertRaises(AssertionError):t.transition(state,slot,'c'*64,'sham',PROVENANCE)

    def test_cold_start_channel_refusals(self):
        for key,value in [('energy',13),('pc',1),('memory',[1]*8),('registers',[1,0]),
                          ('cue',1),('feedback',1),('inbox',0),('nursery',[{}])]:
            state,slot=prepared();state['entities'][1][key]=value
            slot['post_step_hash']=t.h({k:v for k,v in state.items() if k!='events'})
            with self.assertRaises(AssertionError):t.transition(state,slot,'c'*64,'sham',PROVENANCE)

    def test_complete_post_expiration_hash(self):
        for key,value in [('tick',41),('last',1),('free',[]),('heat',201),('expiry_records',[])]:
            state,slot=prepared();state[key]=value
            with self.assertRaises(AssertionError):t.transition(state,slot,'c'*64,'sham',PROVENANCE)

    def test_second_intervention_refused(self):
        state,slot=prepared();after,record=t.transition(state,slot,'c'*64,'ancestor_value_control',PROVENANCE)
        for key,value in [('heat',201),('free',[]),('last',1)]:
            bad=t.clone(after);bad[key]=value
            with self.assertRaises(AssertionError):t.validate_transition(state,bad,record,slot,'c'*64,'ancestor_value_control',PROVENANCE)

    def test_external_provenance_refused(self):
        for bad in [dict(PROVENANCE,extra='path'),dict(PROVENANCE,source_sha256='A'*64),dict(PROVENANCE,configuration_sha256=True)]:
            state,slot=prepared()
            with self.assertRaises(AssertionError):t.transition(state,slot,'c'*64,'sham',bad)

    def test_canonical_actor_aliases_refused(self):
        for actors in [{'01':{}},{True:{}},{'١':{}},{1:{},'1':{}}]:
            with self.assertRaises(AssertionError):t.actor_record(actors,1)

    def test_all_sixteen_gates_and_failure(self):
        original=[summary(i) for i in admission.SEEDS];restored=t.clone(original)
        with patch.object(admission,'ordinary_gate',wraps=admission.ordinary_gate) as gate:
            self.assertTrue(admission.ordinary_admission(original,restored));self.assertEqual(gate.call_count,16)
        original[0]['births']=11
        with patch.object(admission,'ordinary_gate',wraps=admission.ordinary_gate) as gate:
            self.assertFalse(admission.ordinary_admission(original,restored));self.assertEqual(gate.call_count,16)
        restored[-1]['seed']=restored[0]['seed']
        with self.assertRaises(AssertionError):admission.ordinary_admission(original,restored)

    def test_durable_receipt_strict_types(self):
        receipt=dict(PROVENANCE,references=16,treatment_worlds=0,original_restored_equal=True,all_paid_gates=True)
        self.assertTrue(admission.require_durable_admission(receipt,'a'*64,'b'*64))
        for key,value in [('references',16.0),('treatment_worlds',False),('original_restored_equal',1),
                          ('all_paid_gates',1),('source_sha256','d'*64),('configuration_sha256','d'*64)]:
            with self.assertRaises(AssertionError):admission.require_durable_admission(dict(receipt,**{key:value}),'a'*64,'b'*64)
        bad=summary(69000);bad['turnover']['living_descendants']=True
        with self.assertRaises(AssertionError):admission.ordinary_gate(bad)

    def test_full_audit_precedes_selection_and_world(self):
        natural=dict(inheritance_mode='parent_copy',mode='mutating',fuel_mode='renewed',route='ancestor',
            genesis_program=[t.ANCESTOR_WORDS[i:i+3] for i in range(0,27,3)])
        with (patch.object(wrapper.natural_full,'audit',side_effect=AssertionError('Full audit refusal')) as full,
              patch.object(wrapper,'slots_from_audited') as slots):
            with self.assertRaisesRegex(AssertionError,'Full audit refusal'):wrapper.history(natural,1,'sham',PROVENANCE)
            self.assertEqual(full.call_count,1);slots.assert_not_called()

    def test_endpoint_includes_death_and_censor(self):
        slot=dict(target=1,tick=1)
        final=dict(turns={1:2},events=[{},dict(actor=1,tick=2,birth={},attempt=dict(success=True)),
            dict(actor=1,tick=3,outcome='halt',death=[1])])
        self.assertEqual(fork.target_endpoint(final,slot),dict(turns=2,births=1,food=1,death_tick=3,death_cause='halt',censored=False))
        final['events'][-1]=dict(actor=1,tick=3,outcome='ordinary')
        self.assertEqual(fork.target_endpoint(final,slot),dict(turns=2,births=1,food=1,death_tick=None,death_cause=None,censored=True))

if __name__=='__main__':unittest.main()
