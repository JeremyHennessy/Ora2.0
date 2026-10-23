"""Prepared boundary/descriptor tests only; no ordinary World constructed."""
import copy,io,json,types,unittest
from unittest.mock import patch
from experiments import digital_pilot74_journal_child as child

def request(kind='crash',fault='partial'):
    pins={n:'b'*64 for n in child.REQUIRED|child.boundary.boundary.REQUIRED}
    config=copy.deepcopy(child.boundary.CONFIG);source=child.journal.sha(child.journal.enc(pins));cfg=child.journal.sha(child.journal.enc(config));revision='a'*40
    caps=dict(child.COMMON);caps['capsule-1.json' if kind=='sequence' else 'recovery.json']=24*child.MIB if kind=='sequence' else 40*child.MIB
    return dict(configuration=config,revision=revision,source_files=pins,source_sha256=source,configuration_sha256=cfg,identity=dict(revision=revision,source_sha256=source,config_sha256=cfg,law='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1'),kind=kind,fault=fault,role='normal-sequence' if kind=='sequence' else kind+'/'+fault,directory='D:/OraLab/runs/PREPARED-NOT-CREATED',inputs={k+str(c):{} for k in ('cut','audit') for c in (8192,9216,10240)},outputs={n:dict(limit=cap,device=1,inode=i+1) for i,(n,cap) in enumerate(caps.items())})

class JournalChild(unittest.TestCase):
    def test_all_nine_role_shapes(self):
        for kind in ('crash','recover'):
            for fault in ('partial','orphan','committed','normal'):
                r=request(kind,fault);identity,caps=child.shape(r)
                self.assertEqual(identity,r['identity']);self.assertEqual(caps['payload.pending'],40*child.MIB)
        self.assertEqual(child.shape(request('sequence','normal'))[1]['capsule-1.json'],24*child.MIB)
    def test_bad_roles_and_scope_stop_before_source_access(self):
        changes=[dict(kind='service'),dict(fault='retry'),dict(role='other'),dict(revision='z'*40),dict(configuration=dict(child.boundary.CONFIG,horizon=8192)),dict(source_sha256='0'*64)]
        for change in changes:
            r=request();r.update(change)
            with patch.object(child.boundary.boundary,'verify_source',side_effect=RuntimeError('source reached')):
                with self.assertRaises(AssertionError):child.admit(r)
        with self.assertRaises(AssertionError):child.shape(request('sequence','partial'))
    def test_duplicate_output_identity_and_cap_refused(self):
        for mutation in ('duplicate','bool','large','missing'):
            r=request()
            if mutation=='duplicate':r['outputs']['head.pending']['inode']=r['outputs']['head.json']['inode']
            elif mutation=='bool':r['outputs']['payload.pending']['limit']=True
            elif mutation=='large':r['outputs']['capsule-2.json']['limit']=40*child.MIB
            else:r['outputs'].pop('observation.json')
            with self.assertRaises(AssertionError):child.shape(r)
    def test_wrong_identity_and_missing_source_refused(self):
        r=request();r['identity']['law']='old'
        with self.assertRaises(AssertionError):child.shape(r)
        r=request();r['source_files'].pop('experiments/digital_pilot74_journal_child.py')
        with self.assertRaises(AssertionError):child.shape(r)
    def test_oversize_input_refused_before_physical_read(self):
        with patch.object(child,'read_recording',side_effect=RuntimeError('read reached')):
            for extent in (True,0,40*child.MIB+1):
                with self.assertRaises(AssertionError):child.input_record(dict(path='unused',extent=extent,sha256='0'*64),40*child.MIB)
    def test_hydration_exception_restores_every_descriptor(self):
        from experiments import digital_pressure71_population as base,digital_pilot74_population as kernel
        before=(base.World.__init__,base.World.step,base.World.__dict__['restore']);counts=dict(genesis=0,steps=0,hydrates=0);forbidden=dict(genesis=0,prefix=0,restore=0)
        loader=types.SimpleNamespace(hydrate=lambda *a:base.World.restore({}))
        with self.assertRaisesRegex(AssertionError,'forbidden hydration restore'):child.load_without_prefix(base,kernel,loader,b'{}',{}, {},counts,forbidden)
        self.assertEqual(forbidden,dict(genesis=0,prefix=0,restore=1));self.assertEqual(counts['hydrates'],0)
        self.assertIs(base.World.__init__,before[0]);self.assertIs(base.World.step,before[1]);self.assertIs(base.World.__dict__['restore'],before[2])
    def test_invented_object_hydrates_without_constructor_or_steps(self):
        class FakeWorld:
            def snapshot(self):return {'tick':8192}
        world=object.__new__(FakeWorld)
        from experiments import digital_pressure71_population as base
        counts=dict(genesis=0,steps=0,hydrates=0);forbidden=dict(genesis=0,prefix=0,restore=0)
        result=child.load_without_prefix(base,types.SimpleNamespace(World=FakeWorld),types.SimpleNamespace(hydrate=lambda *a:world),b'{"state":{"tick":8192}}',{}, {},counts,forbidden)
        self.assertIs(result,world);self.assertEqual(counts,dict(genesis=0,steps=0,hydrates=1));self.assertFalse(any(forbidden.values()))
    def test_prepared_entrypoint_stops_before_vm_or_owner_query(self):
        raw=child.journal.enc(request());out=io.StringIO()
        with patch.object(child.sys,'argv',['prepared','unused',str(len(raw)),child.journal.sha(raw),'prepared']),patch.object(child,'read_recording',return_value=raw),patch.object(child,'admit',return_value=(None,{})),patch.object(child.journal,'own_identity',side_effect=RuntimeError('owner reached')),patch.object(child.sys,'stdout',out):
            child.main()
        self.assertEqual(json.loads(out.getvalue()),dict(prepared_admission=True,genesis=0,steps=0,hydrates=0))

if __name__=='__main__':unittest.main()
