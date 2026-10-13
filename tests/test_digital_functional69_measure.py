"""Prepared action/censor/family fixtures, not authentic paid histories."""
import copy
import unittest
from experiments import digital_functional69_referee as referee
from experiments import digital_functional69_measure as measure

PROVENANCE=dict(source_sha256='a'*64,configuration_sha256='b'*64)


def body(energy=12,pos=2):
    return referee.body(1,0,1,[[0,i] for i in range(27)],list(range(27,43)),pos)|dict(energy=energy)


def pair(kind,food=2,births=1,control_food=1,control_births=1,changed=True,censored=False):
    slot=dict(target=1 if kind=='parent' else 2,parent=0 if kind=='parent' else 1,generation=1 if kind=='parent' else 2,tick=10 if kind=='parent' else 20)
    result=[]
    for role,f,b,port in [('sham',food,births,0),('ancestor_value_control' if kind=='parent' else 'inherited_source_control',control_food,control_births,1)]:
        result.append(dict(verified=True,seed=1,slot_kind=kind,role=role,provenance=PROVENANCE,natural_history_hash='c'*64,slot=copy.deepcopy(slot),null=False,stage_credit=False,transition_mask=[0] if changed else [],target=dict(food=f,births=b,censored=censored,signatures=[['ACT',2,port]])))
    return result


class MeasurementFixtures(unittest.TestCase):
    def trace(self):
        trace=referee.PersonalTrace(dict(target=1,tick=10))
        trace.intervention(dict(tick=10,entities={'1':body()}),1)
        return trace

    def step(self,trace,before,decoded,terminal,extra=None,tick=11):
        state=dict(last=1,tick=tick,entities={'1':before})
        trace.before(state,decoded)
        event=dict(tick=tick,actor=1,decoded=decoded,before=referee.h(before),outcome='executed')
        event.update(extra or {})
        trace.after({},event,terminal)

    def test_empty_act_is_actual_action_not_food(self):
        trace=self.trace();before=body();before['registers']=[3,0]
        self.step(trace,before,[6,0,0],body(energy=11))
        target=trace.finish(dict(turns={'1':1}))
        self.assertEqual(target['signatures'],[['ACT',2,1]])
        self.assertEqual((target['food'],target['empty_act']),(0,1))
        self.assertTrue(target['censored'])

    def test_terminal_move_counted_as_complete_death(self):
        trace=self.trace();before=body(energy=1);terminal=body(energy=0,pos=1)
        self.step(trace,before,[13,0,0],terminal,dict(death=list(range(43))))
        target=trace.finish(dict(turns={'1':1}))
        self.assertEqual(target['signatures'],[['MOVE',1]])
        self.assertFalse(target['censored']);self.assertEqual(target['death_cause'],'zero_energy')

    def test_food_gain_and_cap_loss_are_paid_after_base(self):
        trace=self.trace();before=body(energy=60);terminal=body(energy=64)
        self.step(trace,before,[6,0,0],terminal,dict(attempt=dict(success=1)))
        target=trace.finish(dict(turns={'1':1}))
        self.assertEqual((target['food'],target['food_energy'],target['cap_loss_energy']),(1,5,15))

    def test_birth_and_expiry_same_step_complete(self):
        trace=self.trace();before=body(energy=40);terminal=body(energy=9)
        self.step(trace,before,[12,0,0],terminal,dict(birth={},expiry={}))
        target=trace.finish(dict(turns={'1':1}))
        self.assertEqual(target['births'],1);self.assertFalse(target['censored'])
        self.assertEqual(target['death_cause'],'execution_budget')

    def test_callback_order_hash_and_turn_refusals(self):
        trace=self.trace()
        with self.assertRaises(AssertionError):trace.after({}, {}, {})
        trace=self.trace();trace.before(dict(last=1,tick=11,entities={'1':body()}),[6,0,0])
        with self.assertRaises(AssertionError):trace.after({},dict(tick=11,actor=1,decoded=[6,0,0],before='d'*64),body())
        trace=self.trace()
        with self.assertRaises(AssertionError):trace.finish(dict(turns={'1':1}))

    def test_strict_pareto_and_shared_action_difference(self):
        p,c=pair('parent');result=measure.validate_pair(p,c,'parent',PROVENANCE)
        self.assertTrue(result['new_strategy']);self.assertFalse(result['stage_credit'])
        p['target']['births']=0
        self.assertFalse(measure.validate_pair(p,c,'parent',PROVENANCE)['useful'])

    def test_noop_censor_and_trace_length_alone_do_not_qualify(self):
        for changed,censored in [(False,False),(True,True)]:
            p,c=pair('parent',changed=changed,censored=censored)
            self.assertFalse(measure.validate_pair(p,c,'parent',PROVENANCE)['new_strategy'])
        p,c=pair('parent');c['target']['signatures']=[['ACT',2,0]]
        p['target']['signatures'].append(['MOVE',3])
        self.assertFalse(measure.validate_pair(p,c,'parent',PROVENANCE)['new_strategy'])

    def test_actual_family_and_child_own_birth_required(self):
        p,pc=pair('parent');c,cc=pair('child')
        result=measure.family_comparison(p,pc,c,cc,PROVENANCE)
        self.assertTrue(result['conditional_functional_contribution'])
        self.assertTrue(result['requires_authenticated_full_history']);self.assertFalse(result['stage_credit'])
        c['target']['births']=0;cc['target']['births']=0
        self.assertFalse(measure.family_comparison(p,pc,c,cc,PROVENANCE)['conditional_functional_contribution'])

    def test_unrelated_family_and_provenance_refused(self):
        p,pc=pair('parent');c,cc=pair('child')
        for x in (c,cc):x['slot']['parent']=99
        with self.assertRaises(AssertionError):measure.family_comparison(p,pc,c,cc,PROVENANCE)
        p,pc=pair('parent');pc['provenance']=dict(PROVENANCE,source_sha256='d'*64)
        with self.assertRaises(AssertionError):measure.validate_pair(p,pc,'parent',PROVENANCE)

    def test_null_child_keeps_denominator_and_prevents_contribution(self):
        p,pc=pair('parent');c,cc=pair('child')
        for x in (c,cc):x.update(null=True,slot=None,target=None,transition_mask=None)
        result=measure.family_comparison(p,pc,c,cc,PROVENANCE)
        self.assertFalse(result['conditional_functional_contribution']);self.assertTrue(result['child']['null'])


if __name__=='__main__':unittest.main()
