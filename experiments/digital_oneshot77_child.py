"""Separately authored paid capacity benchmark, never a blind candidate.

The generic updater was registered before primary outcomes. It contains no
target map; the actor's own negative feedback gates revisions of blank models.
"""
import hashlib
import json
import sys
from pathlib import Path
from experiments import digital_cognitive76_child as boundary
from experiments.digital_oneshot77_source import manifest,programmes,LEARNER,REFERENCES,PRIMARY,UNSEEN

VERSION='DIGITAL-ONESHOT77-PANEL-v1'
ARMS=tuple(REFERENCES)+('intact','model_disabled','history_misbound')
CONFIG=dict(version=VERSION,contract_sha256='08b1ff916c7f5f7ef9374e75603388f4cfedae5cfcf9b91d91dbb35175ec9e5e',primary=list(PRIMARY),unseen=list(UNSEEN),controls=['intact','model_disabled','history_misbound'],references=list(REFERENCES),horizon=512,formation=52,startup=32,programme_sha256=hashlib.sha256(boundary.canonical(manifest())).hexdigest(),updater='AUTHOR-SUPPLIED generic own-error cue model',acquired_models='initially all zero',primary_bank_changed=False)
REQUIRED=boundary.REQUIRED|{'experiments/digital_oneshot77_'+x+'.py' for x in ('source','controls','world','referee','history','child')}
def membership(role):return (role,'intact') if role in REFERENCES else ('supplied_cognitive',role)

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
    role=f"{request['export']}:{request['seed']}:oneshot77:{request['kind']}"
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
        from experiments import digital_oneshot77_referee as referee
        batch=boundary.read_spec(request['input'],16*1024**2)
        assert set(batch)=={'version','seed','histories','updater_supplied','learning_claim','stage_credit'}
        assert batch['version']==VERSION and type(batch['seed']) is int and batch['seed']==request['seed']
        assert batch['updater_supplied'] is True and batch['learning_claim'] is False and batch['stage_credit'] is False
        assert [x['role'] for x in batch['histories']]==list(ARMS)
        proofs=[]
        for item in batch['histories']:
            assert set(item)=={'role','row'}
            row=item['row'];route,mode=membership(item['role']);assert row['route']==route and row['seed']==request['seed'] and row['control_mode']==mode
            proofs.append(dict(role=item['role'],row_sha256=referee.h(row),summary=referee.audit(row,programmes()[route])))
        value=dict(version=VERSION+'-PROOF',seed=request['seed'],proofs=proofs,
                   updater_supplied=True,learning_claim=False,stage_credit=False)
        assert 'experiments.digital_oneshot77_world' not in sys.modules
        assert 'experiments.digital_oneshot77_history' not in sys.modules
    else:
        from experiments import digital_oneshot77_world as kernel
        from experiments import digital_oneshot77_history as producer
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
                       histories=[dict(role=arm,row=producer.history(request['seed'],*membership(arm))) for arm in ARMS],
                       updater_supplied=True,learning_claim=False,stage_credit=False)
            assert counts['genesis']==9 and counts['ordinary_steps']==sum(x['row']['final']['tick'] for x in value['histories'])
        except BaseException as error:
            print(boundary.canonical(dict(failed=True,role=role,counts=counts,error=repr(error),partial_state_unavailable=True)).decode(),file=sys.stderr)
            raise
        finally:
            kernel.World.__init__,kernel.World.step=old_init,old_step
    boundary.module_origins(root,pins)
    assert boundary.verify_source(root,pins)==request['source_sha256']
    receipt=transport.record(request['grant'],request['grant_seal'],request['source_sha256'],request['configuration_sha256'],role,value)
    assert boundary.verify_source(root,pins)==request['source_sha256']
    print(boundary.canonical(dict(role=role,revision=request['revision'],counts=counts,
                                 receipt=receipt,source_sha256=request['source_sha256'],
                                 configuration_sha256=request['configuration_sha256'],
                                 updater_supplied=True,learning_claim=False,stage_credit=False)).decode())

if __name__=='__main__':main()
