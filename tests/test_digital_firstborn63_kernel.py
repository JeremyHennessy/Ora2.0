"""Authored partial tables only: never a prepared organism or valid full history."""
import unittest
from unittest.mock import patch
from experiments import digital_firstborn63_kernel as k

def child(energy=12):
    return dict(id=1,parent=0,generation=1,code=[[0,i] for i in range(27)],state_units=list(range(27,43)),memory=[0]*8,registers=[0,0],pc=0,cue=0,feedback=0,inbox=None,pos=0,energy=energy,nursery=[])

def birth(tick=70):
    c=child();p=child(30);p.update(id=0,parent=None,generation=0)
    return dict(tick=tick,actor=0,decoded=[12,0,0],before='derived',state_hash='derived',after=p,
                birth=dict(child=c,write_ids=list(range(27)),state_formation=[dict(unit=u,value=0,energy=1) for u in c['state_units']],startup_energy=12,release_energy=2))

def action(state,tick,opcode=18,success=None,writes=0,transfer=None,message=None):
    after=k.clone(state);energy=state['energy']-1
    e=dict(tick=tick,actor=1,decoded=[opcode,0,0],before=k.digest(state))
    if opcode==6:
        if success is not None:
            e['attempt']=dict(success=int(success),position=0,packet=16)
            if success:energy=min(64,energy+20)
    if writes:e['writes']=[dict(unit=i) for i in range(writes)];energy-=writes
    if transfer is not None:e['transfer']=transfer;energy-=1
    if message is not None:e['message']=dict(recipient=0,value=message)
    if opcode==17:energy=0
    after['energy']=energy
    if not energy:e['death']=[0]
    else:e['after']=after
    return e,after

class PreparedKernel(unittest.TestCase):
    def setUp(self):
        # Any accidental generator execution is an immediate software failure.
        self.trap=patch('experiments.digital_informative_exposure23.World',side_effect=AssertionError('World prohibited in prepared tables'))
        self.trap.start();self.addCleanup(self.trap.stop)

    def test_allowed_birth_genotype_only(self):
        a=[birth()];b=k.clone(a);b[0]['birth']['child']['code'][0][0]=7
        b[0]['before']='other';b[0]['state_hash']='other'
        self.assertEqual(k.paired_prefix(a,b),dict(birth_tick=70,changed=True))

    def test_unchanged_birth(self):
        self.assertFalse(k.paired_prefix([birth()],[birth()])['changed'])

    def test_copy_values_only(self):
        w=dict(unit=100,value=0,index=0,tick=69,source_unit=0,source_value=0,write_id=0,mutated=False)
        a=[dict(tick=69,actor=0,decoded=[10,0,0],before='x',state_hash='x',writes=[w],after=dict(nursery=[w]))]
        b=k.clone(a);b[0]['writes'][0].update(value=7,mutated=True);b[0]['after']['nursery'][0].update(value=7,mutated=True)
        self.assertEqual(k.normal_prefix(a),k.normal_prefix(b))
        self.assertEqual(k.prefix_fingerprint(a),k.prefix_fingerprint(b))

    def test_nonpermitted_birth_fields_refused(self):
        for field,value in [('pos',1),('energy',13),('memory',[1]*8),('registers',[1,0]),('pc',1),('feedback',1),('cue',1),('inbox',0),('state_units',list(range(28,44)))]:
            with self.subTest(field=field):
                a=[birth()];b=k.clone(a);b[0]['birth']['child'][field]=value
                with self.assertRaises(AssertionError):k.paired_prefix(a,b)

    def test_paid_fields_refused(self):
        for field,value in [('startup_energy',13),('release_energy',1),('write_ids',list(range(1,28)))]:
            with self.subTest(field=field):
                a=[birth()];b=k.clone(a);b[0]['birth'][field]=value
                with self.assertRaises(AssertionError):k.paired_prefix(a,b)

    def test_parent_genome_not_masked(self):
        a=[birth()];b=k.clone(a);b[0]['after']['code'][0][0]=3
        with self.assertRaises(AssertionError):k.paired_prefix(a,b)

    def test_faithful_nonexact_refused(self):
        a=[birth()];a[0]['birth']['child']['code'][0][0]=2
        with self.assertRaises(AssertionError):k.paired_prefix(a,k.clone(a))

    def test_dying_parent_recovery(self):
        state=birth()['after'];a=[dict(tick=69,actor=0,after=state),birth()]
        del a[-1]['after'];a[-1]['death']=[0]
        self.assertFalse(k.paired_prefix(a,k.clone(a))['changed'])

    def test_birthless_and_asymmetric(self):
        a=[dict(tick=1,actor=0,decoded=[17,0,0],before='x',state_hash='x',death=[0])]
        self.assertEqual(k.paired_prefix(a,k.clone(a)),dict(birth_tick=None,changed=False))
        with self.assertRaises(AssertionError):k.paired_prefix(a,[birth()])
        self.assertEqual(k.firstborn_window(a,1,True)['G'],0)

    def test_copy_identity_and_source_not_masked(self):
        w=dict(unit=100,value=0,index=0,tick=69,source_unit=0,source_value=0,write_id=0,mutated=False)
        a=[dict(tick=69,actor=0,writes=[w],after=dict(nursery=[w]))]
        for field in ('unit','index','tick','source_unit','source_value','write_id'):
            with self.subTest(field=field):
                b=k.clone(a);b[0]['writes'][0][field]+=1
                self.assertNotEqual(k.normal_prefix(a),k.normal_prefix(b))
                self.assertNotEqual(k.prefix_fingerprint(a),k.prefix_fingerprint(b))

    def test_unrelated_keys_remain(self):
        a=[dict(tick=1,actor=0,after=dict(code=[[1,0]],memory=[0],value=1,mutated=False),release=dict(energy=16))]
        for path in ('memory','value','mutated','code'):
            b=k.clone(a);b[0]['after'][path]=None
            self.assertNotEqual(k.normal_prefix(a),k.normal_prefix(b))
            self.assertNotEqual(k.prefix_fingerprint(a),k.prefix_fingerprint(b))

    def check_window(self,events,end=78,extinct=False):
        got=k.firstborn_window(events,end,extinct)
        self.assertEqual({n:got[n] for n in ('F','G')},k.literal_gain(events,events[0]['tick']))
        return got

    def test_real_failed_empty_and_food(self):
        events=[birth()];s=child()
        for tick,outcome in [(72,False),(74,None),(76,True)]:
            e,s=action(s,tick,6,outcome);events.append(e)
        got=self.check_window(events)
        self.assertEqual((got['F'],got['G'],got['failed_real'],got['empty']),(1,17,1,1))

    def test_copy_paid_after_birth(self):
        e,_=action(child(),72,10,writes=3);got=self.check_window([birth(),e])
        self.assertEqual((got['G'],got['paid_words']),(-4,3))

    def test_incoming_and_outgoing_removed(self):
        s=child(13);e,_=action(s,74,16,transfer=0)
        events=[birth(),dict(tick=71,actor=0,decoded=[16,0,0],transfer=1),e]
        got=self.check_window(events);self.assertEqual((got['G'],got['incoming'],got['outgoing']),(-1,1,1))

    def test_cap_loss(self):
        s=child();events=[birth()]
        for tick in range(71,75):e,s=action(s,tick,6,True);events.append(e)
        got=self.check_window(events);self.assertEqual((got['F'],got['cap_loss'],got['G']),(4,24,52))

    def test_halt_absorbing(self):
        e,_=action(child(),71,17);got=self.check_window([birth(),e],71,True)
        self.assertTrue(got['complete']);self.assertFalse(got['alive']);self.assertEqual((got['G'],got['halt_heat']),(-12,11))

    def test_no_fabricated_postdeath_channels(self):
        e,_=action(child(),71,17);got=self.check_window([birth(),e],71,True)
        record=got['records'][0]
        self.assertEqual(record['before'],k.digest(child()))
        self.assertEqual(record['program_before'],k.digest([0]*27))
        self.assertTrue(all(record[n] is None for n in ('state','program','memory','registers','pc','inbox')))

    def test_child_death_parent_continues(self):
        e,_=action(child(),71,17);got=self.check_window([birth(),e],512)
        self.assertTrue(got['complete']);self.assertFalse(got['alive'])

    def test_full_extinction_after_window_is_not_window_death(self):
        e,_=action(child(),71);got=self.check_window([birth(),e],400,True)
        self.assertTrue(got['alive']);self.assertTrue(got['complete'])

    def test_cutoff_global_and_late_censor(self):
        a=birth(504);e,_=action(a['birth']['child'],512,6,True)
        self.assertTrue(self.check_window([a,e],512)['complete'])
        a=birth(505);e,_=action(a['birth']['child'],512,6,True)
        self.assertFalse(self.check_window([a,e],512)['complete'])

    def test_later_steps_do_not_change_endpoint(self):
        e,s=action(child(),78);later,_=action(s,79,6,True)
        self.assertEqual(self.check_window([birth(),e])['F'],self.check_window([birth(),e,later],512)['F'])

    def test_second_birth_refused(self):
        with self.assertRaises(AssertionError):k.firstborn_window([birth(),birth(78)],512,False)

    def test_before_hash_and_energy_refusals(self):
        e,_=action(child(),72)
        for field in ('before','after'):
            b=k.clone(e)
            if field=='before':b[field]='wrong'
            else:b[field]['energy']+=1
            with self.assertRaises(AssertionError):k.firstborn_window([birth(),b],512,False)

    def test_inbox_interaction_not_discarded(self):
        s=child();s['inbox']=5;e,_=action(s,72)
        got=self.check_window([birth(),dict(tick=71,actor=0,message=dict(recipient=1,value=5)),e])
        self.assertEqual(got['records'][0]['inbox'],5)

    def test_invalid_numeric_boundaries(self):
        for tick in (-1,513,True):
            with self.assertRaises(AssertionError):k.firstborn_window([],tick,False)

if __name__=='__main__':unittest.main()
