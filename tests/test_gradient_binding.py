import json
import os
from pathlib import Path
import tempfile
import unittest
from experiments import gradient_binding as law
from experiments import gradient_binding_audit as audit
from experiments.gradient_binding_budget import Fixture, feasibility


class GradientTests(unittest.TestCase):
    def test_authored_renewal_budget_and_depth_limit(self):
        result=feasibility()
        self.assertEqual(result['shallow_required_photons'],52)
        self.assertEqual(len(result['shallow']['endpoints']),1)
        self.assertEqual(result['deep_minimum_photons'],316)
        self.assertEqual(result['inaccessible_photons'],1792)
        self.assertEqual(result['natural_worlds_executed'],0)

    def test_all_arms_independent_noise_accounting_and_replay(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as tmp:
            for seed in (91000,91001):
                for arm in law.ARMS:
                    path=Path(tmp)/f'{seed}-{arm}';replay=Path(tmp)/f'{seed}-{arm}-replay'
                    law.world(path,seed,arm,256);law.world(replay,seed,arm,256)
                    result=audit.world(path)
                    self.assertEqual(result['steps'],256)
                    for name in ('initial.json','attempts.jsonl','final.json'):self.assertEqual((path/name).read_bytes(),(replay/name).read_bytes())

    def test_duplicate_payment_is_atomic_noop(self):
        f=Fixture();f.fill(0,2)
        for request in (['capture',0,[2,2]],['bind',[0,1],0,[0,0]]):
            before=law.canon(f.model.snapshot());self.assertEqual(f.perform(request),['noop']);self.assertEqual(law.canon(f.model.snapshot()),before)
        bond=f.bind(0,1);f.fill(0,2);p=f.model.q[0][0]
        before=law.canon(f.model.snapshot());self.assertEqual(f.perform(['transport',bond,0,1,[p,p]]),['noop']);self.assertEqual(law.canon(f.model.snapshot()),before)

    def test_nonendpoint_payer_cannot_buy_remote_link(self):
        f=Fixture();f.fill(0,2);before=law.canon(f.model.snapshot())
        self.assertEqual(f.perform(['bind',[1,2],0,f.model.q[0][:2]]),['noop']);self.assertEqual(law.canon(f.model.snapshot()),before)

    def test_capacity_and_no_capture_at_nonlocal_source(self):
        f=Fixture();f.fill(0,8);before=law.canon(f.model.snapshot())
        self.assertEqual(f.perform(['capture',0,f.model.photons[0][:2]]),['noop']);self.assertEqual(law.canon(f.model.snapshot()),before)
        self.assertEqual(f.perform(['capture',1,[0,1]]),['noop'])

    def test_assisted_route_remains_assisted(self):
        f=Fixture();bond=f.perform(['external',[0,1],f.model.external[:4]])[1];f.fill(0,4)
        for _ in range(2):f.perform(['transport',bond,0,1,f.model.q[0][:2]])
        child=f.perform(['bind',[1,2],1,f.model.q[1][:2]])[1]
        self.assertTrue(f.model.bonds[child]['assisted']);self.assertNotIn('1:2',f.check.tracks)
        self.assertEqual(len(f.model.external),124)

    def test_pre_loss_buffer_is_not_reconstruction_endpoint(self):
        f=Fixture();f.bind(0,1);origin=f.bind(1,2);f.bind(2,3)
        f.fill(1,2);f.perform(['unbind',origin])
        f.perform(['bind',[1,2],1,f.model.q[1][:2]]);f.bind(2,10)
        self.assertEqual(f.check.endpoints,{})

    def test_withdrawal_exports_no_energy_refund(self):
        model=law.Surface(91001,'withdrawal');check=audit.Interpreter(91001,'withdrawal')
        output=model.step(8192,[0]*8)
        self.assertEqual(len(output[0]),2048);self.assertEqual(model.heat,0);self.assertEqual(sum(map(len,model.q.values())),0)
        check.s['exported']=list(range(2048));check.s['photons']={i:[] for i in range(64)};check.conserve()
        self.assertEqual(law.canon(model.snapshot()),audit.canon(check.snapshot()))

    def test_noise_and_ancestry_forgery_rejected(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as tmp:
            path=Path(tmp)/'world';law.world(path,91000,'candidate',256)
            tape=path/'attempts.jsonl';raw=tape.read_bytes();lines=raw.splitlines();row=json.loads(lines[0]);row[1][7]^=1;lines[0]=audit.canon(row).encode();tape.write_bytes(b'\n'.join(lines)+b'\n')
            with self.assertRaisesRegex(ValueError,'transition'):audit.world(path)
            tape.write_bytes(raw);final=path/'final.json';state=json.loads(final.read_bytes());state['heat']+=1;law.save(final,state)
            with self.assertRaisesRegex(ValueError,'ledger'):audit.world(path)

    def test_complete_paired_denominator_and_sign_test(self):
        reports=[dict(batch=i,rows=[dict(seed=s,arm=a,endpoint_count=int(a=='candidate'),distal_paid_bonds=int(a=='free-transport')) for s in range(53000+8*i,53008+8*i) for a in audit.ARMS]) for i in range(4)]
        result=audit.decision(reports);self.assertTrue(result['positive_gate']);self.assertEqual(result['sign_test']['p'],2**-32);self.assertTrue(result['bound_network_necessity_rejected'])
        reports[0]['rows'].pop()
        with self.assertRaisesRegex(ValueError,'samples'):audit.decision(reports)


if __name__=='__main__':unittest.main()
