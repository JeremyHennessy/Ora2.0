import copy
import unittest
from unittest.mock import patch
from experiments import digital_source37_coverage as source
from experiments.digital_source37_independent import audit
from experiments.digital_branch_source30 import candidate as parent

class SourceCoverageTests(unittest.TestCase):
    def test_analytic_path_denominator_and_boundaries(self):
        self.assertEqual(source.COUNT,31360)
        for p in range(56):
            es=source.edits(p);self.assertEqual(len(es),560)
            self.assertEqual(len(set(es)),560);self.assertEqual(es[0][0],15);self.assertEqual(es[-1][0],38)
        self.assertEqual(source.candidate(31359)['source30_parent_id'],55)

    def test_one_extra_word_and_prefix_costs(self):
        for i in (0,7,8,38,69,70,559,560,31359):
            c=source.candidate(i);p=parent(c['source30_parent_id']);changes=[j for j,(a,b) in enumerate(zip(sum(c['program'],[]),sum(p['program'],[]))) if a!=b]
            self.assertEqual(changes,[c['external_mutations'][-1]['flat_address']]);self.assertEqual(c['program'][:5],p['program'][:5]);self.assertEqual(c['formation_cost'],55)

    def test_sample_is_deterministic_and_all_parents_retained(self):
        ids,draws=source.selection();self.assertEqual((ids,draws),source.selection());self.assertEqual(len(set(ids)),112)
        self.assertEqual([sum(i//560==p for i in ids) for p in range(56)],[2]*56)
        self.assertTrue(audit(source.manifest())['verified'])

    def test_identity_type_and_scope_refusal(self):
        for i in (True,-1,31360,1.0,'0'):
            with self.assertRaises(ValueError):source.candidate(i)

    def test_operand_aliases_remain_separate_paths(self):
        es=source.edits(0);same=[(i,e) for i,e in enumerate(es) if e[0]==16 and e[2] in (2,4)]
        self.assertEqual(len(same),2);self.assertNotEqual(same[0][0],same[1][0]);self.assertEqual(same[0][1][2]%2,same[1][1][2]%2)

    def test_no_cached_program_mutation(self):
        a=source.candidate(0);a['program'][0][0]=31;self.assertEqual(source.candidate(0)['program'][0][0],4)

    def test_independent_refuses_hash_ancestry_draw_and_cost_corruption(self):
        base=source.manifest()
        for key in ('hash','ancestry','draw','cost','id'):
            m=copy.deepcopy(base)
            if key=='hash':m['candidates'][0]['program_sha256']='bad'
            elif key=='ancestry':m['candidates'][0]['external_mutations'][0]['new']=2
            elif key=='draw':m['draws'][0]['raw']^=1
            elif key=='cost':m['candidates'][0]['formation_cost']=54
            else:m['path_ids'][0]^=1
            with self.assertRaises(AssertionError):audit(m)

    def test_manifest_claim_boundary(self):
        m=source.manifest();self.assertEqual(m['world_histories'],0);self.assertEqual(m['seeds_executed'],[])
        self.assertFalse(m['performance_selection']);self.assertFalse(m['learning']);self.assertFalse(m['evolution']);self.assertFalse(m['stage_credit'])

    def test_range_and_duplicate_rejections_are_retained(self):
        import json
        threshold=(2**32//560)*560
        def prepared_hash(payload):
            counter=json.loads(payload)[3];value=(threshold,0,0,1)[counter]
            class Prepared:
                def hexdigest(self):return f'{value:08x}'+'0'*56
            return Prepared()
        with patch.object(source.hashlib,'sha256',side_effect=prepared_hash):ids,draws=source.selection()
        self.assertEqual(ids,[p*560+x for p in range(56) for x in (0,1)])
        self.assertEqual(len(draws),224);self.assertEqual(sum(d['disposition']=='range_rejected' for d in draws),56);self.assertEqual(sum(d['disposition']=='duplicate_path_rejected' for d in draws),56)

if __name__=='__main__':unittest.main()
