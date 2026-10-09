import copy
import unittest
from experiments import renewal_opportunity as worker
from experiments import renewal_opportunity_audit as audit
from experiments import startup_unscreened as base

class RenewalTests(unittest.TestCase):
    def test_fresh_scope_and_all_control_interpretations(self):
        self.assertEqual(len(audit.configurations()),224)
        self.assertEqual({c['seed'] for c in audit.configurations()},set(range(41000,41032)))
        for mode in base.MODES:
            r=worker.simulate(41000,mode)
            self.assertEqual(audit.verify(r),r['diagnosis'])
            self.assertEqual({k:r[k] for k in ('config','initial','events','terminal')},base.simulate(41000,mode))
        self.assertNotEqual(audit.configurations(),audit.physics.configurations())

    def test_formulas_against_explicit_finite_enumeration_authored_bookkeeping_fixture(self):
        # An artificial bookkeeping state tests formulas; not an observed origin/path.
        s,_=base.initial(41000,'active')
        for tick,q in enumerate(([0,0,0,0,0,0],[2,0,0,0,0,0],[0,1,1,0,0,0],[3,1,0,0,0,0],[0,1,2,0,0,0],[4,0,0,0,0,0],[0,2,3,0,0,0],[0,3,4,0,0,0],[2,2,0,0,0,0],[0,4,5,0,0,0])):
            base.step(s,'active',tick,q)
        s['units']['E0']['origin']=s['units']['E1']['origin']='capture'
        for u,v in s['units'].items():
            if v['origin'] in ('activation','recharge'): v['parents']=['E0','E1']
        for p in s['products'].values():
            for u in p['work']: s['units'][u]['origin']='capture'
        audit.physics.validate(s)
        for mode in ('active','external','topup_off','food_withdrawn','association_off'):
            values=worker.measure(s,mode,128)
            self.assertEqual(values,audit.opportunities(s,mode,128))
            starts=extensions=releases=empty=partial=0
            for a in s['free']:
                if mode!='association_off' and s['potential'][a] and audit.paid(s,s['potential'][a][0]): starts+=1
            for c in s['chains'].values():
                for a in s['free']:
                    if len(s['potential'][a])==3 and all(audit.paid(s,u) for u in c['debits']+s['potential'][a]): extensions+=1
                residual=[u for a in c['atoms'] for u in s['potential'][a]]
                if len(c['atoms'])>=2 and len(residual)>=3 and all(audit.paid(s,u) for u in c['debits']+residual[:3]): releases+=1
            if mode not in ('external','food_withdrawn'):
                accessible=s['free']+[a for c in s['chains'].values() for a in c['atoms']]
                for a in accessible:
                    for p in s['products'].values():
                        for f in s['food']:
                            if len(p['atoms'])>=2 and len(p['work'])>=2 and all(s['units'][u]['origin']=='capture' for u in p['work'][:2]) and s['atoms'][f]['bit']!=s['atoms'][p['atoms'][-1]]['bit']:
                                empty+=int(len(s['potential'][a])==0)
                                partial+=int(mode!='topup_off' and len(s['potential'][a]) in (1,2))
            for k,v in dict(clean_starts=starts,clean_extensions=extensions,clean_releases=releases,capture_empty_requests=empty,capture_partial_requests=partial).items(): self.assertEqual(values[k],v)

    def test_external_construction_ancestry_cannot_be_erased_by_later_charge(self):
        s,_=base.initial(41000,'active')
        base.step(s,'active',0,[0,0,0,0,0,0]); base.step(s,'active',1,[2,0,0,0,0,0])
        self.assertEqual(worker.measure(s,'active',128)['clean_chains'],0)
        self.assertEqual(audit.opportunities(s,'active',128)['clean_chains'],0)
        debit=s['chains']['C1']['debits'][0]
        self.assertEqual(s['units'][debit]['actor'],'environment')
        self.assertFalse(audit.paid(s,debit))

    def test_opportunity_funding_boolean_noise_and_diagnosis_forgeries(self):
        r=worker.simulate(41000,'active')
        for kind in ('opportunity','funding','boolean','noise','denominator'):
            bad=copy.deepcopy(r)
            if kind=='opportunity': bad['observations'][128]['opportunities']['clean_starts']+=1
            elif kind=='funding': bad['terminal']['units']['E0']['origin']='capture'
            elif kind=='boolean': bad['observations'][0]['opportunities']['clean_starts']=False
            elif kind=='noise': bad['events'][0]['draw'][1]^=1
            else: bad['diagnosis']['worlds']=2
            with self.subTest(kind=kind),self.assertRaises(ValueError): audit.verify(bad)

if __name__=='__main__': unittest.main()
