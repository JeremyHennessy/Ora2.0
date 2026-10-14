"""Mocked endpoint/source guards only; ZERO actual scientific World/seed draws."""
import hashlib,json,os,tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from experiments import digital_pressure71_scientific_child as child
from experiments import digital_pressure71_runplan as plan
from experiments import evidence_write_grant68 as transport
from experiments.evidence_budget import Budget
from tests.test_digital_pressure71_runner_boundaries import receipt

def temporary():
    if os.name=='nt':
        root=Path('D:/OraLab/temp');root.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=root,prefix='prepared71-handler-')
    return tempfile.TemporaryDirectory(prefix='prepared71-handler-')

def request_for(kind):
    spec=next(r for r in plan.roles() if r['kind']==kind.removesuffix('_ref'))
    request=dict(spec,kind=kind,export='original',source_files={},source_sha256='a'*64,
                 configuration_sha256='b'*64)
    endpoint='proof' if kind.endswith('_ref') else 'raw'
    request['role']=f"original:{spec['name']}:{endpoint}"
    return request

class ChildGuardTests(unittest.TestCase):
    def setup_request(self,root,kind):
        request=request_for(kind)
        budget=Budget(root/'budget',dict(raw=2*1024**2,failure=1024**2),3*1024**2)
        grant,seal=transport.seal(budget,'raw','out.json',1024**2,'a'*64,'b'*64,request['role'])
        request.update(grant=grant,grant_seal=seal)
        if kind.startswith('fork'):
            path=root/'admission.json';data=json.dumps(receipt()).encode();path.write_bytes(data)
            request['admission']=dict(path=str(path),extent=len(data),sha256=hashlib.sha256(data).hexdigest())
        return request

    def guarded(self,root,request,operation):
        with patch.object(child,'verify_source',return_value='a'*64) as source, \
             patch.object(child,'module_origins') as origins, \
             patch.object(child,'value_for',operation):
            result=child.execute_request(root,request)
        self.assertEqual(source.call_count,2);self.assertEqual(origins.call_count,2)
        return result

    def test_all_four_mocked_endpoint_paths_keep_counter_and_source_checks(self):
        for kind in ('population','population_ref','fork','fork_ref'):
            with temporary() as tmp:
                root=Path(tmp);request=self.setup_request(root,kind)
                from unittest.mock import Mock
                operation=Mock(return_value=(dict(prepared_only=True,scientific_admission=False),0))
                result=self.guarded(root,request,operation)
                self.assertEqual(result['kind'],kind);self.assertEqual(result['world_constructors'],0)
                self.assertEqual(result['treatment'],kind.startswith('fork'))
                output=Path(request['grant']['root'])/'raw/out.json'
                self.assertEqual(json.loads(output.read_bytes()),dict(prepared_only=True,scientific_admission=False))
                operation.assert_called_once()

    def test_treatment_without_admission_blocks_dispatch(self):
        with temporary() as tmp:
            root=Path(tmp);request=self.setup_request(root,'fork');request.pop('admission')
            with patch.object(child,'verify_source',return_value='a'*64),patch.object(child,'value_for') as operation:
                with self.assertRaises(AssertionError):child.execute_request(root,request)
                operation.assert_not_called()

    def test_wrong_bank_and_role_bindings_block_dispatch(self):
        for field,value in [('seed',74300),('name','wrong'),('role','wrong'),('dose',True)]:
            with temporary() as tmp:
                root=Path(tmp);request=self.setup_request(root,'population');request[field]=value
                with patch.object(child,'verify_source',return_value='a'*64),patch.object(child,'value_for') as operation:
                    with self.assertRaises(AssertionError):child.execute_request(root,request)
                    operation.assert_not_called()

    def test_forged_grant_blocks_dispatch(self):
        with temporary() as tmp:
            root=Path(tmp);request=self.setup_request(root,'population');request['grant']['inode']+=1
            with patch.object(child,'verify_source',return_value='a'*64),patch.object(child,'value_for') as operation:
                with self.assertRaises(AssertionError):child.execute_request(root,request)
                operation.assert_not_called()

    def test_input_extent_refused_before_read_or_hash(self):
        with temporary() as tmp:
            path=Path(tmp)/'input.json';path.write_bytes(b'123456')
            with patch.object(Path,'open',side_effect=RuntimeError('file opened')):
                with self.assertRaises(AssertionError):child.bounded_bytes(path,5)
                with self.assertRaises(AssertionError):child.bounded_bytes(path,20,True)
                with self.assertRaises(AssertionError):child.bounded_bytes(path,20,5)

    def test_input_hash_and_schema_checked(self):
        with temporary() as tmp:
            path=Path(tmp)/'input.json';data=b'{"x":1}';path.write_bytes(data)
            spec=dict(path=str(path),extent=len(data),sha256=hashlib.sha256(data).hexdigest())
            self.assertEqual(child.read_spec(spec,100),dict(x=1))
            spec['sha256']='e'*64
            with self.assertRaises(AssertionError):child.read_spec(spec,100)

    def test_manifest_traversal_refused_without_outside_read(self):
        data=b'prepared source';identity=hashlib.sha256(data).hexdigest()
        pins={name:identity for name in child.REQUIRED};pins['../private.py']=identity
        with patch.object(child,'bounded_bytes',return_value=data) as reader:
            with self.assertRaises(AssertionError):child.verify_source(Path.cwd(),pins)
            self.assertFalse(any('..' in call.args[0].parts for call in reader.call_args_list))

    def test_live_manifest_binding_and_changed_hash_without_source_mutation(self):
        root=Path(child.__file__).resolve().parents[1]
        pins={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in child.REQUIRED}
        self.assertEqual(child.verify_source(root,pins),hashlib.sha256(child.canonical(pins)).hexdigest())
        bad=dict(pins);bad['experiments/digital_pressure71_scientific_child.py']='a'*64
        with self.assertRaises(AssertionError):child.verify_source(root,bad)

    def test_mocked_producer_uses_registered_dose_horizon_and_restores_counter(self):
        from experiments import digital_pressure71_population as kernel
        request=request_for('population');original=kernel.World.__init__
        with patch.object(kernel,'history',return_value={'prepared_only':True}) as history:
            value,calls=child.value_for(request,dict(source_sha256='a'*64,configuration_sha256='b'*64))
        history.assert_called_once_with(request['seed'],mode='faithful',inheritance_mode='parent_copy',dose=8,horizon=4096,software_only=False)
        self.assertEqual(calls,0);self.assertEqual(value,{'prepared_only':True})
        self.assertIs(kernel.World.__init__,original)

    def test_mocked_referee_paths_request_no_producer_import(self):
        import builtins
        from experiments import digital_pressure71_natural_referee as natural
        from experiments import digital_pressure71_referee as literal
        original=builtins.__import__
        def guarded(name,*args,**kwargs):
            assert 'population' not in name and 'digital_pressure71_world' not in name
            assert not any('population' in str(value) for value in kwargs.get('fromlist',()))
            if len(args)>2:assert not any('population' in str(value) for value in (args[2] or ()))
            return original(name,*args,**kwargs)
        for kind in ('population_ref','fork_ref'):
            request=request_for(kind);request['input']={}
            source=dict(seed=request['seed'],dose=request['dose'],mode='faithful',
                        inheritance_mode='parent_copy',horizon=4096,software_only=False,hash='e'*64)
            row=source if kind=='population_ref' else dict(natural=source,slot_kind=request['slot_kind'],role=request['fork_role'])
            with patch.object(child,'read_spec',return_value=row), \
                 patch.object(natural,'audit',return_value={'prepared_only':True}), \
                 patch.object(literal,'audit',return_value={'prepared_only':True,'null':True}), \
                 patch.object(builtins,'__import__',side_effect=guarded):
                _,calls=child.value_for(request,dict(source_sha256='a'*64,configuration_sha256='b'*64))
            self.assertEqual(calls,0)

if __name__=='__main__':unittest.main()
