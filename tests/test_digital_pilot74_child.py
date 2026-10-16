"""Prepared admission/custody checks; grants mocked, no VM execution."""
import copy,hashlib,io,json,unittest
from unittest.mock import patch
from experiments import digital_pilot74_child as child

def request(kind='generate',cut=None):
    pins={n:'b'*64 for n in child.NEW_FILES|child.boundary.REQUIRED}
    role='original:3:'+kind+('' if kind=='generate' else ':'+str(cut))
    caps={str(c):40*child.MIB for c in (8192,9216,10240)} if kind=='generate' else {'main':128*1024 if kind=='audit' else 40*child.MIB if cut in (8192,9216) else 8*1024}
    return dict(configuration=copy.deepcopy(child.CONFIG),revision='a'*40,source_files=pins,source_sha256=child.sha(child.canonical(pins)),configuration_sha256=child.sha(child.canonical(child.CONFIG)),seed=3,export='original',kind=kind,cut=cut,role=role,inputs={} if kind=='generate' else {'capsule':{}} if kind=='audit' else {'capsule':{},'audit':{},'reference':{}},outputs={label:dict(grant=dict(limit=cap,device=1,inode=i+1),seal='c'*64) for i,(label,cap) in enumerate(caps.items())})

class PilotChildPrepared(unittest.TestCase):
    def test_all_role_grants_are_bound_before_execution(self):
        for kind,cut in (('generate',None),('audit',8192),('audit',9216),('audit',10240),('resume',8192),('resume',9216),('resume',10240)):
            r=request(kind,cut)
            with patch.object(child.boundary,'validate_grant') as validate:
                self.assertEqual(child.admit(r),r['role'])
                self.assertEqual(validate.call_count,3 if kind=='generate' else 1)
                for call in validate.call_args_list:
                    bound,source,endpoint=call.args
                    self.assertEqual(source,r['source_sha256']);self.assertEqual(bound['configuration_sha256'],r['configuration_sha256'])
                    self.assertEqual(endpoint,'proof' if kind=='audit' else 'raw')
                    self.assertTrue(bound['role'].startswith(r['role']))
    def test_invalid_configuration_seed_cut_and_roles_stop_before_grants(self):
        changes=[dict(seed=True),dict(seed=1),dict(role='other'),dict(revision='z'*40),dict(kind='service'),dict(cut=7168),dict(configuration=dict(child.CONFIG,dose=8.0)),dict(configuration=dict(child.CONFIG,horizon=8193)),dict(source_sha256='0'*64)]
        for change in changes:
            r=request();r.update(change)
            with patch.object(child.boundary,'validate_grant',side_effect=RuntimeError('grant reached')):
                with self.assertRaises(AssertionError):child.admit(r)
        r=request('resume',7168);r['cut']=True
        with patch.object(child.boundary,'validate_grant',side_effect=RuntimeError('grant reached')):
            with self.assertRaises(AssertionError):child.admit(r)
    def test_missing_output_role_and_role_specific_caps_refused(self):
        r=request();r['outputs'].pop('9216')
        with patch.object(child.boundary,'validate_grant',side_effect=RuntimeError('grant reached')):
            with self.assertRaises(AssertionError):child.admit(r)
        r=request('resume',10240);r['outputs']['main']['grant']['limit']=8193
        with patch.object(child.boundary,'validate_grant'):
            with self.assertRaises(AssertionError):child.admit(r)
    def test_overlarge_and_boolean_input_extent_refused_before_read(self):
        from experiments import digital_pilot74_custody as custody
        for extent in (True,0,41*child.MIB):
            with patch.object(custody,'read_recording',side_effect=RuntimeError('read reached')):
                with self.assertRaises(AssertionError):child.read_input(dict(path='D:/OraLab/unused',extent=extent,sha256='0'*64),40*child.MIB)
    def test_two_generation_outputs_cannot_share_one_precharged_file(self):
        r=request();r['outputs']['8192']['grant']['inode']=r['outputs']['9216']['grant']['inode']
        with patch.object(child.boundary,'validate_grant'):
            with self.assertRaises(AssertionError):child.admit(r)
    def test_generator_exception_restores_classmethod_descriptor_and_reports_counts(self):
        from experiments import digital_pressure71_population as base,digital_pilot74_population as kernel
        r=request();before=base.World.__dict__['restore'];stderr=io.StringIO()
        with patch.object(child.sys,'argv',['prepared','D:/OraLab/unused.json']),patch.object(child.boundary,'bounded_bytes',return_value=child.canonical(r)),patch.object(child.boundary,'validate_grant'),patch.object(child.boundary,'verify_source'),patch.object(kernel,'World',side_effect=RuntimeError('prepared producer stop')),patch.object(child.sys,'stderr',stderr):
            with self.assertRaisesRegex(RuntimeError,'prepared producer stop'):child.main()
        self.assertIs(base.World.__dict__['restore'],before)
        recorded=json.loads(stderr.getvalue());self.assertEqual(recorded['counts'],dict(genesis=0,ordinary_steps=0,hydrations=0))
        self.assertTrue(recorded['partial_state_unavailable'])

if __name__=='__main__':unittest.main()
