"""Authored possibility/negative fixtures; reserved panel seeds never used."""
import copy
import unittest
from experiments.redox import World,compatible,digest,ARMS
from experiments import redox_audit as independent

class RedoxTests(unittest.TestCase):
    def paired(self,arm='candidate'):
        w=World(17,arm);s,b,r=independent.initialize(17,arm)
        self.assertEqual(w.state,s);self.assertEqual(w.births,b)
        return w,s,b

    def apply(self,w,s,b,t,action,slot,kind=0,byte=0,token=0):
        d=[action,slot,token,kind,byte,0,0,0]
        self.assertEqual(w.advance(t,d),independent.step(s,b,t,d))
        self.assertEqual(w.state,s);self.assertEqual(w.births,b)

    def test_two_photon_prices_decay_and_recapture(self):
        w,s,b=self.paired();cell=w.state['slots'][0]['cell']
        self.apply(w,s,b,0,0,0);self.assertEqual(w.state['photons'][cell],14)
        self.apply(w,s,b,1,0,0);self.assertEqual(w.state['photons'][cell],14)
        self.apply(w,s,b,2,1,0);self.assertEqual(w.state['heat'],1)
        self.apply(w,s,b,3,3,0);self.assertEqual(w.state['heat'],2)
        self.apply(w,s,b,4,0,0);self.assertEqual(w.state['photons'][cell],12)
        self.assertEqual(w.state['slots'][0]['q'],2)
        self.assertEqual(b[-1]['atoms'],[0,1]);self.assertEqual(b[-1]['parents'],[48])

    def test_local_shortage_and_atomic_motion(self):
        w,s,b=self.paired();cell=s['slots'][0]['cell']
        for state in (w.state,s):state['photons'][cell]=1;state['heat']=15
        before=copy.deepcopy(w.state);self.apply(w,s,b,0,0,0)
        self.assertEqual(w.state['slots'],before['slots']);self.assertEqual(w.state['photons'],before['photons'])
        w,s,b=self.paired('mixed')
        for state in (w.state,s):state['thermal']=1;state['heat']=255
        self.apply(w,s,b,0,2,0);self.assertEqual(w.state['thermal'],1)
        self.assertEqual(w.state['stats']['motion'],0)

    def test_basal_acceptance_has_no_false_catalyst_ancestry(self):
        w,s,b=self.paired()
        for state in (w.state,s):
            for p in state['slots']:p['cell']=0
        j=next(j for j in range(16) if compatible(0,j))
        self.apply(w,s,b,0,0,0);self.apply(w,s,b,1,1,0)
        self.apply(w,s,b,2,0,1);self.apply(w,s,b,3,1,1,j,0)
        self.assertEqual(w.state['stats']['catalysis'],0)
        self.assertEqual(len(w.births[-1]['parents']),1)

    def test_authored_paid_damage_reconstruction_is_possible(self):
        w,s,b=self.paired()
        for state in (w.state,s):
            for p in state['slots']:p['cell']=0
        j=next(j for j in range(16) if compatible(0,j))
        k=next(k for k in range(16) if compatible(j,k))
        self.apply(w,s,b,0,0,0);self.apply(w,s,b,1,1,0)
        self.apply(w,s,b,2,0,1);self.apply(w,s,b,3,1,1,j,4,0)
        self.apply(w,s,b,4,0,2);self.apply(w,s,b,5,1,2,k,4,1)
        self.apply(w,s,b,2048,2,47)
        self.assertEqual(w.state['stats']['functional_damage'],2)
        self.apply(w,s,b,2049,0,1);self.apply(w,s,b,2050,0,0)
        self.apply(w,s,b,2051,1,0,0,0)
        self.apply(w,s,b,2052,1,1,j,4,0)
        self.apply(w,s,b,2053,0,3);self.apply(w,s,b,2054,1,3,k,4,1)
        self.assertTrue(w.record(17)['endpoint']);self.assertTrue(w.record(17)['exact'])
        self.assertEqual(sum(w.state['photons']),1012)
        self.assertEqual(w.state['heat'],10)

    def test_supplied_ancestry_and_withdrawal(self):
        w,s,b=self.paired('supplied')
        count=w.state['stats']['genesis'];self.assertLessEqual(count,12)
        self.assertEqual(w.state['operator'],16-count);self.assertEqual(w.state['heat'],2*count)
        uid=w.state['slots'][0]['uid']
        self.apply(w,s,b,0,3,0)
        self.assertTrue(w.state['slots'][0]['assisted']);self.assertEqual(b[-1]['parents'],[uid])
        w,s,b=self.paired('withdrawal');self.apply(w,s,b,0,0,0)
        self.apply(w,s,b,2048,0,1)
        self.assertEqual(w.state['exported'],1022);self.assertEqual(w.state['slots'][0]['q'],2)
        self.assertEqual(w.state['stats']['capture'],1)

    def test_all_arm_rng_and_independent_transitions(self):
        streams=[]
        for arm in ARMS:
            w,s,b=self.paired(arm);r=__import__('random').Random();r.setstate(w.initial_rng);history=[]
            for t in range(128):
                d=w.draws();self.assertEqual(d,independent.draw(r));history.append(d)
                self.assertEqual(w.advance(t,d),independent.step(s,b,t,d))
                self.assertEqual(digest(w.state),independent.sha(s))
            self.assertEqual(w.births,b);streams.append(history)
        self.assertTrue(all(x==streams[0] for x in streams))

    def test_inert_rejects_catalytic_only_byte(self):
        w,s,b=self.paired('inert')
        for state in (w.state,s):
            for p in state['slots']:p['cell']=0
        j=next(j for j in range(16) if compatible(0,j))
        self.apply(w,s,b,0,0,0);self.apply(w,s,b,1,1,0)
        self.apply(w,s,b,2,0,1);self.apply(w,s,b,3,1,1,j,4)
        self.assertIsNone(w.state['slots'][1]['kind']);self.assertEqual(w.state['stats']['catalysis'],0)

if __name__=='__main__':unittest.main()
