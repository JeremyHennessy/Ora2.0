"""NON-PHYSICS custody dependency/early-admission tests, zero Worlds/labels."""
import copy
import unittest
import tempfile
import pathlib
from experiments.digital_revision84_child import CONFIG,PREPARED,scope
from experiments.digital_revision84_plan import plan,pipeline,required_raw,M

def request(configuration,role,kind):
    return dict(configuration=copy.deepcopy(configuration),source_files={},source_sha='',config_sha='',
                role=role,kind=kind,input=None,grant={},seal='')

class Revision84ControllerTests(unittest.TestCase):
    def test_whole69_and21_roles_precharge_and_complete_dependency(self):
        self.assertEqual(len(plan(CONFIG))+4,69)
        self.assertEqual(len(plan(PREPARED))+4,21)
        self.assertLess(required_raw(CONFIG),3584*M)
        seen=[]
        def launch(role,inputs):
            if role=='original:interpret':self.assertEqual(len(inputs),16)
            elif role.endswith(':metrics'):
                self.assertEqual(set(inputs),{'recording','proof'})
                self.assertIn(':generate',inputs['recording']['path'])
                self.assertIn(':audit',inputs['proof']['path'])
            elif role.endswith(':audit'):self.assertIn(':generate',inputs['path'])
            seen.append(role)
            # Mock evidence descriptor, explicitly not physical receipts.
            return dict(path=role,extent=1,sha256=role.replace('restored:','original:'))
        result=pipeline(CONFIG,launch)
        self.assertEqual(seen,plan(CONFIG))
        self.assertEqual(len(result['metrics']),16)

    def test_fail_stop_and_replay_mismatch_before_later_roles(self):
        seen=[]
        def launch(role,inputs):
            seen.append(role)
            return dict(path=role,extent=1,sha256=role)
        with self.assertRaisesRegex(AssertionError,'Producer replay mismatch'):
            pipeline(PREPARED,launch)
        self.assertEqual(len(seen),3)
        self.assertFalse(any(r.endswith(':metrics') for r in seen))

    def test_scope_rejects_software_reserve_foreign_and_wrong_phase(self):
        for seed in (2100280,1009400,1009600,2100080,-1):
            with self.assertRaises(AssertionError):scope(request(CONFIG,f'original:{seed}:generate','generate'))
        for seed in (1009300,1009500,1009400):
            with self.assertRaises(AssertionError):scope(request(PREPARED,f'original:{seed}:generate','generate'))
        bad=request(CONFIG,'original:1009300:generate','generate')
        bad['configuration']['software_only']=0
        with self.assertRaises(AssertionError):scope(bad)
        bad=request(CONFIG,'original:01009300:generate','generate')
        with self.assertRaises(AssertionError):scope(bad)

    def test_scope_requires_complete_config_and_exact_kind(self):
        bad=request(CONFIG,'restored:1009300:audit','audit')
        with self.assertRaises(AssertionError):scope(bad)
        bad=request(CONFIG,'original:1009300:metrics','generate')
        with self.assertRaises(AssertionError):scope(bad)
        bad=request(CONFIG,'original:interpret','interpret')
        bad['configuration']['horizon']=512
        with self.assertRaises(AssertionError):scope(bad)
        for cfg in (CONFIG,PREPARED):
            supplied=request(cfg,f'original:{cfg["seeds"][0]}:generate','generate')
            self.assertEqual(scope(supplied)[1],cfg['seeds'][0])

    def test_precharged_stream_refuses_growth_and_reopen(self):
        from experiments.evidence_budget import Budget,QuotaError
        from experiments.digital_revision84_custody import open_reserved,mirror_limits
        with tempfile.TemporaryDirectory(dir=pathlib.Path.cwd()) as temp:
            self.assertEqual(pathlib.Path(temp).resolve().parent,pathlib.Path.cwd().resolve())
            b=Budget(pathlib.Path(temp)/'fresh',dict(raw=4),4)
            with b.create('raw','data',reserve=4):pass
            with open_reserved(b,'raw','data') as stream:
                stream.write(b'abcd')
                with self.assertRaises(QuotaError):stream.write(b'e')
            self.assertEqual((b.root/'raw/data').read_bytes(),b'abcd')
            with self.assertRaises(AssertionError):open_reserved(b,'raw','data')
        limits=mirror_limits({'a':64,'b':8},{'outcome':8})
        self.assertEqual(limits['restore'],80)

if __name__=='__main__':unittest.main()
