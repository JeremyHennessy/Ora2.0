"""Authored partial tables/joins only; no World or hidden-context query."""
import copy,types,sys,unittest
from unittest.mock import patch
from experiments import digital_renewable65 as m
from experiments import digital_renewable65_runner as runner


def summary(seed=66000,mode='faithful'):
    return dict(verified=True,seed=seed,mode=mode,fuel_mode='renewed',route='ancestor',formation_cost=43,
                genesis_program_hash=m.full.h(m.ANCESTOR),mutations=0 if mode=='faithful' else 3,
                turnover=dict(founder_expiry_tick=853,post_founder_instructions=3243,births=19,
                              maximum_generation=5,post_founder_paid_personal_births=12,
                              post_founder_renewed_food=400,paid_personal_chains=[[1,2,4]],living_descendants=7),births=19)


def proof(seed,mode):
    return dict(verified=True,summary=summary(seed,mode),projection=dict(primary_endpoint=12+(mode=='mutating'),
                secondary_endpoint=400+20*(mode=='mutating'),underexposed=False if mode=='mutating' else None,
                neutral_source_slot=None,actors={}),ordinary_gate=True if mode=='faithful' else None,
                history_hash='prepared-stub',stage_credit=False)


def partial(events,food=0,deaths=0):
    s=dict(verified=True,ticks=len(events),births=0,deaths=deaths,successful_food=food,
           turns={'0':len(events)},turnover=dict(founder_expiry_tick=None,post_founder_paid_personal_births=0,
           post_founder_renewed_food=0,maximum_generation=0))
    return dict(mode='faithful',final=dict(events=events,food={})),s


class Prepared(unittest.TestCase):
    def test_ordinary_complete_even_first_false(self):
        values=[summary(seed) for seed in m.SEEDS];values[0]['births']=11
        with patch.object(m,'ordinary_gate',wraps=m.ordinary_gate) as gate:
            self.assertFalse(m.ordinary_admission(values));self.assertEqual(gate.call_count,16)

    def test_membership_mode_source_and_threshold_refusals(self):
        for key,value in [('seed',66100),('seed',True),('mode','mutating'),('formation_cost',42),('genesis_program_hash','wrong')]:
            s=summary();s[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(AssertionError):m.ordinary_gate(s)
        for key,value in [('founder_expiry_tick',None),('post_founder_instructions',127),('maximum_generation',2),('paid_personal_chains',[]),('living_descendants',0)]:
            s=summary();s['turnover'][key]=value;self.assertFalse(m.ordinary_gate(s))

    def test_duplicate_missing_reference_refused(self):
        for rows in [[summary(s) for s in m.SEEDS[:-1]],[summary(m.SEEDS[0]) for _ in m.SEEDS]]:
            with self.assertRaises(AssertionError):m.ordinary_admission(rows)

    def test_complete_banks_and_null_source_slots(self):
        result=m.cohort([proof(s,a) for s in m.SEEDS for a in ('faithful','mutating')])
        self.assertTrue(result['operator_advantage']);self.assertEqual(len(result['neutral_source_slots']),16)
        self.assertTrue(all(s['slot'] is None for s in result['neutral_source_slots']))
        self.assertFalse(result['selection']);self.assertFalse(result['stage_credit'])

    def test_unseen_failure_not_rescued_by_primary(self):
        rows=[proof(s,a) for s in m.SEEDS for a in ('faithful','mutating')]
        for p in rows:
            if p['summary']['seed'] in (66206,66207) and p['summary']['mode']=='mutating':p['projection']['primary_endpoint']=12
        r=m.cohort(rows);self.assertTrue(r['banks']['primary']['passed']);self.assertFalse(r['banks']['unseen']['passed']);self.assertFalse(r['operator_advantage'])

    def test_complete_cohort_identity_refusals(self):
        rows=[proof(s,a) for s in m.SEEDS for a in ('faithful','mutating')]
        for bad in [rows[:-1],rows[:-1]+[copy.deepcopy(rows[0])]]:
            with self.assertRaises(AssertionError):m.cohort(bad)

    def test_negative_live_or_no_mutation_rejects_advantage(self):
        for field in ('live','mutation'):
            rows=[proof(s,a) for s in m.SEEDS for a in ('faithful','mutating')]
            p=next(p for p in rows if p['summary']['seed']==66000 and p['summary']['mode']=='mutating')
            if field=='live':p['summary']['turnover']['living_descendants']=6
            else:p['summary']['mutations']=0
            self.assertFalse(m.cohort(rows)['operator_advantage'])

    def test_full_audit_failure_before_projection(self):
        row=dict(seed=66000,mode='faithful',fuel_mode='renewed',route='ancestor',genesis_program=[m.ANCESTOR[i:i+3] for i in range(0,27,3)])
        with patch.object(m.full,'audit',side_effect=AssertionError('invalid full VM')),patch.object(m,'_project_audited') as projection:
            with self.assertRaises(AssertionError):m.audit_row(row)
            projection.assert_not_called()

    def test_generator_source_and_membership_without_world(self):
        calls=[];stub=types.SimpleNamespace(PROGRAMS={'ancestor':[m.ANCESTOR[i:i+3] for i in range(0,27,3)]},history=lambda *a:calls.append(a) or 'stub')
        import experiments
        with patch.dict(sys.modules,{'experiments.digital_renewable64':stub}),patch.object(experiments,'digital_renewable64',stub,create=True):
            self.assertEqual(m.generate(66000,'mutating'),'stub');self.assertEqual(calls,[(66000,'ancestor','mutating','renewed')])
            for seed,mode in [(66100,'faithful'),(True,'faithful'),(66000,'copy_disabled')]:
                with self.assertRaises(AssertionError):m.generate(seed,mode)
            stub.PROGRAMS={'ancestor':[[18,0,0]]}
            with self.assertRaises(AssertionError):m.generate(66000,'faithful')
        self.assertEqual(len(calls),1)

    def test_partial_cap_loss_join_and_faithful_exposure(self):
        events=[dict(actor=0,tick=i,decoded=[6,0,0],outcome='executed',attempt=dict(success=1),after=dict(energy=energy,code=[[v,j] for j,v in enumerate(m.ANCESTOR)])) for i,energy in enumerate((31,50,64),1)]
        row,s=partial(events,food=3);r=m._project_audited(row,s)
        self.assertEqual(r['cap_loss_energy'],5);self.assertIsNone(r['underexposed'])

    def test_partial_terminal_selfwrite_not_lost(self):
        events=[dict(actor=0,tick=i,decoded=[18,0,0],outcome='executed',after=dict(energy=12-i,code=[[v,j] for j,v in enumerate(m.ANCESTOR)])) for i in range(1,12)]
        events.append(dict(actor=0,tick=12,decoded=[9,0,0],outcome='executed',self_write=dict(index=0,value=3),death=[]))
        row,s=partial(events,deaths=1);r=m._project_audited(row,s);changed=list(m.ANCESTOR);changed[0]=3
        self.assertEqual(r['actors'][0]['program_at_end_hash'],m.full.h(changed));self.assertFalse(r['actors'][0]['censored'])

    def test_partial_transfer_and_temporal_copy_source_join(self):
        old=list(m.ANCESTOR);newborn=list(old);newborn[0]=5;later=list(old);later[1]=2
        cells=lambda values:[[v,i] for i,v in enumerate(values)]
        writes=[dict(write_id=i,source_value=v,value=newborn[i],mutated=v!=newborn[i],index=i,unit=43+i) for i,v in enumerate(old)]
        events=[dict(actor=0,tick=1,decoded=[10,0,0],outcome='executed',writes=writes,after=dict(energy=11,code=cells(old))),
                dict(actor=0,tick=2,decoded=[9,0,0],outcome='executed',self_write=dict(index=1,value=2),after=dict(energy=10,code=cells(later))),
                dict(actor=0,tick=3,decoded=[12,0,0],outcome='executed',birth=dict(child=dict(id=1,generation=1,energy=12,code=cells(newborn)),write_ids=list(range(27)),startup_energy=12,release_energy=2),after=dict(energy=9,code=cells(later))),
                dict(actor=0,tick=4,decoded=[16,0,0],outcome='executed',transfer=1,after=dict(energy=7,code=cells(later))),
                dict(actor=1,tick=5,decoded=[6,0,0],outcome='executed',attempt=dict(success=1),after=dict(energy=32,code=cells(newborn)))]
        row,s=partial(events,food=1);row['mode']='mutating';s['births']=1;s['turns']={'0':4,'1':1};s['turnover']['maximum_generation']=1
        r=m._project_audited(row,s);b=r['neutral_source_slot']
        self.assertEqual(r['cap_loss_energy'],0);self.assertEqual(r['changed_paid_newborns'],1)
        self.assertEqual(b['temporally_copied_source_program'],old);self.assertEqual(b['parent_program_at_division'],later)
        self.assertEqual(b['newborn_program'],newborn);self.assertEqual(r['actors'][1]['food'],1)

    def test_ordering_success_all_reference_then_durable_admission(self):
        calls=[];saved=[]
        def run(location,seed,mode):
            if mode=='mutating':self.assertEqual(len(saved),1);self.assertEqual(sum(a=='faithful' for _,_,a in calls),32)
            calls.append((location,seed,mode));return proof(seed,mode)
        r=runner.panel(run,lambda receipt:saved.append(copy.deepcopy(receipt)))
        self.assertEqual(len(calls),64);self.assertEqual(saved[0]['mutating_world_calls'],0);self.assertEqual(r['original_roles'],32)

    def test_reference_failure_completes_both_exports_no_treatment(self):
        calls=[];saved=[]
        def run(location,seed,mode):
            self.assertEqual(mode,'faithful');calls.append((location,seed,mode));p=proof(seed,mode)
            if seed==66000:p['summary']['births']=11
            return p
        r=runner.panel(run,lambda receipt:saved.append(receipt));self.assertEqual(len(calls),32)
        self.assertFalse(saved[0]['admitted']);self.assertIsNone(r['comparison'])

    def test_replay_mismatch_or_failed_durable_save_no_treatment(self):
        for mismatch in (True,False):
            calls=[]
            def run(location,seed,mode):
                self.assertEqual(mode,'faithful');calls.append((location,seed));p=proof(seed,mode)
                if mismatch and location=='restored' and seed==66000:p['history_hash']='mismatch'
                return p
            def save(receipt):raise AssertionError('durable save failed')
            with self.assertRaises(AssertionError):runner.panel(run,save)
            self.assertEqual(len(calls),32)


if __name__=='__main__':unittest.main()
