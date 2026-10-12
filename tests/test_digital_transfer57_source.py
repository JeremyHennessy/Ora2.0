import copy
import unittest
from experiments.digital_transfer57_source import enroll,sources


class Transfer57SourceTests(unittest.TestCase):
    def bank(self):
        return [dict(seed=55000+i,mode='mutating',child=1,program=[[0,0,0]]*9,performance=i) for i in range(12)]

    def birth(self):
        writes=[dict(write_id=i,index=i,tick=10,source_unit=i,source_value=0,value=0,unit=43+i,mutated=False) for i in range(27)]
        child=dict(id=1,parent=0,generation=1,code=[[0,43+i] for i in range(27)],energy=12,pos=1)
        row=dict(seed=55000,mode='mutating',hash='synthetic-not-full-VM',final=dict(events=[dict(actor=0,tick=10,writes=writes),dict(actor=0,tick=20,birth=dict(child=child,write_ids=list(range(27)),startup_energy=12))]))
        return row,dict(summary=dict(births=1))

    def test_input_order_does_not_change_enrollment(self):
        bank=self.bank();self.assertEqual(enroll(bank),enroll(list(reversed(bank))))

    def test_program_and_performance_do_not_change_identities(self):
        bank=self.bank();changed=copy.deepcopy(bank)
        for r in changed:r.update(program=[[31,31,31]]*9,performance=999999)
        self.assertEqual([(r['seed'],r['child']) for r in enroll(bank)],[(r['seed'],r['child']) for r in enroll(changed)])

    def test_duplicate_identity_refused(self):
        bank=self.bank();bank.append(bank[0])
        with self.assertRaises(AssertionError):enroll(bank)

    def test_invalid_source_and_insufficient_pool_refused(self):
        for change in ({'seed':55100},{'child':True},{'child':0},{'mode':'faithful'}):
            bank=self.bank();bank[0].update(change)
            with self.assertRaises(AssertionError):enroll(bank)
        with self.assertRaises(AssertionError):enroll(self.bank()[:7])

    def test_paid_birth_inventory(self):
        row,proof=self.birth();records=sources(row,proof)
        self.assertEqual((len(records),len(records[0]['paid_words']),records[0]['birth_position']),(1,27,1))

    def test_unpaid_birth_refused(self):
        row,proof=self.birth();row['final']['events'][1]['birth']['write_ids'][0]=999
        with self.assertRaises(AssertionError):sources(row,proof)

    def test_word_value_or_timing_mismatch_refused(self):
        for kind in ('value','tick'):
            row,proof=self.birth();row['final']['events'][0]['writes'][0][kind]=1 if kind=='value' else 20
            with self.assertRaises(AssertionError):sources(row,proof)

    def test_startup_and_generation_mismatch_refused(self):
        for kind in ('startup','generation'):
            row,proof=self.birth();birth=row['final']['events'][1]['birth']
            if kind=='startup':birth['startup_energy']=0
            else:birth['child']['generation']=2
            with self.assertRaises(AssertionError):sources(row,proof)
