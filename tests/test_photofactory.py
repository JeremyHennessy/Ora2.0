import copy
import unittest
from experiments.photofactory import experiment
from experiments.photofactory_audit import audit


class PhotofactoryTests(unittest.TestCase):
    def test_complete_renewal_and_dominance(self):
        result=audit(experiment())
        self.assertEqual(result['decision'],'REJECT_BEFORE_NATURAL_WORLDS')
        self.assertEqual(result['results']['candidate']['formed_devices'],15)
        self.assertEqual(result['results']['candidate']['payback'],324)
        self.assertEqual(result['results']['stationary']['payback'],352)

    def test_reject_corrupted_energy_material_function_and_accounting(self):
        original=experiment()
        for fault in ('energy','material','upkeep','release','fresh','score','admission','shuffle'):
            data=copy.deepcopy(original); events=data['runs'][0]['events']
            if fault=='energy':
                ev=next(e for e in events if e['op']=='load');ev['inputs'][1]=ev['inputs'][0]
            elif fault=='material':
                ev=next(e for e in events if e['op']=='fabricate');ev['material']=[0,1]
            elif fault=='upkeep':events.remove(next(e for e in events if e['op']=='upkeep'))
            elif fault=='release':events.remove(next(e for e in events if e['op']=='release'))
            elif fault=='fresh':
                ev=next(e for e in events if e['op']=='load' and e['phase']==1)
                ev['inputs'][0]=next(e for e in events if e['op']=='load')['inputs'][0]
            elif fault=='score':data['runs'][0]['payback']+=1
            elif fault=='admission':data['mechanism_admitted']=True
            elif fault=='shuffle':data['shuffle_cases'].pop()
            with self.subTest(fault=fault),self.assertRaises((AssertionError,KeyError)):
                audit(data)
