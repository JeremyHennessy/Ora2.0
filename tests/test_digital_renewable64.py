"""Prepared small-state cases only; fresh ordinary/reserved seeds never run."""
import unittest
from unittest.mock import patch
from experiments import digital_renewable64 as p
from experiments import digital_renewable64_interpret as f


class Environment(unittest.TestCase):
    def state(self,mode='renewed'):
        # Explicit partial software state, not an organism/history certificate.
        w=object.__new__(p.World);w.seed=1;w.fuel_mode=mode;w.tick=64
        w.food={};w.offered=w.admitted=w.rejected=0;w.next_packet=64
        return w

    def test_uniform_inputs_capped_and_rejected_ids_consumed(self):
        w=self.state();w.food={i:[0,0] for i in range(32)}
        offers=w.input();self.assertEqual(len(offers),16)
        self.assertEqual((w.offered,w.admitted,w.rejected,w.next_packet),(16,12,4,80))
        self.assertEqual([o['packet'] for o in offers],list(range(64,80)))
        self.assertTrue(all(o['outcome']=='rejected' for o in offers[:4]))
        self.assertEqual([sum(v[0]==s for v in w.food.values()) for s in range(4)],[32,4,4,4])

    def test_no_inflow_and_off_cadence_leave_state_unchanged(self):
        for mode,tick in [('no_inflow',64),('renewed',63)]:
            w=self.state(mode);w.tick=tick;before=p.h(w.snapshot())
            self.assertIsNone(w.input());self.assertEqual(p.h(w.snapshot()),before)

    def test_direct_early_late_input_refused(self):
        for tick in (0,4160):
            w=self.state();w.tick=tick
            with self.assertRaises(AssertionError):w.input()

    def test_expiration_after_real_instruction_keeps_vm_after_body(self):
        # Paid body/stock states authored for one NOP. No World constructor.
        w=self.state('no_inflow');w.tick=10;w.mode='faithful';w.last=-1;w.next_id=1;w.writes=0
        code=[[18,i] for i in range(27)];e=p.World.body(0,None,0,code,list(range(27,43)),0);e['energy']=2
        w.entities={0:e};w.free=list(range(43,512));w.constructor_remaining=85;w.heat=53;w.formation=[]
        w.food={i:[0 if i<32 else 1+(i-32)//16,0] for i in range(64)}
        w.events=[];w.births=w.deaths=0;w.maximum=1;w.turns={0:255}
        with patch.object(p,'h',wraps=p.h):self.assertTrue(w.step())
        ev=w.events[0];self.assertEqual(ev['after']['energy'],1)
        self.assertEqual(ev['expiry']['energy'],1);self.assertEqual(ev['expiry']['turns'],256)
        self.assertEqual(ev['expiry']['body_before'],p.h(ev['after']))
        self.assertEqual(w.entities,{});self.assertEqual(w.free,list(range(512)))
        self.assertEqual(w.heat,55);self.assertNotEqual(ev['vm_state_hash'],ev['state_hash'])
        self.assertEqual(ev['state_hash'],p.h(w.snapshot(False)))
        before=p.h(w.snapshot());self.assertFalse(w.step());self.assertEqual(p.h(w.snapshot()),before)

    def test_vm_terminal_death_precedes_execution_expiration(self):
        w=self.state('no_inflow');w.tick=10;w.mode='faithful';w.last=-1;w.next_id=1;w.writes=0
        e=p.World.body(0,None,0,[[17,i] for i in range(27)],list(range(27,43)),0)
        w.entities={0:e};w.free=list(range(43,512));w.constructor_remaining=85;w.heat=43;w.formation=[]
        w.food={i:[0 if i<32 else 1+(i-32)//16,0] for i in range(64)}
        w.events=[];w.births=w.deaths=0;w.maximum=1;w.turns={0:255}
        w.step();ev=w.events[0]
        self.assertIn('death',ev);self.assertNotIn('expiry',ev);self.assertNotIn('after',ev)
        self.assertEqual(w.deaths,1);self.assertEqual(w.turns[0],256)


class Gate(unittest.TestCase):
    def setUp(self):
        trap=patch.object(p,'World',side_effect=AssertionError('World forbidden'))
        trap.start();self.addCleanup(trap.stop)
        self.s=dict(verified=True,seed=65000,mode='faithful',route='ancestor',formation_cost=43,
                    genesis_program_hash=f.h(f.ANCESTOR_WORDS),fuel_mode='renewed',births=12,
                    turnover=dict(founder_expiry_tick=2000,post_founder_instructions=128,maximum_generation=3,
                    post_founder_paid_personal_births=1,post_founder_renewed_food=1,paid_personal_chains=[[1,2,3]],living_descendants=1))

    def test_threshold_classifier_fixture_only(self):
        self.assertTrue(f.ordinary_gate(self.s))
        for key,value in [('post_founder_instructions',127),('maximum_generation',2),('post_founder_paid_personal_births',0),('post_founder_renewed_food',0),('paid_personal_chains',[]),('living_descendants',0),('founder_expiry_tick',None)]:
            s=f.clone(self.s);s['turnover'][key]=value;self.assertFalse(f.ordinary_gate(s))
        s=f.clone(self.s);s['births']=11;self.assertFalse(f.ordinary_gate(s))

    def test_source_reserved_identity_and_control_refusals(self):
        for key,value in [('seed',True),('seed',65100),('seed',1),('mode','mutating'),('route','other'),('formation_cost',55),('genesis_program_hash','other'),('fuel_mode','no_inflow')]:
            s=f.clone(self.s);s[key]=value
            with self.assertRaises(AssertionError):f.ordinary_gate(s)

    def test_full_row_extra_fields_and_false_assistance_refused(self):
        with self.assertRaises(AssertionError):f.audit(dict(hidden_teacher=True))
        row=dict(version='DIGITAL-RENEWABLE-ECOLOGY-64-v1',seed=1,mode='faithful',fuel_mode='renewed',route='ancestor',
                 genesis_program=[[17,0,0]],checkpoint={},final={},hash='',ancestor_supplied=False,checkpoint_replay=True,learning_demonstrated=False)
        with self.assertRaises(AssertionError):f.audit(row)

    def test_all_eight_roles_required_and_failure_does_not_skip_later_gates(self):
        rows=[]
        for seed in range(65000,65004):
            for mode in ('renewed','no_inflow'):
                s=f.clone(self.s);s['seed']=seed;s['fuel_mode']=mode;rows.append(s)
        self.assertTrue(f.ordinary_admission(rows))
        with patch.object(f,'ordinary_gate',side_effect=[False,True,True,True]) as gate:
            self.assertFalse(f.ordinary_admission(rows));self.assertEqual(gate.call_count,4)
        with self.assertRaises(AssertionError):f.ordinary_admission(rows[:-1])
        rows[-1]=f.clone(rows[0])
        with self.assertRaises(AssertionError):f.ordinary_admission(rows)


if __name__=='__main__':unittest.main()
