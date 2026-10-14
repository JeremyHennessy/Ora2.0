"""Native boundary preparation; grants/producers mocked, no science contexts."""
import copy,io,json,unittest
from unittest.mock import patch
from experiments import digital_cognitive76_child as child
def request(kind='generate',export='original',chunk=2):
    pins={p:'b'*64 for p in child.REQUIRED};cfg=copy.deepcopy(child.CONFIG)
    role=f'{export}:77400:intact:{chunk}:{kind}'
    return dict(configuration=cfg,revision='a'*40,source_files=pins,source_sha256=child.hashlib.sha256(child.canonical(pins)).hexdigest(),configuration_sha256=child.hashlib.sha256(child.canonical(cfg)).hexdigest(),seed=77400,control='intact',chunk=chunk,kind=kind,export=export,role=role,input=None if kind=='generate' else {},grant=dict(limit=(1 if kind=='audit' else 16)*1024**2),grant_seal='c'*64)
class Boundary(unittest.TestCase):
    def test_complete_role_shape_is_bound_before_source_work(self):
        for kind,export in (('generate','original'),('generate','restored'),('audit','original')):
            for chunk in (0,1,2):
                r=request(kind,export,chunk)
                with patch.object(child,'validate_grant') as validate:
                    self.assertEqual(child.admit(r),r['role']);self.assertEqual(validate.call_count,1)
                    self.assertEqual(validate.call_args.args[1],r['source_sha256'])
    def test_reserves_bad_scopes_and_configuration_refused_before_grants(self):
        changes=[dict(seed=True),dict(seed=77500),dict(seed=77700),dict(chunk=True),dict(chunk=3),dict(kind='service'),dict(control='repair'),dict(role='other'),dict(revision='z'*40),dict(configuration=dict(child.CONFIG,failure_penalty=0)),dict(source_sha256='0'*64)]
        for change in changes:
            r=request();r.update(change)
            with patch.object(child,'validate_grant',side_effect=RuntimeError('grant reached')):
                with self.assertRaises(AssertionError):child.admit(r)
    def test_proof_must_use_original_and_source_roster_is_complete(self):
        with patch.object(child,'validate_grant'):
            with self.assertRaises(AssertionError):child.admit(request('audit','restored'))
            r=request();r['source_files'].pop('experiments/digital_cognitive76_referee.py')
            with self.assertRaises(AssertionError):child.admit(r)
    def test_caps_and_input_extent_refused(self):
        r=request();r['grant']['limit']=16*1024**2+1
        with patch.object(child,'validate_grant'):
            with self.assertRaises(AssertionError):child.admit(r)
        for extent in (True,0,16*1024**2+1):
            with self.assertRaises(AssertionError):child.read_spec(dict(path='unused',extent=extent,sha256='0'*64),16*1024**2)
    def test_duplicate_json_keys_are_not_canonical_authority(self):
        with self.assertRaises(AssertionError):json.loads('{"a":0,"a":1}',object_pairs_hook=child.pairs)
    def test_producer_failure_restores_methods_and_reports_counts(self):
        from experiments import digital_cognitive76_world as kernel,digital_cognitive76_history as producer
        r=request();before=(kernel.World.__init__,kernel.World.step);err=io.StringIO()
        with patch.object(child.sys,'argv',['prepared','D:/OraLab/unused']),patch.object(child,'bounded_bytes',return_value=child.canonical(r)),patch.object(child,'validate_grant'),patch.object(child,'verify_source',return_value=r['source_sha256']),patch.object(producer,'batch',side_effect=RuntimeError('prepared stop')),patch.object(child.sys,'stderr',err):
            with self.assertRaisesRegex(RuntimeError,'prepared stop'):child.main()
        self.assertIs(kernel.World.__init__,before[0]);self.assertIs(kernel.World.step,before[1])
        self.assertEqual(json.loads(err.getvalue())['counts'],dict(genesis=0,ordinary_steps=0))

if __name__=='__main__':unittest.main()
