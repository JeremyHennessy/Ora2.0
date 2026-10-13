"""Prepared software tables and an authored extinction row; never World.

Seed1 is an explicit non-scientific arithmetic fixture, never a panel seed.
Partial paid-birth tables are deliberately not asserted as valid full VM runs.
"""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from experiments import digital_firstborn63_integration as f

PROGRAM=[[18,0,0] for _ in range(9)]

def paid_table(mode='faithful'):
    state=f.body(0,None,0,[[v,i] for i,v in enumerate(sum(PROGRAM,[]))],list(range(27,43)),0)
    events=[];tick=0;packet=0
    def step(op,writes=None,birth=None):
        nonlocal tick,packet,state
        tick+=1;event=dict(tick=tick,actor=0,decoded=[op,0,0],before=f.h(state))
        after=f.clone(state);after['energy']-=1
        if op==6:
            event['attempt']=dict(packet=packet,position=0,success=1);packet+=1
            after['energy']=min(64,after['energy']+20)
        if writes:
            event['writes']=writes;after['energy']-=len(writes);after['nursery']+=f.clone(writes)
        if birth:
            event['birth']=birth;after['energy']-=30;after['nursery']=[]
        event['after']=after;events.append(event);state=after
    for i in range(9):
        step(6);writes=[]
        for index in range(i*3,i*3+3):
            draw=int(f.h([1,'mutation',index])[:16],16);mutated=mode=='mutating' and draw%100<8
            value=(state['code'][index][0]+1+(draw//100)%31)%32 if mutated else state['code'][index][0]
            writes.append(dict(unit=43+index,value=value,index=index,tick=tick+1,source_unit=index,
                               source_value=state['code'][index][0],write_id=index,mutated=mutated))
        step(10,writes)
    nursery=state['nursery'];child=f.body(1,0,1,[[w['value'],w['unit']] for w in nursery],list(range(70,86)),0)
    step(12,birth=dict(child=child,write_ids=list(range(27)),startup_energy=12,release_energy=2))
    return events

def halted_row():
    program=[[17,0,0]]+PROGRAM[1:];values=sum(program,[])
    initial=f.body(0,None,0,[[v,i] for i,v in enumerate(values)],list(range(27,43)),0)
    final=dict(seed=1,mode='faithful',tick=1,last=0,next_id=1,writes=0,constructor_remaining=85,heat=55,
               formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(values+[0]*16)],
               food={i:[0 if i<32 else 1+(i-32)//16,int(f.h([1,'food',i])[:8],16)%2] for i in range(64)},
               free=list(range(512)),entities={},births=0,deaths=1,maximum=1)
    event=dict(tick=1,actor=0,decoded=[17,0,0],before=f.h(initial),outcome='halt',death=list(range(43)),state_hash=f.h(f.clone(final)))
    final['events']=[event];final=f.clone(final)
    return dict(version='DIGITAL-INFORMATIVE-EXPOSURE-23-v1',seed=1,mode='faithful',route='authored-halt-fixture',
                genesis_program=program,final=final,checkpoint=f.clone(final),hash=f.h(final),
                ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False)

def complete_pairs():
    pairs=[]
    for role in (None,)+f.ROSTER:
        for seed in f.SEEDS:
            pairs.append(dict(seed=seed,arm='withheld' if role is None else 'retained',
                              source=None if role is None else dict(seed=role[0],child=role[1]),
                              changed=True,complete=True,F=1,G=19,
                              faithful=dict(F=1,G=18),mutating=dict(F=0,G=-1)))
    return pairs

class PreparedIntegration(unittest.TestCase):
    def setUp(self):
        self.trap=patch('experiments.digital_informative_exposure23.World',side_effect=AssertionError('World prohibited'))
        self.trap.start();self.addCleanup(self.trap.stop)

    def manifest(self):
        return json.loads((Path(__file__).resolve().parents[1]/'docs/DIGITAL-TRANSFER-57-SOURCE.json').read_bytes())['summary']

    def envelope(self,role=None):
        manifest=self.manifest();arm='withheld' if role is None else 'retained'
        program,origin=f.choice(arm,role,manifest)
        return dict(version=f.VERSION,arm=arm,source=origin,source_manifest_hash=f.SOURCE_HASH,
                    history=dict(seed=f.SEEDS[0],mode='faithful',genesis_program=program))

    def test_all_sources_and_baseline_identity(self):
        for role in (None,)+f.ROSTER:
            e=self.envelope(role);program,origin=f.identity(e,self.manifest())
            self.assertEqual(program,e['history']['genesis_program']);self.assertEqual(origin,e['source'])

    def test_origin_hash_type_and_extra_field_refusals(self):
        e=self.envelope(f.ROSTER[0])
        for key,value in [('seed',True),('child',True),('program_hash','wrong'),('source_row_hash','wrong'),('extra',1)]:
            with self.subTest(key=key):
                bad=f.clone(e);bad['source'][key]=value
                with self.assertRaises(AssertionError):f.identity(bad,self.manifest())

    def test_reserved_wrong_seed_mode_and_genome_refused(self):
        for key,value in [('seed',64100),('seed',64300),('seed',True),('mode','copy_disabled'),('genesis_program',PROGRAM)]:
            with self.subTest(key=key,value=value):
                e=self.envelope();e['history'][key]=value
                with self.assertRaises(AssertionError):f.identity(e,self.manifest())

    def test_manifest_tampering_and_role_refused(self):
        e=self.envelope();m=self.manifest();m['eligible']-=1
        with self.assertRaises(AssertionError):f.identity(e,m)
        e['arm']='retained'
        with self.assertRaises(AssertionError):f.identity(e,self.manifest())

    def test_mutation_aware_paid_ancestry(self):
        a=f.census(PROGRAM,paid_table(),1,'faithful')
        b=f.census(PROGRAM,paid_table('mutating'),1,'mutating')
        self.assertEqual(a['paid_words'],27);self.assertEqual(b['paid_words'],27)
        self.assertTrue(a['edges'][0]['exact_program_transfer']);self.assertGreater(b['mutations'],0)
        self.assertEqual(b['edges'][0]['mutated_words'],b['mutations'])
        self.assertFalse(b['edges'][0]['exact_program_transfer']);self.assertEqual(b['actors'][1]['endpoint_energy'],12)

    def test_mutation_certificate_law_refusals(self):
        events=paid_table('mutating');target=next(e for e in events if e.get('writes'))
        for field,value in [('mutated',1),('value',31),('source_value',31),('source_unit',31),('write_id',999)]:
            with self.subTest(field=field):
                bad=f.clone(events);bad[events.index(target)]['writes'][0][field]=value
                with self.assertRaises(AssertionError):f.census(PROGRAM,bad,1,'mutating')

    def test_paid_startup_zero_state_refusals(self):
        for field,value in [('energy',13),('memory',[1]*8),('pc',1),('pos',1),('inbox',0)]:
            with self.subTest(field=field):
                events=paid_table();events[-1]['birth']['child'][field]=value
                with self.assertRaises(AssertionError):f.census(PROGRAM,events,1,'faithful')

    def test_copied_unit_ancestry_and_energy_refusals(self):
        events=paid_table();events[-1]['birth']['child']['code'][0][1]=999
        with self.assertRaises(AssertionError):f.census(PROGRAM,events,1,'faithful')
        events=paid_table();events[-1]['after']['energy']+=1
        with self.assertRaises(AssertionError):f.census(PROGRAM,events,1,'faithful')

    def test_generic_full_vm_extinction_fixture(self):
        row=halted_row();checked=f.audit(row)
        self.assertEqual((checked['ticks'],checked['deaths'],checked['live_energy']),(1,1,0))
        ledger=f.census(row['genesis_program'],row['final']['events'],1,'faithful')
        s=ledger['actors'][0]['steps'][0]
        self.assertIsNone(s['after']);self.assertIsNone(s['program_after']);self.assertIsNone(s['pc_after'])
        self.assertEqual(ledger['actors'][0]['halt_heat'],11)

    def test_generic_vm_failure_precedes_ledger(self):
        row=halted_row();row['final']['heat']+=1
        envelope=dict(history=row,arm='withheld')
        with patch.object(f,'identity',return_value=(row['genesis_program'],None)),patch.object(f,'census',side_effect=AssertionError('ledger must not run')) as ledger:
            with self.assertRaises(AssertionError):f.interpret(envelope,{})
            ledger.assert_not_called()

    def test_full_vm_projection_wiring_birthless(self):
        row=halted_row();e=dict(history=row,arm='withheld')
        # Identity is deliberately substituted only for this authored non-source
        # row. Real enrollment is exercised separately and never bypassed in API.
        with patch.object(f,'identity',return_value=(row['genesis_program'],None)):
            result=f.interpret(e,{})
        self.assertEqual((result['window']['F'],result['window']['G']),(0,0))
        self.assertFalse(result['stage_credit']);self.assertEqual(result['summary']['deaths'],1)

    def test_complete_whole_cohort_and_separate_baseline(self):
        pairs=complete_pairs();pairs[0].update(F=-99,G=-99,faithful=dict(F=0,G=-100),mutating=dict(F=99,G=-1))
        result=f.cohort(pairs)
        self.assertTrue(result['causal_early_firstborn_fidelity_benefit']);self.assertEqual(result['unique_histories'],288)
        self.assertEqual(len(result['contexts']),8);self.assertFalse(result['stage_credit'])

    def test_missing_duplicate_and_reserved_cohort_refused(self):
        pairs=complete_pairs()
        with self.assertRaises(AssertionError):f.cohort(pairs[:-1])
        pairs[-1]=f.clone(pairs[0])
        with self.assertRaises(AssertionError):f.cohort(pairs)
        pairs=complete_pairs();pairs[-1]['seed']=64100
        with self.assertRaises(AssertionError):f.cohort(pairs)

    def test_each_context_no_pooled_rescue(self):
        for seed in f.SEEDS[::2]:
            pairs=complete_pairs()
            for p in pairs:
                if p['arm']=='retained' and p['seed'] in (seed,seed+1):
                    p.update(F=0,faithful=dict(F=0,G=18))
            result=f.cohort(pairs)
            self.assertFalse(result['causal_early_firstborn_fidelity_benefit'])

    def test_underexposure_keeps_all_pairs(self):
        pairs=complete_pairs()
        for p in pairs:
            if p['seed'] in (64200,64201) and p['arm']=='retained':p['changed']=False
        result=f.cohort(pairs)
        self.assertTrue(result['contexts'][4]['underexposed']);self.assertEqual(len(result['pairs']),144)
        self.assertFalse(result['causal_early_firstborn_fidelity_benefit'])

    def test_censored_baseline_or_source_blocks_acceptance(self):
        for index in (0,16):
            pairs=complete_pairs();pairs[index]['complete']=False
            self.assertFalse(f.cohort(pairs)['causal_early_firstborn_fidelity_benefit'])

    def test_cohort_delta_and_bool_counter_refused(self):
        for key,value in [('F',True),('G',0),('changed',1),('complete',1)]:
            pairs=complete_pairs();pairs[0][key]=value
            with self.assertRaises(AssertionError):f.cohort(pairs)

    def test_ordinary_full_lifecycle_gate(self):
        summary=dict(verified=True,seed=64000,arm='withheld',source=None,source_manifest_hash=f.SOURCE_HASH,
                     formation_cost=43,first_birth_tick=70,births=2,paid_copy_words=54,remote_food=1,descendant_food=1,resource_then_birth=1)
        result=dict(pair=dict(seed=64000,arm='withheld',source=None,complete=True,faithful=dict(F=1)),
                    histories=[dict(summary=dict(summary,mode='faithful')),dict(summary=dict(summary,mode='mutating'))])
        self.assertTrue(f.ordinary_gate(result))
        for key,value in [('formation_cost',42),('first_birth_tick',71),('births',1),('paid_copy_words',53),('remote_food',0),('descendant_food',0),('resource_then_birth',0)]:
            bad=f.clone(result);bad['histories'][0]['summary'][key]=value
            if key=='formation_cost':
                with self.assertRaises(AssertionError):f.ordinary_gate(bad)
            else:self.assertFalse(f.ordinary_gate(bad))

    def test_ordinary_all_sixteen_denominator(self):
        results=[dict(pair=dict(seed=s)) for s in f.SEEDS]
        with patch.object(f,'ordinary_gate',return_value=True):
            self.assertTrue(f.ordinary_admission(results))
            with self.assertRaises(AssertionError):f.ordinary_admission(results[:-1])
            results[-1]=results[0]
            with self.assertRaises(AssertionError):f.ordinary_admission(results)
        with patch.object(f,'ordinary_gate',side_effect=[False]+[True]*15) as gate:
            self.assertFalse(f.ordinary_admission([dict(pair=dict(seed=s)) for s in f.SEEDS]))
            self.assertEqual(gate.call_count,16)

if __name__=='__main__':unittest.main()
