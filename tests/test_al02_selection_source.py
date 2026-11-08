"""Inert authored log fixtures only: NEVER construct an AL02 World."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from experiments import al02_selection_request as admission
from experiments import al02_selection_referee as referee


def request():
    return dict(schema='AL02-SELECTION-REQUEST-v1',
                protocol_sha256=hashlib.sha256(admission.PROTOCOL.read_bytes()).hexdigest(),
                context_commitment='a' * 64, founder=[0, 2, 3, 4],
                source_pins=dict(admission.LEGACY_PINS))


def fixture(with_birth=False):
    """Literal bookkeeping table, not a policy, simulator or sampled history."""
    events = []
    def add(kind, tick, **fields):
        result = dict(event_id=len(events), tick=tick, kind=kind, **fields)
        events.append(result)
        return result
    add('GENESIS', 0, organism_id=0, tape_ops=[0, 2, 3, 4], tape_units=[0, 1, 2, 3],
        food_a=int(with_birth), food_b=0, energy=4, free_material=252)
    # actor,op,before,after,pc_before,pc_after,read,nursery,outcome,heat,pop
    rows = [
        (0,0,4,23,0,1,0,0,'ate_a',1,1),
        (0,2,23,21,1,2,1,1,'copied_one_byte',3,1),
        (0,3,21,20,2,1,1,1,'loop_copy',4,1),
        (0,2,20,18,1,2,2,2,'copied_one_byte',6,1),
        (0,3,18,17,2,1,2,2,'loop_copy',7,1),
        (0,2,17,15,1,2,3,3,'copied_one_byte',9,1),
        (0,3,15,14,2,1,3,3,'loop_copy',10,1),
        (0,2,14,12,1,2,4,4,'copied_one_byte',12,1),
        (0,3,12,11,2,3,4,4,'loop_finished',13,1),
        (0,4,11,4,3,0,0,0,'executed_division',16,2),
        (1,0,4,3,0,1,0,0,'food_unavailable',17,2),
        (0,0,4,3,0,1,0,0,'food_unavailable',18,2),
        (1,2,3,1,1,2,1,1,'copied_one_byte',20,2),
        (0,2,3,1,1,2,1,1,'copied_one_byte',22,2),
        (1,3,1,0,2,1,1,1,'loop_copy',23,2),
        (0,3,1,0,2,1,1,1,'loop_copy',24,1),
    ] if with_birth else [
        (0,0,4,3,0,1,0,0,'food_unavailable',1,1),
        (0,2,3,1,1,2,1,1,'copied_one_byte',3,1),
        (0,3,1,0,2,1,1,1,'loop_copy',4,1),
    ]
    writes = []
    births = []
    units = iter([4,5,6,7,8,9] if with_birth else [4])
    for tick, row in enumerate(rows, 1):
        actor, op, before, after, pc, nxt, read, nursery, outcome, heat, pop = row
        if op == 2:
            index = read - 1
            write = add('COPY_WRITE', tick, parent_id=actor,
                        parent_genome_hash=referee._hash([0,2,3,4]), source_index=index,
                        source_material_unit=index + (4 if actor else 0),
                        source_op=[0,2,3,4][index], material_unit=next(units),
                        written_op=[0,2,3,4][index], mutated=False,
                        nursery_index=index, paid_energy=2)
            writes.append(write['event_id'])
        if op == 4:
            birth = add('BIRTH', tick, parent_id=0, child_id=1,
                        parent_genome_hash=referee._hash([0,2,3,4]),
                        child_genome_hash=referee._hash([0,2,3,4]),
                        parent_genome_ops=[0,2,3,4], child_genome_ops=[0,2,3,4],
                        child_material_units=[4,5,6,7], copy_event_ids=writes[:],
                        generation=1, transferred_energy=4, genesis_seeded=False)
            births.append({key: val for key, val in birth.items() if key not in ('kind','tick')})
        add('EXEC', tick, organism_id=actor, opcode=op, pc_before=pc, pc_after=nxt,
            energy_before=before, energy_after=after, read_head_after=read,
            nursery_bytes_after=nursery, outcome=outcome, food_a=0, food_b=0,
            population_after_instruction=pop, heat=heat)
        if after == 0:
            add('DEATH', tick, organism_id=actor, reason='energy_exhausted',
                energy_released=0, abandoned_nursery=1)
    summary = dict(seed=0,variant='faithful',ticks=len(rows),world_extinct=True,
                   live_count=0,max_population=2 if with_birth else 1,
                   birth_count=int(with_birth),death_count=2 if with_birth else 1,
                   copy_events=6 if with_birth else 1,mutated_bytes_written=0,
                   failed_copy_attempts=0,failed_divisions=0,remaining_food_a=0,
                   remaining_food_b=0,consumed_food_a=int(with_birth),consumed_food_b=0,
                   remaining_material=256,heat=24 if with_birth else 4,
                   max_material_residual=0,max_energy_residual=0,
                   genesis_energy=24 if with_birth else 4,genesis_material=256,
                   remaining_tapes=[])
    return events, births, summary


class AdmissionTests(unittest.TestCase):
    def test_data_only_no_producer_import(self):
        with patch.dict('sys.modules', {'experiments.executed_heredity': None}):
            plan = admission.prepare_request(request())
        self.assertEqual(len(plan['slots']), 34)
        self.assertFalse(plan['execution_authorized'])
        self.assertEqual(plan['maximum_instructions'], 20400)

    def test_injected_founder_and_authority_fields_refused(self):
        for key, value in [('founder',[1,2,3,4]),('founder',[False,2,3,4]),
                           ('source_pins',{}),('protocol_sha256','0'*64),
                           ('context_commitment','not a digest')]:
            item = request(); item[key] = value
            with self.subTest(key=key,value=value), self.assertRaises(ValueError):
                admission.prepare_request(item)
        item=request(); item['authorized']=True
        with self.assertRaises(ValueError): admission.prepare_request(item)

    def test_json_encoding_duplicates_and_nonfinite(self):
        raw=admission.canonical(request())
        self.assertEqual(admission.parse_request(raw.replace(b',',b',\r\n')),request())
        for invalid in (b'{"a":1,"a":2}',b'{"a":NaN}',b'\xff',raw.decode().encode('utf-16')):
            with self.subTest(invalid=invalid[:20]), self.assertRaises((ValueError,UnicodeError)):
                admission.parse_request(invalid)

    def test_source_change_refused_before_any_effect(self):
        with patch.object(admission,'LEGACY_PINS',dict(admission.LEGACY_PINS)):
            admission.LEGACY_PINS['experiments/executed_heredity.py']='0'*64
            with self.assertRaises(ValueError): admission.prepare_request(request())

    def test_rehashed_protocol_replacement_is_not_approval(self):
        with patch.object(admission, 'PROTOCOL_PIN', '0'*64):
            with self.assertRaises(ValueError): admission.prepare_request(request())

    def test_opening_missing_denominator(self):
        plan=admission.prepare_request(request())
        with self.assertRaises(ValueError): admission.validate_opening(plan,{'schema':'AL02-SELECTION-CONTEXTS-v1','seeds':[]})
        with self.assertRaises(ValueError): referee.verify_panel(request(),{},[])


class RefereeTests(unittest.TestCase):
    def check(self, payload, **kwargs):
        return referee.verify_fixture(0,'faithful',int(kwargs.get('birth',False)),0,*payload)

    def test_literal_starvation_and_paid_birth_extinction(self):
        for birth in (False,True):
            result=self.check(fixture(birth),birth=birth)
            self.assertEqual(result['births'],int(birth))
            self.assertFalse(result['authenticated_execution'])
            self.assertIn('SYNTHETIC',result['scope'])

    def test_reordered_and_missing_history_refused(self):
        for mode in ('swap','truncate','extra'):
            payload=copy.deepcopy(fixture(True)); events=payload[0]
            if mode=='swap': events[1],events[2]=events[2],events[1]
            elif mode=='truncate': events.pop()
            else: events.append(copy.deepcopy(events[-1]))
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.check(payload,birth=True)

    def test_forged_birth_ancestry_rng_and_payment_refused(self):
        changes=[('BIRTH','parent_id',99),('BIRTH','child_genome_ops',[1,2,3,4]),
                 ('COPY_WRITE','written_op',1),('COPY_WRITE','paid_energy',1),
                 ('COPY_WRITE','material_unit',0),('EXEC','heat',999),
                 ('EXEC','food_a',1),('EXEC','organism_id',1),('EXEC','energy_after',True)]
        for kind,key,value in changes:
            payload=copy.deepcopy(fixture(True))
            next(event for event in payload[0] if event['kind']==kind)[key]=value
            with self.subTest(kind=kind,key=key), self.assertRaises(ValueError): self.check(payload,birth=True)

    def test_changed_founder_summary_or_receipt_refused(self):
        for mode in ('founder','fitness','receipt','origin'):
            payload=copy.deepcopy(fixture(True))
            if mode=='founder': payload[0][0]['tape_ops'][0]=1
            elif mode=='fitness': payload[2]['birth_count']=99
            elif mode=='origin': payload[0][0]['authenticated_execution']=True
            else: payload[1][0]['parent_id']=10
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.check(payload,birth=True)

    def test_synthetic_starvation_is_not_an_admitted_study_world(self):
        events,births,summary=fixture()
        with self.assertRaises(ValueError):
            referee._interpret(0,'faithful',12,18,events,births,summary)

    def test_actual_rng_order_on_inert_unmutated_fixture(self):
        events,births,summary=fixture(True)
        summary['variant']='mutating'
        result=referee.verify_fixture(0,'mutating',1,0,events,births,summary)
        self.assertEqual(result['births'],1)
        self.assertFalse(result['authenticated_execution'])

    def test_independent_mutation_branch_and_child_source_words(self):
        events,births,summary=copy.deepcopy(fixture(True))
        first=next(e for e in events if e['kind']=='COPY_WRITE')
        first.update(written_op=1,mutated=True)
        born=next(e for e in events if e['kind']=='BIRTH')
        born.update(child_genome_ops=[1,2,3,4],child_genome_hash=referee._hash([1,2,3,4]))
        births[0].update(child_genome_ops=[1,2,3,4],child_genome_hash=referee._hash([1,2,3,4]))
        next(e for e in events if e['kind']=='EXEC' and e['organism_id']==1)['opcode']=1
        child_write=next(e for e in events if e['kind']=='COPY_WRITE' and e['parent_id']==1)
        child_write.update(parent_genome_hash=referee._hash([1,2,3,4]),source_op=1,written_op=1)
        summary.update(variant='mutating',mutated_bytes_written=1)
        class Draws:
            def __init__(self): self.count=0
            def random(self):
                self.count+=1
                return 0.0 if self.count==1 else 1.0
            def randrange(self,n):
                if n!=5: raise AssertionError('wrong mutation alphabet')
                return 0
        draws=Draws()
        with patch.object(referee.random,'Random',return_value=draws):
            result=referee.verify_fixture(0,'mutating',1,0,events,births,summary)
        self.assertEqual(draws.count,6)
        self.assertEqual(result['actors'][1]['code'],[1,2,3,4])

    def test_mechanism_requires_food_inheritance_and_contemporary_a(self):
        # These are inert reconstructed-state selector fixtures, not log evidence.
        def actor(code,born,death,food,births):
            return dict(eligible=True,code=code,born=born,death=death,foods_b=food,births=births,
                        b_events=[dict(tick=born+1,food_before=1,coexisting=[1,2,3])])
        actors={1:actor([0,2,3,4],10,15,0,[]),2:actor([1,2,3,4],11,50,1,[3]),
                3:actor([1,2,3,4],20,49,1,[4]),4:actor([1,2,3,4],30,45,0,[])}
        self.assertTrue(referee.mechanism({'actors':actors})['demonstrated_in_log'])
        for mode in ('food','inheritance','timing','eligible'):
            changed=copy.deepcopy(actors)
            if mode=='food': changed[2]['foods_b']=0
            elif mode=='inheritance': changed[3]['code']=[0,2,3,4]
            elif mode=='timing': changed[1]['death']=11
            else: changed[2]['eligible']=False
            with self.subTest(mode=mode):
                self.assertFalse(referee.mechanism({'actors':changed})['demonstrated_in_log'])

    def test_no_mechanism_without_shared_food_opportunity(self):
        def actor(code,born,death,food,births):
            return dict(eligible=True,code=code,born=born,death=death,foods_b=food,
                        births=births,b_events=[])
        actors={1:actor([0,2,3,4],10,15,0,[]),2:actor([1,2,3,4],11,50,1,[3]),
                3:actor([1,2,3,4],20,49,1,[4]),4:actor([1,2,3,4],30,45,0,[])}
        actors[2]['b_events']=[dict(tick=16,food_before=1,coexisting=[2])]
        self.assertFalse(referee.mechanism({'actors':actors})['demonstrated_in_log'])

    def test_panel_join_denominator_and_serializable_proof(self):
        # DATA join only. Transition verifier is mocked, never a World or run.
        manifest={'schema':'AL02-SELECTION-CONTEXTS-v1','seeds':[100]*16}
        req=request(); req['context_commitment']=admission.digest(manifest)
        slots=admission.prepare_request(req)['slots']
        records=[dict(role=s['role'],context_index=s['context_index'],
                      events=[],births=[],summary={}) for s in slots]
        verified=dict(births=0,actors={},eligible_births=[],ticks=0,extinct=True,
                      authenticated_execution=False)
        with patch.object(referee,'_interpret',return_value=verified):
            result=referee.verify_panel(req,manifest,records)
        self.assertFalse(result['primary_positive'])
        self.assertFalse(result['scientific_selection_claim'])
        self.assertEqual(result['deltas'],[0]*16)
        json.dumps(result)
        for invalid in (records[:-1], records[:-1]+[records[0]]):
            with self.subTest(length=len(invalid)), patch.object(referee,'_interpret',return_value=verified), self.assertRaises(ValueError):
                referee.verify_panel(req,manifest,invalid)

    def test_context_opening_is_bound_and_closed_contexts_refused(self):
        manifest={'schema':'AL02-SELECTION-CONTEXTS-v1','seeds':[100]*16}
        req=request(); req['context_commitment']=admission.digest(manifest)
        plan=admission.prepare_request(req)
        self.assertEqual(admission.validate_opening(plan,manifest),(100,)*16)
        for invalid in ([100]*15+[101],[0]*16,[5000]*16,[771177]*16,[True]*16):
            changed=dict(manifest,seeds=invalid)
            with self.subTest(invalid=invalid[-1]), self.assertRaises(ValueError):
                admission.validate_opening(plan,changed)

    def test_primary_11_vs_12_boundary_is_bookkeeping_not_science(self):
        manifest={'schema':'AL02-SELECTION-CONTEXTS-v1','seeds':[100]*16}
        req=request(); req['context_commitment']=admission.digest(manifest)
        slots=admission.prepare_request(req)['slots']
        for positive in (11,12):
            records=[dict(role=s['role'],context_index=s['context_index'],
                          events=[int(s['role']=='mixed_mutating' and s['context_index']<positive)],
                          births=[],summary={}) for s in slots]
            def inert_result(seed,variant,food_a,food_b,events,births,summary):
                return dict(births=events[0],actors={},eligible_births=[],ticks=0,
                            extinct=True,authenticated_execution=False)
            with self.subTest(positive=positive), patch.object(referee,'_interpret',side_effect=inert_result):
                result=referee.verify_panel(req,manifest,records)
            self.assertEqual(result['positive'],positive)
            self.assertEqual(result['primary_positive'],positive==12)
            self.assertFalse(result['scientific_selection_claim'])


if __name__=='__main__':
    unittest.main()
