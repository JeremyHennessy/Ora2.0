"""Prepared sampler/cost refusal fixtures, never candidate histories."""
import unittest
from experiments.digital_neutral_tail42_source import word, DrawStop, cold_prefix, OPS


class NeutralTailTests(unittest.TestCase):
    def test_range_rejection_precedes_modulo(self):
        draws=[]; stream=iter((2**32-1,0))
        self.assertEqual(word(0,5,0,draws,lambda _:next(stream)),1)
        self.assertEqual([d['disposition'] for d in draws],['range_rejected','accepted'])
        self.assertEqual(draws[0]['threshold'],2**32-4)

    def test_operand_maximum_is_accepted(self):
        draws=[];self.assertEqual(word(0,5,1,draws,lambda _:2**32-1),31)
        self.assertEqual(len(draws),1)

    def test_per_word_failure_keeps_all_rejections(self):
        draws=[]
        with self.assertRaises(DrawStop) as failure:word(0,5,0,draws,lambda _:2**32-1)
        self.assertEqual(len(draws),64);self.assertEqual(failure.exception.draws,draws)

    def test_global_limit_refuses_before_extra_draw(self):
        draws=[{}]*7000
        with self.assertRaises(DrawStop):word(0,5,1,draws,lambda _:0)
        self.assertEqual(len(draws),7000)

    def test_invalid_identity_is_not_silent_source_change(self):
        for args in ((True,5,0),(-1,5,0),(256,5,0),(0,4,0),(0,5,True)):
            with self.assertRaises(ValueError):word(*args,[],lambda _:0)

    def test_opcode_alphabet_preserves_existing_local_scope(self):
        for i,op in enumerate(OPS):self.assertEqual(word(0,5,0,[],lambda _,i=i:i),op)
        self.assertNotIn(9,OPS);self.assertNotIn(12,OPS)

    def test_cold_prefix_paid_orientation_ledger(self):
        a,b=cold_prefix()
        self.assertEqual([s['energy'] for s in a['steps']],[11,30,29,28,27])
        self.assertEqual([s['energy'] for s in b['steps']],[11,10,9,28,27])
        for x in (a,b):
            self.assertEqual(x['steps'][-1]['food'],63)
            self.assertEqual(x['memory'][1],1);self.assertFalse(x['world'])

    def test_raw_aliases_are_retained(self):
        x=word(0,5,2,[],lambda _:0);y=word(0,5,2,[],lambda _:13)
        self.assertNotEqual(x,y);self.assertEqual(x%13,y%13)
        self.assertEqual(word(0,5,1,[],lambda _:1),1)


if __name__=='__main__':unittest.main()
