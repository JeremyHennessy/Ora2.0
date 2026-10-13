"""Twenty prepared cases. World constructors trapped; no scientific contexts."""
import copy
import json
import unittest
from unittest.mock import patch
from experiments import digital_birthcontext67_transition as m
from experiments import digital_birthcontext67_interpret as referee
from experiments import digital_birthcontext67_world as producer


def fixture(noop=False):
    seed = 1; words = []
    # Disclosed partial-state certificate fixture, not a fully paid history.
    for i in range(27):
        write_id = i
        if noop:
            while int(m.h([seed, 'mutation', write_id])[:16], 16) % 100 < 8 or any(
                    w['write_id'] == write_id for w in words):
                write_id += 27
        draw = int(m.h([seed, 'mutation', write_id])[:16], 16)
        source = i % 32
        value = ((source + 1 + (draw // 100) % 31) % 32 if draw % 100 < 8 else source)
        words.append(dict(unit=43+i, value=value, index=i, tick=10+i,
            source_unit=i, source_value=source, write_id=write_id,
            mutated=value != source, actor=0))
    code = [[w['value'], w['unit']] for w in words]
    child = m.body(1, 0, 1, code, list(range(70, 86)), 2)
    state = dict(seed=seed, mode='mutating', fuel_mode='renewed', tick=100,
        entities={'1':child}, turns={'0':256, '1':0}, last=0,
        food={'64':[2,1]}, heat=500, free=list(range(86, 512)), events=[])
    slot = dict(target=1, parent=0, generation=1, tick=100,
        certificates=words, born_code=code,
        post_step_hash=m.h({k:v for k,v in state.items() if k!='events'}))
    return state, slot


class Prepared(unittest.TestCase):
    def setUp(self):
        trap = patch.object(producer.kernel.World, '__init__',
                            side_effect=AssertionError('World forbidden'))
        trap.start(); self.addCleanup(trap.stop)

    def test_01_temporal_source_not_current_parent(self):
        before, slot = fixture()
        after, record = m.transition(before, slot, 'a'*64, 'remove_copy_mutations')
        self.assertEqual([v[0] for v in after['entities']['1']['code']], list(range(27)))
        self.assertTrue(record['mutation_mask'])
        self.assertEqual(before['entities']['1']['code'], slot['born_code'])

    def test_02_completed_parent_expiration(self):
        before, slot = fixture()
        self.assertNotIn('0', before['entities'])
        after, _ = m.transition(before, slot, 'a'*64, 'sham')
        self.assertEqual(after['turns']['0'], 256)
        self.assertEqual(after, before)

    def test_03_noop_keeps_material_and_full_state(self):
        before, slot = fixture(noop=True)
        after, record = m.transition(before, slot, 'a'*64, 'remove_copy_mutations')
        self.assertEqual(after, before); self.assertEqual(record['mutation_mask'], [])

    def test_04_sham_exact_state(self):
        before, slot = fixture()
        after, record = m.transition(before, slot, 'a'*64, 'sham')
        self.assertEqual(after, before); self.assertEqual(record['before_hash'], record['after_hash'])

    def test_05_units_tamper(self):
        self.tamper(lambda after: after['entities']['1']['code'][0].__setitem__(1, 511))

    def test_06_startup_tamper(self):
        self.tamper(lambda after: after['entities']['1'].__setitem__('energy', 13))

    def test_07_stock_tamper(self):
        self.tamper(lambda after: after['food'].__setitem__('65', [2,1]))

    def test_08_clock_tamper(self):
        self.tamper(lambda after: after.__setitem__('tick', 101))

    def test_09_scheduler_tamper(self):
        self.tamper(lambda after: after.__setitem__('last', 1))

    def test_10_second_edit_tamper(self):
        self.tamper(lambda after: after['entities']['1']['memory'].__setitem__(0, 1))

    def tamper(self, edit):
        before, slot = fixture()
        after, record = m.transition(before, slot, 'a'*64, 'remove_copy_mutations')
        edit(after)
        with self.assertRaises(AssertionError):
            m.validate_transition(before, after, record, slot, 'a'*64, 'remove_copy_mutations')

    def test_11_cold_experienced_absent_refused(self):
        for change in ('turns', 'pc', 'memory', 'absent'):
            before, slot = fixture()
            if change=='turns': before['turns']['1']=1
            elif change=='pc': before['entities']['1']['pc']=1
            elif change=='memory': before['entities']['1']['memory'][0]=1
            else: del before['entities']['1']
            slot['post_step_hash']=m.h({k:v for k,v in before.items() if k!='events'})
            with self.assertRaises(AssertionError): m.transition(before, slot, 'a'*64, 'sham')

    def test_12_wrong_identity_role_tick(self):
        for key, value in (('target',True), ('target',2), ('parent',2), ('tick',99)):
            before, slot=fixture(); slot[key]=value
            with self.assertRaises(AssertionError): m.transition(before, slot, 'a'*64, 'sham')
        before, slot=fixture()
        with self.assertRaises(AssertionError): m.transition(before, slot, 'a'*64, 'rescue')

    def test_13_certificate_forgery(self):
        for key, value in (('actor',2), ('source_value',32), ('value',True), ('tick',100)):
            before, slot=fixture(); slot['certificates'][0][key]=value
            with self.assertRaises(AssertionError): m.transition(before, slot, 'a'*64, 'sham')

    def test_14_missing_duplicate_reordered_copy(self):
        for change in ('missing','duplicate','order'):
            before, slot=fixture()
            if change=='missing': slot['certificates'].pop()
            elif change=='duplicate': slot['certificates'][1]=slot['certificates'][0]
            else: slot['certificates'].reverse()
            with self.assertRaises(AssertionError): m.transition(before, slot, 'a'*64, 'sham')

    def test_15_json_identity_canonical(self):
        self.assertEqual(m.actor_record({1:7},1),7)
        self.assertEqual(m.actor_record(json.loads('{"1":7}'),1),7)
        for bad in ({'01':7}, {True:7}, {1:7,'1':7}, {'+1':7}, {'١':7}):
            with self.assertRaises(AssertionError): m.actor_record(bad,1)

    def test_16_no_producer_import_in_referee(self):
        import ast
        from pathlib import Path
        tree=ast.parse(Path(referee.__file__).read_text())
        imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertFalse(any('digital_birthcontext67_world' in ast.unparse(n)
                              or 'digital_renewable64 as' in ast.unparse(n) for n in imports))

    def test_17_full_natural_audit_before_projection(self):
        natural=dict(mode='mutating',fuel_mode='renewed',route='ancestor',
                     genesis_program=[referee.ANCESTOR_WORDS[i:i+3] for i in range(0,27,3)])
        row=dict(version=m.VERSION,natural=natural,branch=None,generation=1,role='sham',transition=None)
        with patch.object(referee.natural_full,'audit',side_effect=AssertionError('bad ancestry')), \
             patch.object(referee,'slots_from_audited') as slots:
            with self.assertRaises(AssertionError): referee.audit(row)
            slots.assert_not_called()

    def test_18_null_slot_never_constructs(self):
        natural=dict(mode='mutating',fuel_mode='renewed',route='ancestor',
                     genesis_program=[referee.ANCESTOR_WORDS[i:i+3] for i in range(0,27,3)])
        with patch.object(producer.natural_full,'audit',return_value={'verified':True}), \
             patch.object(producer,'slots_from_audited',return_value={1:None}):
            result=producer.history(natural,1,'sham')
            self.assertIsNone(result['branch']); self.assertIsNone(result['transition'])
        before, slot=fixture()
        words=[{k:v for k,v in w.items() if k!='actor'} for w in slot['certificates']]
        birth=dict(child=before['entities']['1'],write_ids=[w['write_id'] for w in words])
        first=dict(actor=0,tick=100,birth=birth,state_hash=slot['post_step_hash'])
        final=dict(events=[dict(actor=0,writes=words),first,first])
        row=dict(seed=1,final=final,hash=m.h(final))
        slots=m.slots_from_audited(row,dict(verified=True,seed=1))
        self.assertEqual(slots[1]['target'],1)
        self.assertIsNone(slots[2]); self.assertIsNone(slots[3])

    def test_19_record_source_hash_and_assistance_bound(self):
        before, slot=fixture(); after, record=m.transition(before,slot,'a'*64,'sham')
        for key,value in (('natural_history_hash','b'*64),('assistance','organism repair'),('role','remove_copy_mutations')):
            wrong=copy.deepcopy(record); wrong[key]=value
            with self.assertRaises(AssertionError): m.validate_transition(before,after,wrong,slot,'a'*64,'sham')
        for died in (True,False):
            event=dict(actor=1,tick=2,outcome='executed')
            if died: event['death']=[]
            measured=referee.target_endpoint(dict(events=[{},event],turns={'1':1}),dict(target=1,tick=1))
            self.assertEqual((measured['births'],measured['food']),(0,0))
            self.assertEqual(measured['censored'],not died)

    def test_20_null_and_forged_extra_transition_refused(self):
        natural=dict(mode='mutating',fuel_mode='renewed',route='ancestor',
                     genesis_program=[referee.ANCESTOR_WORDS[i:i+3] for i in range(0,27,3)])
        row=dict(version=m.VERSION,natural=natural,branch=None,generation=1,role='sham',transition={})
        with patch.object(referee.natural_full,'audit',return_value={'verified':True}), \
             patch.object(referee,'slots_from_audited',return_value={1:None}):
            with self.assertRaises(AssertionError): referee.audit(row)
        row['extra_intervention']={}
        with self.assertRaises(AssertionError): referee.audit(row)


if __name__ == '__main__':
    unittest.main()
