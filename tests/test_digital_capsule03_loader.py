"""Prepared mocks/invented authority only; no natural resume qualification."""
import ast,hashlib,json,unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_capsule03_data as data,digital_capsule03_loader as loader,digital_capsule03_referee as referee
from test_digital_capsule03_data import IDENTITY,prepared,packet

def invented_audit(raw,sha,state):
    summary=dict(verified=True,seed=state['seed'],dose=8,horizon=state['tick'],ticks=state['tick'],software_only=True,scientific_admission=False,mode='faithful',inheritance_mode='parent_copy',fuel_mode='renewed',stage_credit=False,selection=False)
    return dict(version='DIGITAL-CAPSULE03-AUDIT-v1',verified=True,identity=IDENTITY,capsule_sha256=sha,extent=len(raw),state_sha256=data.digest(state),tick=state['tick'],audit_prefix_instructions=state['tick'],summary=summary,engineering_only=True,stage_credit=False)

class LongLoaderPrepared(unittest.TestCase):
    def test_no_genesis_step_or_restore_during_invented_state_hydration(self):
        # Trusted-parent audit is deliberately fabricated; this is software reachability.
        for cut in (7168,8192):
            state,checkpoint=prepared(cut);raw,sha=packet(state,checkpoint);a=invented_audit(raw,sha,state)
            with patch.object(loader.kernel.World,'__init__',side_effect=AssertionError('genesis')),patch.object(loader.kernel.World,'step',side_effect=AssertionError('step')),patch.object(loader.kernel.World,'restore',side_effect=AssertionError('restore')):
                world=loader.hydrate(raw,IDENTITY,sha,a,data.digest(a))
                self.assertIs(type(world),loader.kernel.World);self.assertEqual(world.snapshot(),state)
    def test_external_audit_hash_precedes_boundary_and_allocation(self):
        raw,sha=packet()
        with patch.object(data,'decode_prepared',side_effect=AssertionError('decode')):
            with self.assertRaises(ValueError):loader.hydrate(raw,IDENTITY,sha,{'verified':True},'0'*64)
    def test_verified_flag_is_insufficient_even_when_externally_hashed(self):
        raw,sha=packet();a={'verified':True}
        with patch.object(data,'decode_prepared',side_effect=AssertionError('decode')):
            with self.assertRaises(ValueError):loader.hydrate(raw,IDENTITY,sha,a,data.digest(a))
    def test_receipt_cut_extent_bool_identity_and_state_hash_binding(self):
        state,checkpoint=prepared();raw,sha=packet(state,checkpoint);a=invented_audit(raw,sha,state)
        for edit in (dict(a,tick=64,audit_prefix_instructions=64),dict(a,tick=True),dict(a,extent=True),dict(a,extent=len(raw)+1),dict(a,identity=dict(IDENTITY,revision='d'*40)),dict(a,stage_credit=True),dict(a,audit_prefix_instructions=True)):
            with patch.object(data,'decode_prepared',side_effect=AssertionError('decode')):
                with self.assertRaises(ValueError):loader.hydrate(raw,IDENTITY,sha,edit,data.digest(edit))
        bad=dict(a,state_sha256='f'*64)
        with self.assertRaises(ValueError):loader.hydrate(raw,IDENTITY,sha,bad,data.digest(bad))
    def test_independent_capsule_custody_refuses_before_literal_audit(self):
        raw,sha=packet()
        with patch.object(referee,'audit',side_effect=AssertionError('literal audit reached')):
            for bad,identity in ((raw[:-1],IDENTITY),(raw,dict(IDENTITY,revision='d'*40)),(raw.replace(b'"_dose":8',b'"_dose":8,"_dose":8'),IDENTITY)):
                with self.assertRaises((AssertionError,ValueError)):referee.verify_capsule(bad,identity,hashlib.sha256(bad).hexdigest(),len(bad))
    def test_wrong_summary_seed_dose_cut_scope_refused(self):
        state,checkpoint=prepared();raw,sha=packet(state,checkpoint);a=invented_audit(raw,sha,state)
        for key,value in (('seed',4),('seed',True),('dose',1),('ticks',8192),('horizon',8192),('software_only',False),('verified',1),('selection',True)):
            bad=dict(a,summary=dict(a['summary'],**{key:value}))
            with self.assertRaises(ValueError):loader.hydrate(raw,IDENTITY,sha,bad,data.digest(bad))
    def test_literal_audit_is_explicit_and_separate_from_loader(self):
        raw,sha=packet()
        # No call to producer or data boundary may substitute for the independent audit.
        with patch.object(referee,'audit',side_effect=RuntimeError('independent audit required')),patch.object(data,'decode_prepared',side_effect=AssertionError('shared validation')):
            with self.assertRaisesRegex(RuntimeError,'independent audit required'):referee.verify_capsule(raw,IDENTITY,sha,len(raw))
        tree=ast.parse(Path(referee.__file__).read_text())
        self.assertFalse(any(isinstance(n,ast.ImportFrom) for n in ast.walk(tree)))
        self.assertEqual([a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names],['hashlib','json'])
    def test_loader_source_has_no_vm_replay_calls(self):
        tree=ast.parse(Path(loader.__file__).read_text())
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in ('step','restore','run','audit','verify_capsule','__init__') for n in ast.walk(tree)))

if __name__=='__main__':unittest.main()
