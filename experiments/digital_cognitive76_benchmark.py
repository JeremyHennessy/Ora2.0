"""Separately authored paid capacity benchmark, never a blind candidate.

The generic updater was registered before primary outcomes. It contains no
target map; the actor's own negative feedback gates revisions of blank models.
"""
import hashlib
import json
import sys
from pathlib import Path
from experiments import digital_cognitive76_child as boundary
from experiments.digital_cognitive76_source import compile_atoms

NAME = 'supplied_learning_benchmark'
ARMS = ('intact', 'model_disabled', 'history_misbound')
VERSION = 'DIGITAL-COGNITIVE76-SUPPLIED-BENCHMARK-v1'
PROGRAM = compile_atoms([[18,0,0],[21,0,0]])
CONFIG = dict(version=VERSION, contract_sha256='90f7c13f49e591d021777f2596d42e5b0805ee476fa2f7b95c7abbab8792e26f', primary=list(range(77400,77408)),
              unseen=list(range(77600,77608)), controls=list(ARMS), horizon=512,
              formation=76, programme_sha256=hashlib.sha256(boundary.canonical(PROGRAM)).hexdigest(),
              updater='AUTHOR-SUPPLIED generic prediction flip after own error',
              acquired_models='initially all zero', primary_bank_changed=False)
REQUIRED = boundary.REQUIRED | {'experiments/digital_cognitive76_benchmark.py'}

def programme(): return [t[:] for t in PROGRAM]

def admit(request):
    assert type(request) is dict and set(request)=={
        'configuration','revision','source_files','source_sha256',
        'configuration_sha256','seed','kind','export','role','input','grant','grant_seal'}
    assert boundary.canonical(request['configuration'])==boundary.canonical(CONFIG)
    assert request['configuration_sha256']==hashlib.sha256(boundary.canonical(CONFIG)).hexdigest()
    assert type(request['revision']) is str and len(request['revision'])==40 and all(c in '0123456789abcdef' for c in request['revision'])
    assert type(request['seed']) is int and request['seed'] in CONFIG['primary']+CONFIG['unseen']
    assert request['kind'] in ('generate','audit') and request['export'] in ('original','restored')
    assert request['kind']!='audit' or request['export']=='original'
    role=f"{request['export']}:{request['seed']}:benchmark:{request['kind']}"
    assert request['role']==role
    assert request['input'] is None if request['kind']=='generate' else type(request['input']) is dict
    assert type(request['source_files']) is dict and REQUIRED<=set(request['source_files'])
    assert request['source_sha256']==hashlib.sha256(boundary.canonical(request['source_files'])).hexdigest()
    endpoint='proof' if request['kind']=='audit' else 'raw'
    boundary.validate_grant(request,request['source_sha256'],endpoint)
    assert request['grant']['limit']==(1024**2 if endpoint=='proof' else 16*1024**2)
    return role

def main():
    request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),1024**2),object_pairs_hook=boundary.pairs)
    role=admit(request);root=Path.cwd();pins=request['source_files']
    assert boundary.verify_source(root,pins)==request['source_sha256']
    from experiments import evidence_write_grant68 as transport
    counts=dict(genesis=0,ordinary_steps=0)
    if request['kind']=='audit':
        from experiments import digital_cognitive76_referee as referee
        batch=boundary.read_spec(request['input'],16*1024**2)
        assert set(batch)=={'version','seed','histories','updater_supplied','learning_claim','stage_credit'}
        assert batch['version']==VERSION and type(batch['seed']) is int and batch['seed']==request['seed']
        assert batch['updater_supplied'] is True and batch['learning_claim'] is False and batch['stage_credit'] is False
        assert [x['role'] for x in batch['histories']]==list(ARMS)
        proofs=[]
        for item in batch['histories']:
            assert set(item)=={'role','row'}
            row=item['row'];assert row['route']==NAME and row['seed']==request['seed'] and row['control_mode']==item['role']
            proofs.append(dict(role=item['role'],row_sha256=referee.h(row),summary=referee.audit(row,PROGRAM)))
        value=dict(version=VERSION+'-PROOF',seed=request['seed'],proofs=proofs,
                   updater_supplied=True,learning_claim=False,stage_credit=False)
        assert 'experiments.digital_cognitive76_world' not in sys.modules
        assert 'experiments.digital_cognitive76_history' not in sys.modules
    else:
        from experiments import digital_cognitive76_world as kernel
        assert NAME not in kernel.PROGRAMS
        # Explicit benchmark-only apparatus; all blind source programmes remain
        # unchanged. No actor-specific repair or outcome-dependent registration.
        kernel.PROGRAMS[NAME]=programme()
        from experiments import digital_cognitive76_history as producer
        old_init,old_step=kernel.World.__init__,kernel.World.step
        def counted_init(self,*args,**kwargs):
            counts['genesis']+=1;return old_init(self,*args,**kwargs)
        def counted_step(self):
            result=old_step(self)
            if result:counts['ordinary_steps']+=1
            return result
        kernel.World.__init__,kernel.World.step=counted_init,counted_step
        try:
            value=dict(version=VERSION,seed=request['seed'],
                       histories=[dict(role=arm,row=producer.history(request['seed'],NAME,arm)) for arm in ARMS],
                       updater_supplied=True,learning_claim=False,stage_credit=False)
            assert counts['genesis']==3 and counts['ordinary_steps']==sum(x['row']['final']['tick'] for x in value['histories'])
        except BaseException as error:
            print(boundary.canonical(dict(failed=True,role=role,counts=counts,error=repr(error),partial_state_unavailable=True)).decode(),file=sys.stderr)
            raise
        finally:
            kernel.World.__init__,kernel.World.step=old_init,old_step
            del kernel.PROGRAMS[NAME]
    boundary.module_origins(root,pins)
    assert boundary.verify_source(root,pins)==request['source_sha256']
    receipt=transport.record(request['grant'],request['grant_seal'],request['source_sha256'],request['configuration_sha256'],role,value)
    assert boundary.verify_source(root,pins)==request['source_sha256']
    print(boundary.canonical(dict(role=role,revision=request['revision'],counts=counts,
                                 receipt=receipt,source_sha256=request['source_sha256'],
                                 configuration_sha256=request['configuration_sha256'],
                                 updater_supplied=True,learning_claim=False,stage_credit=False)).decode())

if __name__=='__main__':main()
