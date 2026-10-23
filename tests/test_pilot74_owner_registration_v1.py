"""Synthetic grant/receipt refusals only;no locks,processes,grants or Worlds."""
import copy,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import digital_pilot74_owner_registration_v1 as r
from experiments import digital_pilot74_outer_owner_v1 as outer


class Registration(unittest.TestCase):
    def fixture(self):
        registration={'path':'synthetic','extent':1,'sha256':'f'*64}
        reg=dict(owner={'pid':123,'birth':'456'},operator_lock={'synthetic':True},source_head='a'*40,
            source_files={'synthetic.py':'b'*64},python={'synthetic':True},argv_sha256='c'*64,prepared_monotonic_ns=1)
        grant=dict(schema='PILOT74-NEW-OWNER-PROBE-GRANT-v1',verdict='PASS',registration=registration,
            cases=r.CASES,reviewer_identity='SYNTHETIC',review_evidence=['fixture'],worlds=0,production_admission=False,
            issued_monotonic_ns=2,expires_monotonic_ns=100*10**9,**{k:reg[k] for k in reg if k!='prepared_monotonic_ns'})
        return registration,reg,grant

    def test_valid_shape_is_not_a_production_grant(self):
        pin,reg,grant=self.fixture();r.validate_grant(grant,pin,reg,3)
        self.assertFalse(grant['production_admission'])

    def test_expired_or_short_or_overlong_grant_refused(self):
        for expiry in [0,30*10**9,301*10**9]:
            pin,reg,g=self.fixture();g['expires_monotonic_ns']=expiry
            with self.assertRaises(AssertionError):r.validate_grant(g,pin,reg,3)

    def test_other_owner_registration_command_and_source_refused(self):
        for key in ['owner','operator_lock','registration','source_head','source_files','python','argv_sha256']:
            pin,reg,g=self.fixture();g[key]='changed'
            with self.assertRaises(AssertionError):r.validate_grant(g,pin,reg,3)

    def test_scientific_or_extra_case_authority_refused(self):
        for key,value in [('worlds',1),('production_admission',True),('cases',['ordinary','extra'])]:
            pin,reg,g=self.fixture();g[key]=value
            with self.assertRaises(AssertionError):r.validate_grant(g,pin,reg,3)

    def test_corrupt_physical_pin_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'data.json';r.write(path,{'a':1});p=r.pin(path);path.write_bytes(b'changed')
            with self.assertRaises(AssertionError):r.read(p)

    def test_deadline_cannot_be_extended_or_boolean(self):
        # Invalid boundary inputs fail before any process creation.
        from unittest.mock import patch,Mock
        for value in [True,0,3600001]:
            k=Mock();k.GetTickCount64.return_value=1
            with patch.object(outer.win,'kernel',return_value=k):
                with self.assertRaises(ValueError):outer.launch({'wall_ms':value},lambda request:True)


if __name__=='__main__':unittest.main()
