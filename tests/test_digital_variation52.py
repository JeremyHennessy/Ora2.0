import unittest
from experiments.digital_variation52 import census,words,PROGRAM

class LineageFixtures(unittest.TestCase):
    def code(self,new=True):
        p=sum(PROGRAM,[]);p[6]=13 if new else p[6];return [[v,i] for i,v in enumerate(p)]
    def birth(self,tick,parent,child,generation,code):
        return dict(tick=tick,actor=parent,after=dict(code=code),birth=dict(child=dict(id=child,parent=parent,generation=generation,code=code)))
    def food(self,tick,actor,code):return dict(tick=tick,actor=actor,after=dict(code=code),attempt=dict(success=1,position=1))
    def events(self):
        p=self.code();return [self.birth(1,0,1,1,p),self.food(2,1,p),self.birth(3,1,2,2,p),self.food(4,2,p)]
    def test_stable_paid_lineage_join(self):self.assertEqual(census(self.events(),PROGRAM)['inherited_remote_function_witnesses'],1)
    def test_parent_only_is_insufficient(self):self.assertEqual(census(self.events()[:-1],PROGRAM)['inherited_remote_function_witnesses'],0)
    def test_child_only_is_insufficient(self):
        e=self.events();del e[1];self.assertEqual(census(e,PROGRAM)['inherited_remote_function_witnesses'],0)
    def test_ancestor_function_is_not_novel(self):
        e=self.events();p=self.code(False)
        for ev in e:
            ev['after']['code']=p
            if 'birth' in ev:ev['birth']['child']['code']=p
        self.assertEqual(census(e,PROGRAM)['novel_resource_actors'],0)
    def test_changed_child_is_not_exact_transfer(self):
        e=self.events();e[2]['birth']['child']['code']=self.code(False);e[3]['after']['code']=self.code(False)
        self.assertEqual(census(e,PROGRAM)['inherited_remote_function_witnesses'],0)
    def test_parent_self_write_disclosed(self):
        e=self.events();e[1]['self_write']=dict(old=1,value=2)
        self.assertEqual(census(e,PROGRAM)['inherited_remote_function_witnesses'],0)
    def test_child_self_write_disclosed(self):
        e=self.events();e[3]['self_write']=dict(old=1,value=2)
        self.assertEqual(census(e,PROGRAM)['inherited_remote_function_witnesses'],0)
    def test_even_noop_self_write_is_outside_registered_stable_assay(self):
        e=self.events();e[3]['self_write']=dict(old=1,value=1)
        self.assertEqual(census(e,PROGRAM)['inherited_remote_function_witnesses'],0)
    def test_parent_later_food_not_retroactive(self):
        p=self.code();e=[self.birth(1,0,1,1,p),self.birth(2,1,2,2,p),self.food(3,1,p),self.food(4,2,p)]
        self.assertEqual(census(e,PROGRAM)['inherited_remote_function_witnesses'],0)
    def test_wrong_parent_refused(self):
        e=self.events();e[2]['birth']['child']['parent']=0
        with self.assertRaises(AssertionError):census(e,PROGRAM)
    def test_boolean_program_word_refused(self):
        p=self.code();p[0][0]=True
        with self.assertRaises(AssertionError):words(p)
    def test_repeated_food_counts_one_edge(self):
        e=self.events()+[self.food(5,2,self.code())]
        self.assertEqual(census(e,PROGRAM)['inherited_remote_function_witnesses'],1)
    def test_unknown_actor_refused(self):
        with self.assertRaises(AssertionError):census([self.food(1,99,self.code())],PROGRAM)
