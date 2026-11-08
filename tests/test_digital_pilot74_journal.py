"""Invented host journal fixtures only; no executed ancestry or World import."""
import ast,json,os,tempfile,unittest
from pathlib import Path
from experiments import digital_pilot74_journal as j

class PilotJournal(unittest.TestCase):
    ROOT=Path('D:/OraLab/tmp') if os.name=='nt' else Path(tempfile.gettempdir())
    def setUp(self):
        root=self.ROOT;root.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='pilot74-journal-prepared-',dir=root)
        self.directory=Path(self.temp.name);self.identity={'fixture':'AUTHOR-SUPPLIED'}
        assert self.directory.resolve().is_relative_to(root.resolve())
        self.raw={str(cut):j.enc(dict(version='DIGITAL-PILOT74-STATE-data-v1',identity=self.identity,state={'tick':cut})) for cut in (8192,9216,10240)}
        self.audits={cut:dict(version='DIGITAL-PILOT74-AUDIT-v1',identity=self.identity,tick=int(cut),extent=len(raw),capsule_sha256=j.sha(raw),verified=True,engineering_only=True,stage_credit=False) for cut,raw in self.raw.items()}
        for name in ('capsule-1.json','capsule-2.json','capsule-3.json','payload.pending','head.json','head.pending'):(self.directory/name).touch()
        j.write(self.directory/'capsule-1.json',self.raw['8192'],4096)
        j.write(self.directory/'head.json',j.enc(j.head(self.raw['8192'],self.audits['8192'],1)),4096)
    def tearDown(self):
        assert self.directory.resolve().is_relative_to(self.ROOT.resolve());self.temp.cleanup()
    def to_middle(self):
        self.assertTrue(j.commit(self.directory,self.raw['9216'],self.audits['9216'],'normal',2,self.audits))
    def test_normal_two_interval_commit_and_terminal_authority(self):
        self.to_middle();self.assertTrue(j.commit(self.directory,self.raw['10240'],self.audits['10240'],'normal',3,self.audits))
        self.assertEqual(j.select(self.directory,self.identity,self.audits)[0]['tick'],10240)
    def test_partial_does_not_promote(self):
        self.to_middle();self.assertFalse(j.commit(self.directory,self.raw['10240'],self.audits['10240'],'partial',3,self.audits))
        self.assertEqual(j.select(self.directory,self.identity,self.audits)[0]['tick'],9216)
        self.assertEqual((self.directory/'payload.pending').read_bytes(),self.raw['10240'][:len(self.raw['10240'])//2])
    def test_complete_orphan_does_not_promote(self):
        self.to_middle();self.assertFalse(j.commit(self.directory,self.raw['10240'],self.audits['10240'],'orphan',3,self.audits))
        self.assertEqual(j.select(self.directory,self.identity,self.audits)[0]['tick'],9216)
        self.assertEqual((self.directory/'capsule-3.json').read_bytes(),self.raw['10240'])
    def test_committed_boundary_promotes_only_after_complete_head(self):
        self.to_middle();self.assertTrue(j.commit(self.directory,self.raw['10240'],self.audits['10240'],'committed',3,self.audits))
        self.assertEqual(j.select(self.directory,self.identity,self.audits)[0]['tick'],10240)
    def test_skipped_or_reverse_sequence_refused(self):
        with self.assertRaises(AssertionError):j.commit(self.directory,self.raw['10240'],self.audits['10240'],'normal',3,self.audits)
        self.to_middle()
        with self.assertRaises(AssertionError):j.commit(self.directory,self.raw['8192'],self.audits['8192'],'normal',1,self.audits)
    def test_corrupt_previous_authority_refused_before_new_write(self):
        (self.directory/'capsule-1.json').write_bytes(b'CORRUPT')
        with self.assertRaises(AssertionError):self.to_middle()
        self.assertEqual((self.directory/'capsule-2.json').stat().st_size,0)
    def test_wrong_audit_or_old_version_refused(self):
        bad=dict(self.audits['9216'],version='DIGITAL-CAPSULE03-AUDIT-v1')
        with self.assertRaises(AssertionError):j.head(self.raw['9216'],bad,2)
        bad=dict(self.audits['9216'],capsule_sha256='0'*64)
        with self.assertRaises(AssertionError):j.head(self.raw['9216'],bad,2)
    def test_duplicate_or_noncanonical_head_refused(self):
        head=j.head(self.raw['8192'],self.audits['8192'],1)
        (self.directory/'head.json').write_text(json.dumps(head,indent=2),encoding='ascii')
        with self.assertRaises(AssertionError):j.select(self.directory,self.identity,self.audits)
    def test_typed_fields_and_names_refused(self):
        original=j.head(self.raw['8192'],self.audits['8192'],1)
        for field,value in [('sequence',True),('tick',True),('extent',True),('payload_name','../escape')]:
            (self.directory/'head.json').write_bytes(j.enc(dict(original,**{field:value})))
            with self.assertRaises(AssertionError):j.select(self.directory,self.identity,self.audits)
    def test_nonempty_new_slot_refused(self):
        (self.directory/'capsule-2.json').write_bytes(b'ORPHAN')
        with self.assertRaises(AssertionError):self.to_middle()
        self.assertEqual((self.directory/'capsule-2.json').read_bytes(),b'ORPHAN')
    def test_unknown_or_reused_process_does_not_authorize_deletion(self):
        self.assertEqual(j.owner_decision(123,None),'UNKNOWN');self.assertEqual(j.owner_decision(123,124),'REUSED')
        tree=ast.parse(Path(j.__file__).read_text(encoding='utf-8'))
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in ('unlink','rmdir','remove') for n in ast.walk(tree)))
if __name__=='__main__':unittest.main()
