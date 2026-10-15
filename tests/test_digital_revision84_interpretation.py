"""NON-PHYSICS history fragments and arithmetic; no World/target evaluation."""
import ast
import inspect
import unittest
from experiments import digital_revision84_metrics as metrics
from experiments import digital_revision84_acceptance as acceptance

def fragment():
    return dict(programme=[[7,8,1]],state=dict(events=[
        dict(attempt=dict(packet=0,cue=0,target=0,port=0,success=1)),
        dict(attempt=dict(packet=48,cue=0,target=1,port=0,success=0)),
        dict(decoded=[20,1,0],history_store=dict(address=0,before=0,after=15,blocked=0)),
        dict(history_read=dict(source_address=0)),
        dict(attempt=dict(packet=56,cue=0,target=1,port=1,success=1))]))

class Revision84InterpretationTests(unittest.TestCase):
    def test_requires_own_changed_observation_and_actual_source_channel(self):
        row=fragment();out=metrics.origins(row)
        self.assertEqual(len(out['postchange_correct_uses']),1)
        self.assertTrue(out['revisions'][0]['personally_changed'])
        row['state']['events'][3]['history_read']['source_address']=1
        self.assertEqual(metrics.origins(row)['postchange_correct_uses'],[])
        row=fragment();row['state']['events'].pop(0)
        self.assertEqual(metrics.origins(row)['postchange_correct_uses'],[])

    def test_frozen_store_creates_no_new_knowledge_origin(self):
        row=fragment();store=row['state']['events'][2]['history_store']
        store.update(blocked=1,after=0)
        self.assertEqual(metrics.origins(row)['revisions'],[])
        self.assertEqual(metrics.origins(row)['postchange_correct_uses'],[])
        store['after']=15
        with self.assertRaises(AssertionError):metrics.origins(row)

    def test_detached_or_incomplete_evidence_refused(self):
        with self.assertRaises(AssertionError):metrics.batch([],[])
        with self.assertRaises(AssertionError):acceptance.interpret([])
        row=fragment();row.update(seed=1009300,role='learner8',control='intact')
        proof=dict(verified=True,seed=row['seed'],role=row['role'],control=row['control'],history_sha256='0'*64)
        with self.assertRaises(AssertionError):metrics.summarize(row,proof)

    def test_exact_signs_ties_and_frozen_multiple_comparison_boundary(self):
        self.assertEqual(acceptance.signs([0]*16)['p'],dict(numerator=1,denominator=1))
        self.assertEqual(acceptance.signs([1,-1]+[0]*14)['p'],dict(numerator=3,denominator=4))
        self.assertFalse(acceptance.signs([1]*7+[0]*9)['passed'])
        self.assertTrue(acceptance.signs([1]*8+[0]*8)['passed'])
        self.assertEqual(acceptance.signs([-1]*16)['p'],dict(numerator=1,denominator=1))

    def test_interpretation_dependencies_are_separate(self):
        for module in (metrics,acceptance):
            tree=ast.parse(inspect.getsource(module))
            names=[]
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):names.extend(a.name for a in node.names)
                elif isinstance(node,ast.ImportFrom):names.append(node.module)
            self.assertTrue(set(names)<={'hashlib','json','fractions','math'})

if __name__=='__main__':unittest.main()
