"""Authored partial raw tables and mocked integrity ordering; never World histories."""
import copy,json,unittest
from unittest.mock import patch
from experiments.digital_informative_exposure23_interpret import body,clone,h
from experiments import digital_diagnosis59 as contract
from experiments.digital_diagnosis59_project import project as chronological
from experiments.digital_diagnosis59_project_independent import project as joined

SELECTED=(chronological,joined);SEMANTICS={}


def table(steps):
    """Prepared event-table fabricator, NOT a lawful scheduler/PC/generic VM witness."""
    triples=[]
    for i,op,a,b,extra in steps:
        if [op,a,b] not in triples:triples.append([op,a,b])
    assert len(triples)<=9
    triples += [[18,0,0] for _ in range(9-len(triples))]
    values=sum(triples,[]);states={0:body(0,None,0,[[v,i] for i,v in enumerate(values)],list(range(27,43)),0)}
    occupied=set(range(43));food={p:[0 if p<32 else 1+(p-32)//16,0] for p in range(64)};events=[];wid=0
    for offset,(i,op,a,b,extra) in enumerate(steps):
        t=offset+1;s=states[i];assert [c[0] for c in s['code'][s['pc']*3:s['pc']*3+3]]==[op,a,b]
        e=dict(tick=t,actor=i,decoded=[op,a,b],before=h(s));s['energy']-=1;r=s['registers']
        if op==4:r[a%2]=b%16
        if op==0:r[a%2]=s['pos'];s['cue']=s['pos']
        if op==1:r[a%2]=s['feedback']
        if op==2:r[a%2]=s['memory'][b%8]
        if op==3:s['memory'][a%8]=r[b%2]
        if op==5:r[a%2]^=r[b%2]
        if op==6:
            local=sorted(p for p in food if food[p][0]==s['pos'] and (not 16<=p<32 or t>=64))
            s['feedback']=int(bool(local) and extra.get('success',True))
            if local:
                p=local[0];e['attempt']=dict(packet=p,position=s['pos'],cue=0,port=r[a%2]%2,target=r[a%2]%2 if s['feedback'] else 1-r[a%2]%2,success=s['feedback'])
                if s['feedback']:del food[p];s['energy']=min(64,s['energy']+20)
            e['feedback']=s['feedback']
        if op==9:
            index=b%27;old=s['code'][index][0];s['code'][index][0]=r[a%2]
            e['self_write']=dict(index=index,unit=s['code'][index][1],old=old,value=r[a%2])
        if op==10:
            records=[]
            for index in range(len(s['nursery']),len(s['nursery'])+3):
                unit=min(set(range(512))-occupied);occupied.add(unit);value,source_unit=s['code'][index]
                w=dict(unit=unit,value=value,index=index,tick=t,source_unit=source_unit,source_value=value,write_id=wid,mutated=False)
                wid+=1;records.append(w);s['nursery'].append(clone(w))
            s['energy']-=3;e['writes']=records
        if op==12:
            units=sorted(set(range(512))-occupied)[:16];occupied.update(units);cid=len(states)
            child=body(cid,i,s['generation']+1,[[w['value'],w['unit']] for w in s['nursery']],units,s['pos'])
            e['birth']=dict(child=clone(child),write_ids=[w['write_id'] for w in s['nursery']],state_formation=[dict(unit=u,value=0,energy=1) for u in units],release_energy=2,startup_energy=12)
            states[cid]=child;s['nursery']=[];s['energy']-=30
        if op==13:s['pos']=(s['pos']+(1 if r[a%2]%2 else -1))%4
        if op==14 and extra.get('recipient') is not None:
            who=extra['recipient'];states[who]['inbox']=r[a%2];e['message']=dict(recipient=who,value=r[a%2])
        if op==15 and s['inbox'] is not None:r[a%2]=s['inbox'];s['inbox']=None
        if op==17:s['energy']=0
        if s['energy']==0:
            released=[c[1] for c in s['code']]+s['state_units']+[w['unit'] for w in s['nursery']]
            occupied.difference_update(released);e['death']=released;del states[i]
        else:
            future=next((x for x in steps[offset+1:] if x[0]==i),None)
            s['pc']=triples.index(list(future[1:4])) if future else 0;e['after']=clone(s)
        events.append(e)
    return dict(seed=58000,mode='faithful',genesis_program=triples,final=dict(events=events,free=sorted(set(range(512))-occupied),food=food))


def step(op,a=0,b=0,actor=0,**extra):return (actor,op,a,b,extra)
def reproduction():return [step(6)]*3+[step(10)]*9+[step(6),step(12)]


class Diagnosis59Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trap=patch('experiments.digital_informative_exposure23.World.__init__',side_effect=AssertionError('World forbidden'));cls.trap.start()
        with open('docs/DIGITAL-TRANSFER-57-SOURCE.json',encoding='utf-8') as f:cls.manifest=json.load(f)['summary']

    @classmethod
    def tearDownClass(cls):
        cls.trap.stop();print('\nSEMANTICS:'+json.dumps(SEMANTICS,sort_keys=True,separators=(',',':')),flush=True)

    def check(self,row):
        results=[f(copy.deepcopy(row)) for f in SELECTED]
        if len(results)>1:self.assertEqual(results[0],results[1])
        SEMANTICS.setdefault(self._testMethodName,[]).append(results[0]);return results[0]

    def refuse(self,row):
        for f in SELECTED:
            with self.assertRaises((AssertionError,KeyError,IndexError)):f(copy.deepcopy(row))
        SEMANTICS.setdefault(self._testMethodName,[]).append('REFUSED')

    def summaries(self):
        summaries=[]
        for source in (None,)+contract.ROSTER:
            record=None
            if source is not None:
                r=self.manifest['roster'][contract.ROSTER.index(source)];record={k:r[k] for k in ('seed','child','program_hash','source_row_hash')}
            for seed in range(58000,58016):
                summaries.append(dict(verified=True,identity=dict(seed=seed,arm='withheld' if source is None else 'retained',source=record),source_manifest_hash=contract.SOURCE_HASH,stage_credit=False,
                    raw_hash='a'*64,semantic_hash='b'*64,summary=dict(ticks=0,actors=1,births=0,deaths=0,food=0,copy_words=0,free_material=469,live_energy=12)))
        return summaries

    def test_01_complete_panel(self):
        r=contract.panel(self.summaries(),self.manifest);self.assertEqual(r['histories'],144);SEMANTICS[self._testMethodName]=r

    def test_02_duplicate_panel(self):
        rows=self.summaries();rows[-1]=rows[0]
        with self.assertRaises(AssertionError):contract.panel(rows,self.manifest)
        SEMANTICS[self._testMethodName]='REFUSED'

    def test_03_missing_panel(self):
        with self.assertRaises(AssertionError):contract.panel(self.summaries()[:-1],self.manifest)
        SEMANTICS[self._testMethodName]='REFUSED'

    def test_04_zero_action_actor(self):
        r=self.check(table([]));self.assertEqual(r['actors']['0']['instructions'],0)

    def test_05_death_denominator(self):
        r=self.check(table([step(17)]));self.assertEqual(r['summary']['deaths'],1)

    def test_06_paid_birth_startup(self):
        r=self.check(table(reproduction()));self.assertEqual(r['summary']['copy_words'],27);self.assertEqual(r['edges'][0]['startup_energy'],12)

    def test_07_exact_birth_and_division(self):
        r=self.check(table(reproduction()));self.assertTrue(r['edges'][0]['equal_parent_birth']);self.assertTrue(r['edges'][0]['equal_parent_division'])
        route=[step(6)]*3+[step(10)]*9+[step(4,b=1),step(9,b=26),step(6),step(12)]
        r=self.check(table(route));self.assertTrue(r['edges'][0]['equal_parent_birth']);self.assertFalse(r['edges'][0]['equal_parent_division'])

    def test_08_write_before_tail_copy(self):
        route=[step(6)]*3+[step(10)]*4+[step(4,b=1),step(9,b=26)]+[step(10)]*5+[step(6),step(12)]
        r=self.check(table(route));self.assertFalse(r['edges'][0]['equal_parent_birth']);self.assertTrue(r['edges'][0]['equal_parent_division'])

    def test_09_noop_and_changed_writes(self):
        r=self.check(table([step(4,b=1),step(9,b=26),step(9,b=26)]));self.assertEqual([w['changed'] for w in r['actors']['0']['self_writes']],[True,False])

    def test_10_parent_after_birth_excluded(self):
        r=self.check(table(reproduction()+[step(6)]));self.assertEqual(sum(map(len,r['edges'][0]['parent_prior_food'])),4);self.assertEqual(sum(map(len,r['actors']['0']['food_ticks_by_site'])),5)

    def test_11_child_after_birth_only(self):
        r=self.check(table(reproduction()+[step(6,actor=1)]));self.assertEqual(r['edges'][0]['child_later_food'][0],[15])

    def test_12_zero_action_newborn_censor(self):
        r=self.check(table(reproduction()));self.assertTrue(r['actors']['1']['alive']);self.assertEqual(r['actors']['1']['instructions'],0)

    def test_13_empty_action(self):
        r=self.check(table([step(13),step(6)]));self.assertEqual(r['actors']['0']['empty_action_ticks'],[2])

    def test_14_paid_failed_action(self):
        r=self.check(table([step(6,success=False)]));self.assertEqual(r['actors']['0']['personal_trial_ticks'],[1]);self.assertEqual(r['summary']['food'],0)

    def test_15_acquired_packet_removal(self):
        r=self.check(table([step(6),step(6)]));self.assertEqual([f['attempt']['packet'] for f in r['frames']],[0,1])

    def test_16_repeated_unsuccessful_packet(self):
        r=self.check(table([step(6,success=False),step(6,success=False)]));self.assertEqual([f['attempt']['packet'] for f in r['frames']],[0,0])

    def test_17_latest_empty_overwrite(self):
        r=self.check(table([step(6),step(13),step(6),step(1)]));self.assertEqual(r['origins']['records'][-1]['read'],[])

    def test_18_older_register_origin(self):
        r=self.check(table([step(6),step(1),step(6)]));self.assertEqual(r['origins']['actors']['0']['registers'][0],[[0,1]])

    def test_19_memory_retention(self):
        r=self.check(table([step(6),step(1),step(3),step(4),step(2)]));self.assertEqual(r['origins']['actors']['0']['registers'][0],[[0,1]])

    def test_20_code_origin(self):
        r=self.check(table([step(6),step(1),step(9,b=26)]));self.assertEqual(r['origins']['actors']['0']['code'][26],[[0,1]])

    def test_21_pc_dependency_unknown(self):
        r=self.check(table([step(6),step(1),step(8)]));self.assertEqual(r['origins']['causal_effect'],'UNKNOWN');self.assertEqual(r['origins']['actors']['0']['pc'],[[0,1]])

    def test_22_inbox_origin_and_birth_reset(self):
        r=self.check(table(reproduction()+[step(1),step(14,recipient=1),step(6,actor=1),step(15,actor=1)]))
        self.assertIsNone(r['origins']['actors']['1']['inbox']);self.assertEqual(r['origins']['actors']['1']['registers'][0],[[0,13]])

    def test_23_duplicate_copy_and_before_hash_refused(self):
        row=table(reproduction());row['final']['events'][4]['writes'][0]['write_id']=0;self.refuse(row)
        row=table([step(6)]);row['final']['events'][0]['before']='wrong';self.refuse(row)

    def test_24_full_vm_before_projection_and_reserved_refusal(self):
        envelope=dict(version='DIGITAL-REPLICATION-58-assisted-v1',source_manifest_hash=contract.SOURCE_HASH,arm='withheld',source=None,history=dict(seed=58000,mode='faithful',genesis_program=contract.REFERENCE))
        with patch.object(contract,'audit',side_effect=AssertionError('raw integrity')),patch.object(contract,'chronological',side_effect=RuntimeError('too early')) as p:
            with self.assertRaises(AssertionError):contract.interpret(envelope,self.manifest)
            p.assert_not_called()
        envelope['history']['seed']=58100
        with patch.object(contract,'audit',side_effect=RuntimeError('reserve reached')) as p:
            with self.assertRaises(AssertionError):contract.interpret(envelope,self.manifest)
            p.assert_not_called()
        SEMANTICS[self._testMethodName]='VM_FIRST_RESERVE_REFUSED'


if __name__=='__main__':
    import sys
    if len(sys.argv)==2:SELECTED=(chronological,) if sys.argv.pop()=='chronological' else (joined,)
    unittest.main()
