"""New authored software fixtures only. No candidate/source selection or primary runs."""
import copy
import unittest
from experiments.digital_budgeted_transfer_v1 import Fixture, SOFTWARE_ONLY
from experiments.digital_budgeted_transfer_referee_v1 import verify

WITNESS = [[7,4,1],[0,1,0],[19,0,1],[25,5,7],[6,0,0],[1,0,0],
           [25,0,1],[24,0,1],[20,1,0],[25,5,4],[7,0,1]]
FIXED = [[7,2,1],[6,0,0],[7,0,1]]

class InterfaceTests(unittest.TestCase):
    def fixture(self, code=WITNESS, **kw):
        return Fixture(copy.deepcopy(code), admission=SOFTWARE_ONLY, **kw)

    def test_admission_and_no_extra_actor_channels(self):
        with self.assertRaises(ValueError): Fixture(WITNESS)
        with self.assertRaises(ValueError): self.fixture([[7,2,1],[18,0,0]])
        with self.assertRaises(ValueError): self.fixture(order=(0,1,2,3,4,5,6,6))
        with self.assertRaises(ValueError): self.fixture(mask=True)

    def test_complete_map_algebra_and_atomic_final_response(self):
        costs = []
        for mask in range(16):
            f = self.fixture(mask=mask); result = f.run_fixture(); n = mask.bit_count()
            self.assertTrue(verify(WITNESS, mask, f.order, f.rows, result))
            self.assertEqual(result['transfer_correct'], 4)
            self.assertEqual(result['cost'], 104+8*n+16*(n>=2))
            self.assertEqual(result['ticks'], 59+4*n)
            self.assertIsNotNone(f.rows[-1]['response'])
            snapshot = copy.deepcopy(f.world.snapshot())
            self.assertFalse(f.step()); self.assertEqual(snapshot, f.world.snapshot())
            costs.append(result['cost'])
        self.assertEqual(sum(costs)/16, 131)

    def test_cheap_no_sense_baseline_not_padded(self):
        for mask in (0,5,15):
            f = self.fixture(FIXED, mask=mask); result=f.run_fixture()
            self.assertEqual((result['cost'],result['ticks']), (51,16))
            self.assertTrue(verify(FIXED, mask, f.order, f.rows, result))
            self.assertFalse(any('sense' in e for e in f.world.events))

    def test_used_memory_and_feedback_controls(self):
        intact=self.fixture(mask=15); a=intact.run_fixture()
        disrupted=self.fixture(mask=15,mode='history_disrupted'); b=disrupted.run_fixture()
        disabled=self.fixture(mask=15,mode='memory_disabled'); c=disabled.run_fixture()
        self.assertEqual(a['transfer_correct'], 4)
        self.assertLess(b['transfer_correct'], a['transfer_correct'])
        self.assertLess(c['transfer_correct'], a['transfer_correct'])
        self.assertEqual(b['completed'], 8)
        # Physical feedback and action rewards are preserved; delivered OBS is explicitly masked.
        self.assertTrue(any(x['intervention'] and x['intervention'].get('physical')==1
                            for x in disrupted.rows))
        for f,res in ((intact,a),(disrupted,b),(disabled,c)):
            self.assertTrue(verify(WITNESS,15,f.order,f.rows,res))
        prefix=next(i for i,x in enumerate(disrupted.rows) if x['intervention'])
        self.assertEqual(intact.rows[:prefix],disrupted.rows[:prefix])

    def test_order_and_packet_identity(self):
        f=self.fixture(mask=6,order=(3,1,0,2,7,5,4,6)); result=f.run_fixture()
        self.assertEqual(result['transfer_correct'],4)
        self.assertTrue(verify(WITNESS,6,f.order,f.rows,result))
        events=f.world.events
        for i,e in enumerate(events):
            if 'sense' in e:
                attempt=next(x['attempt'] for x in events[i:] if 'attempt' in x)
                self.assertEqual(e['sense']['packet'],attempt['packet'])

    def test_budget_refusal_no_hidden_label_or_partial_transition(self):
        f=self.fixture(FIXED,budget=20); result=f.run_fixture()
        self.assertEqual((result['completed'],result['cost'],result['stop']), (0,20,'budget'))
        self.assertTrue(all(x['correct'] is None for x in result['planned']))
        g=self.fixture(FIXED,mask=15,budget=20); other=g.run_fixture()
        self.assertEqual(result,other)

    def test_restore_includes_task_control_and_scheduler_identity(self):
        f=self.fixture(mask=9,mode='history_disrupted')
        for _ in range(25): self.assertTrue(f.step())
        sealed=f.snapshot()
        g=Fixture.restore(sealed,admission=SOFTWARE_ONLY)
        self.assertEqual(f.run_fixture(),g.run_fixture())
        self.assertEqual(f.snapshot(),g.snapshot())
        bad=copy.deepcopy(sealed); bad['payload']['world']['tick']+=1
        with self.assertRaises(ValueError): Fixture.restore(bad,admission=SOFTWARE_ONLY)

    def test_referee_rejects_tampered_cost_label_and_endpoint(self):
        f=self.fixture(mask=5); result=f.run_fixture()
        for kind in ('cost','label','extra_tail','packet'):
            rows=copy.deepcopy(f.rows); res=copy.deepcopy(result)
            if kind=='cost': rows[-1]['charged']-=1
            elif kind=='label': rows[-1]['response']['correct']=False
            elif kind=='packet': rows[-1]['response']['packet']=rows[4]['response']['packet'] if rows[4]['response'] else 0
            else: rows.append(copy.deepcopy(rows[-1]))
            with self.assertRaises(AssertionError): verify(WITNESS,5,f.order,rows,res)

if __name__ == '__main__': unittest.main()
