"""Meaningful prospective-scope refusals over authored structural fixtures."""
import copy,hashlib,unittest
from unittest.mock import patch
from experiments import digital_pilot74_data as data,digital_pilot74_loader as loader,digital_pilot74_referee as referee
from test_digital_pilot74_data import prepared,packet,IDENTITY
from test_digital_pilot74_loader import invented_audit

class PilotScope(unittest.TestCase):
    def test_old_versions_and_laws_cannot_be_relabelled_by_loader(self):
        state,checkpoint=prepared();raw,sha=packet(state,checkpoint)
        value=__import__('json').loads(raw);value['version']='DIGITAL-CAPSULE03-LONG-STATE-data-v1'
        bad=data.canonical(value)
        with self.assertRaises(ValueError):data.decode_prepared(bad,IDENTITY,hashlib.sha256(bad).hexdigest(),40*1024**2)
        oldlaw=dict(IDENTITY,law='DIGITAL-FINITE-LONGITUDINAL-ECOLOGY-01-engineering-v1')
        with self.assertRaises(ValueError):data.decode_prepared(raw,oldlaw,sha,40*1024**2)
    def test_unregistered_intermediate_or_overshoot_cut_refused(self):
        for cut in (7168,8193,10241):
            state,checkpoint=prepared();state['tick']=cut
            raw,sha=packet(state,checkpoint)
            with self.assertRaises(ValueError):data.decode_prepared(raw,IDENTITY,sha,40*1024**2)
    def test_byte_cap_rejects_before_json_parse(self):
        raw,sha=packet()
        with patch.object(data.json,'loads',side_effect=AssertionError('parser reached')):
            for cap in (True,0,40*1024**2+1):
                with self.assertRaises(ValueError):data.decode_prepared(raw,IDENTITY,sha,cap)
    def test_direct_loader_never_invokes_full_prefix_referee(self):
        state,checkpoint=prepared(10240);raw,sha=packet(state,checkpoint);a=invented_audit(raw,sha,state)
        with patch.object(referee,'audit',side_effect=AssertionError('prefix')),patch.object(referee,'verify_capsule',side_effect=AssertionError('capsule replay')):
            world=loader.hydrate(raw,IDENTITY,sha,a,data.digest(a));self.assertEqual(world.tick,10240)
    def test_old_audit_version_and_seed4_refused(self):
        state,checkpoint=prepared();raw,sha=packet(state,checkpoint);a=invented_audit(raw,sha,state)
        a['version']='DIGITAL-CAPSULE03-AUDIT-v1'
        with self.assertRaises(ValueError):loader.hydrate(raw,IDENTITY,sha,a,data.digest(a))
        state,checkpoint=prepared(seed=4);raw,sha=packet(state,checkpoint)
        with self.assertRaises(ValueError):data.decode_prepared(raw,IDENTITY,sha,40*1024**2)
    def test_capsule_referee_rejects_unregistered_cut_before_execution(self):
        state,checkpoint=prepared();state['tick']=8193;raw,sha=packet(state,checkpoint)
        with patch.object(referee,'audit',side_effect=AssertionError('unregistered prefix')):
            with self.assertRaises(AssertionError):referee.verify_capsule(raw,IDENTITY,sha,len(raw))
if __name__=='__main__':unittest.main()
