import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from experiments import kinetic_dynamics as producer
from experiments import kinetic_dynamics_audit as audit


class KineticDynamicsTests(unittest.TestCase):
    def test_independent_development_replay_all_controls(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as tmp:
            for seed in (90000,90001):
                for arm in producer.ARMS:
                    folder=Path(tmp)/f'{seed}-{arm}'
                    producer.run_world(folder,seed,arm,128)
                    row=audit.world(folder)
                    self.assertEqual(row['steps'],128)
                    self.assertEqual(row['endpoint_count'],0)

    def test_raw_noise_forgery_rejects_without_trusting_hash(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as tmp:
            folder=Path(tmp)/'world';producer.run_world(folder,90000,'candidate',8)
            path=folder/'attempts.jsonl';rows=[json.loads(s) for s in path.read_text().splitlines()]
            rows[0][1][7]^=1;path.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'raw draw'):audit.world(folder)

    def test_final_accounting_forgery_rejects(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as tmp:
            folder=Path(tmp)/'world';producer.run_world(folder,90000,'candidate',8)
            path=folder/'final.json';state=json.loads(path.read_bytes());state['heat']+=1
            path.write_text(json.dumps(state),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'final state'):audit.world(folder)

    def test_energy_conserving_free_price_is_not_enough(self):
        model=audit.Interpreter(90000,'candidate');model.s['heat']+=1;model.s['photons'][0]-=1
        model.conserve()
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as tmp:
            folder=Path(tmp)/'world';producer.run_world(folder,90000,'candidate',8)
            path=folder/'initial.json';raw=json.loads(path.read_bytes());raw['state']['heat']+=1;raw['state']['photons'][0]-=1
            path.write_text(json.dumps(raw),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'initial'):audit.world(folder)

    def test_retained_copy_and_wrong_reconstructed_actor_cannot_count(self):
        model=audit.Interpreter(90000,'candidate')
        model.s['bits']=[0]*96
        first=model.associate(0,1,[0,1],4096,None)[3]
        model.measure(4096,['associate',0,1,first,None,[0,1]])
        model.tracks['00']['first_use']=[4097,first,999]
        second=model.associate(2,3,[2,3],4098,None)[3]
        site=model.s['active'].pop(str(first));children=[model.birth([0],[first],4099,site,False),model.birth([1],[first],4099,site,False)]
        model.measure(4099,['cleave',first,1,children]);self.assertNotIn('loss',model.tracks['00'])
        model.tracks['00'].update(loss=[4100,second],reconstruction=[4101,first,999])
        model.measure(4102,['associate',4,5,second,second,[4,5]])
        self.assertEqual(model.endpoints,{})

    def test_exact_paired_gate_counts_ties_and_all_samples(self):
        audits=[]
        for block in range(4):
            rows=[dict(seed=s,arm=arm,endpoint_count=int(arm=='candidate' and s<43008)) for s in range(43000+8*block,43008+8*block) for arm in audit.ARMS]
            audits.append(dict(batch=block,rows=rows))
        d=audit.decision(audits);self.assertEqual((d['wins'],d['ties']),(8,24));self.assertTrue(d['positive_gate'])
        changed=copy.deepcopy(audits);changed[0]['rows'][0]['endpoint_count']=0
        self.assertFalse(audit.decision(changed)['positive_gate'])

    def test_authored_paid_lifecycle_detected_and_assistance_excluded(self):
        for assisted in (False,True):
            model=audit.Interpreter(90000,'candidate');model.s['bits']=[0]*96;model.s['bits'][1]=1
            e=model.associate(0,1,[0,1],4096,None,assisted);first=e[3];model.measure(4096,e)
            e=model.associate(2,3,[2,3],4097,first);helper=e[3];model.measure(4097,e)
            site=model.s['active'].pop(str(first));obj=model.s['objects'][str(first)]
            children=[model.birth([atom],[first],4098,site,obj['assisted']) for atom in (0,1)]
            model.s['heat']+=1;model.measure(4098,['cleave',first,1,children])
            e=model.associate(*children,[4,5],4099,helper);rebuilt=e[3];model.measure(4099,e)
            e=model.associate(4,5,[6,7],4100,rebuilt);model.measure(4100,e);model.conserve()
            self.assertEqual(set(model.endpoints),set() if assisted else {'01'})
