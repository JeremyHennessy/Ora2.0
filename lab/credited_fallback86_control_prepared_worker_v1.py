"""Source-only tests and retained-record literal checks. New Worlds forbidden."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import stat

root=Path.cwd()
sys.path.insert(0,str(root))
request=json.loads(Path(sys.argv[1]).read_bytes())
for name,digest in request['source_files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
for spec in request['closed_inputs']:
    path=Path(spec['path']); meta=path.lstat()
    assert stat.S_ISREG(meta.st_mode) and meta.st_nlink==1 and not getattr(meta,'st_file_attributes',0)&0x400
    assert meta.st_size==spec['extent']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==spec['sha256']

ALLOWED={'experiments.digital_memory80','experiments.digital_credited_fallback86_source',
         'experiments.digital_credited_fallback86_controls',
         'experiments.digital_credited_fallback86_control_referee'}
class ImportGuard:
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('experiments.') and fullname not in ALLOWED:
            raise AssertionError('Unqualified module refused: '+fullname)
sys.meta_path.insert(0,ImportGuard())
from experiments import digital_memory80 as engine
def no_worlds(*args,**kwargs):raise AssertionError('New World forbidden during retained/source qualification')
engine.World.__init__=no_worlds
engine.World.step=no_worlds
from experiments import digital_credited_fallback86_controls as adapter
from experiments import digital_credited_fallback86_control_referee as literal

buffer=io.StringIO()
result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(
    unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_digital_credited_fallback86_controls.py'))
if not result.wasSuccessful():print(buffer.getvalue())
assert result.wasSuccessful() and result.testsRun==5
closed=json.loads(Path(request['closed_receipt']['path']).read_bytes())
assert closed['verified'] and closed['archive_exact']
rows=[];dead_derivations=0;forgeries=0
for seed in range(2100080,2100084):
    spec=closed['completed_roles'][f'original:{seed}:generate']
    assert spec in request['closed_inputs']
    body=json.loads(Path(spec['path']).read_bytes())
    assert body['seed']==seed and body['error'] is None
    assert [r['descriptor'] for r in body['records']]==[
        [q,route] for q in (2,4,8) for route in ('fallback0','model','fallback1')]
    for row in body['records']:
        kwargs=dict(seed=seed,mode='no_variation',max_population=1,expansion_tick=0,
                    program=row['programme'],horizon=256)
        proof=literal.audit(row['state'],**kwargs)
        old=next(r['proof'] for r in closed['summary'][str(seed)]['summaries']
                 if r['descriptor']==row['descriptor'])
        assert proof==old
        rows.append(dict(seed=seed,descriptor=row['descriptor'],proof=proof))
        if not row['state']['deaths']:continue
        # Read-only ledger derivation on OLD dead records. No copied state enters
        # a new World; these are never-active null proofs, not paid active roles.
        for control in ('model_erased','model_misbound','fallback_misbound','history_disabled'):
            rt=adapter.Runtime(row['descriptor'][1],control)
            entity=dict(pc=0);ledger=[]
            for event in row['state']['events']:
                completed=rt.completed
                entry=rt.before(entity);pc=rt.dispatch_pc
                read=rt.read(entity['memory'],entity['registers'][1]) if pc in (7,12) else None
                completion=rt.after(event)
                ledger.append(dict(tick=event['tick'],dispatch_pc=pc,completed_before=completed,
                                   entry=entry,read=read,completion=completion))
                if 'after' in event:entity=copy.deepcopy(event['after'])
            assert rt.completed<48
            active_kwargs=dict(kwargs,horizon=1024,control=control,ledger=ledger)
            assert literal.audit(row['state'],**active_kwargs)==old
            dead_derivations+=1
            if forgeries:continue
            candidates=[]
            def corrupt(index,field,value):
                altered=copy.deepcopy(ledger);altered[index][field]=value;return altered
            candidates += [corrupt(0,'dispatch_pc',1),corrupt(0,'completed_before',1),
                           corrupt(0,'tick',2),ledger[:-1]]
            ix=next(i for i,x in enumerate(ledger) if x['entry'] is not None)
            for field,value in (('active',1),('projected_entry',12),('previous_pc',0),('completed',99)):
                altered=copy.deepcopy(ledger);altered[ix]['entry'][field]=value;candidates.append(altered)
            ix=next(i for i,x in enumerate(ledger) if x['read'] is not None)
            for field,value in (('value',17),('source_address',None),('address',17)):
                altered=copy.deepcopy(ledger);altered[ix]['read'][field]=value;candidates.append(altered)
            for altered in candidates:
                try:literal.audit(row['state'],**dict(active_kwargs,ledger=altered))
                except AssertionError:forgeries+=1
                else:raise AssertionError('Forged control evidence accepted')
assert len(rows)==36 and dead_derivations==32 and forgeries==11
assert not [n for n in sys.modules if n.startswith('experiments.') and n not in ALLOWED]
for name in ALLOWED:
    assert Path(sys.modules[name].__file__).resolve()==(root/(name.replace('.','/')+'.py')).resolve()
for name,digest in request['source_files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
print(json.dumps(dict(verified=True,checks=5,retained_null_histories=36,
    never_active_dead_ledger_derivations=32,forgeries_refused=11,rows=rows,
    worlds=0,targets=0,paid_active_physics_qualified=False,stage_credit=False),sort_keys=True))
