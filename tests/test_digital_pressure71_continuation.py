"""Fixed software1/2,512-step actual continuation checks; never scientific evidence."""
import copy
import os
import unittest
from experiments import digital_pressure71_population as population
from experiments import digital_pressure71_world as wrapper
from experiments import digital_pressure71_referee as referee
from experiments import digital_pressure71_natural_referee as natural_referee

PROVENANCE=dict(source_sha256='b'*64,configuration_sha256='c'*64)


class ContinuationTests(unittest.TestCase):
    rows={};proofs={};rejected={}

    @classmethod
    def setUpClass(cls):
        seed=int(os.environ.get('ORA71_SOFTWARE_SEED','1'))
        dose=int(os.environ.get('ORA71_SOFTWARE_DOSE','1'))
        assert seed in (1,2) and dose in (1,8)
        cls.natural=population.history(seed,mode='mutating',dose=dose,
                                      horizon=512,software_only=True)
        cls.natural_proof=natural_referee.audit(cls.natural)
        cls.rows={};cls.proofs={};cls.rejected={}
        for slot,role in [('parent','sham'),('parent','ancestor_value_control'),
                          ('child','sham'),('child','inherited_source_control')]:
            key=slot+':'+role
            row=wrapper.history(cls.natural,slot,role,PROVENANCE)
            cls.rows[key]=row;cls.proofs[key]=referee.audit(row,PROVENANCE)

    def reject(self,name,row):
        original=copy.deepcopy(row)
        with self.assertRaises((AssertionError,KeyError)):
            referee.audit(row,PROVENANCE)
        self.assertEqual(row,original)
        self.rejected[name]=row

    def present(self):
        row=self.rows['parent:sham']
        # Missing neutral roots are retained, never replaced by a later winner.
        return row if row['branch'] is not None else None

    def test_actual_replay_and_scope(self):
        self.assertEqual(len(self.rows),4)
        for proof in self.proofs.values():
            self.assertTrue(proof['verified']);self.assertFalse(proof['scientific_admission'])
            self.assertFalse(proof['stage_credit'])
        self.assertEqual(self.natural['horizon'],512)
        self.assertTrue(self.natural['software_only'])

    def test_sham_or_empty_mask_exact_complete_natural(self):
        for row in self.rows.values():
            if row['branch'] is None:continue
            if row['role']=='sham' or not row['transition']['code_value_mask']:
                self.assertEqual(row['branch'],self.natural)

    def test_neutral_roster_and_null_denominator(self):
        edges=self.natural_proof['birth_edges']
        parent=next((edge for edge in edges if edge['generation']==2),None)
        child=next((edge for edge in edges if parent and edge['parent']==parent['child']),None)
        for kind,edge in [('parent',parent),('child',child)]:
            proof=self.proofs[kind+':sham']
            self.assertEqual(proof['null'],edge is None)
            if edge:self.assertEqual(proof['slot']['target'],edge['child'])

    def test_wrong_provenance_refused(self):
        row=copy.deepcopy(self.rows['parent:sham']);row['provenance']['source_sha256']='d'*64
        self.reject('provenance',row)

    def test_forged_original_draw_refused(self):
        original=self.present()
        if original is None:return
        row=copy.deepcopy(original);row['transition']['certificates'][0]['mutation_draw']^=1
        self.reject('draw',row)

    def test_rehashed_resource_and_prefix_refused(self):
        original=self.present()
        if original is None:return
        for defect in ('heat','prefix'):
            row=copy.deepcopy(original)
            if defect=='heat':row['branch']['final']['heat']+=1
            else:row['branch']['final']['events'][0]['decoded'][0]=31
            row['branch']['hash']=referee.h(row['branch']['final'])
            self.reject(defect,row)

    def test_dose_and_truncated_live_history_refused(self):
        original=self.present()
        if original is None:return
        row=copy.deepcopy(original);row['branch']['dose']=8 if self.natural['dose']==1 else 1
        self.reject('dose',row)
        if original['branch']['final']['entities']:
            row=copy.deepcopy(original);row['branch']['final']['events'].pop()
            row['branch']['final']['tick']-=1;row['branch']['hash']=referee.h(row['branch']['final'])
            self.reject('truncated-live',row)

    def test_undeclared_edit_rejected_as_natural(self):
        for row in self.rows.values():
            if row['branch'] is None or row['role']=='sham' or not row['transition']['code_value_mask']:continue
            with self.assertRaises(AssertionError):natural_referee.audit(row['branch'])


if __name__=='__main__':unittest.main()
