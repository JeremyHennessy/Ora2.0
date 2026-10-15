"""Pure retained native receipt binding. IO/physical source membership is external."""
import hashlib
import json

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def pairs(items):
    value={}
    for key,item in items:
        assert key not in value;value[key]=item
    return value

def authenticate(request,native,spec,role,configuration,grant_path,file_identity):
    assert type(request) is dict and set(request)=={
        'configuration','source_files','source_sha','config_sha','role','kind','input','grant','seal'}
    assert canonical(request['configuration'])==canonical(configuration)
    assert request['role']==role and request['kind']==role.split(':')[-1]
    assert request['source_sha']==digest(request['source_files'])
    assert request['config_sha']==digest(configuration)
    grant=request['grant'];assert request['seal']==digest(grant)
    assert grant['version']=='sharedlineage68-file-grant-candidate-v1'
    assert (grant['source_sha'],grant['config_sha'],grant['role'])==(request['source_sha'],request['config_sha'],role)
    assert type(spec) is dict and set(spec)=={'path','extent','sha256'}
    assert grant_path==spec['path']
    assert all(type(grant[k]) is int for k in ('device','inode','limit'))
    assert file_identity==(grant['device'],grant['inode'])
    assert type(spec['extent']) is int and 0<spec['extent']<=grant['limit']
    assert grant['limit']==(64 if request['kind']=='generate' else 8)*1024**2
    assert native['exit_code']==0 and type(native['exit_code']) is int
    assert native['timed_out'] is False and native['output_truncated'] is False
    assert native['post_close_processes_exited'] is True
    assert type(native['usage']['active_before_close']) is int and native['usage']['active_before_close']==0
    output=json.loads(native['output'],object_pairs_hook=pairs)
    assert set(output)=={'role','source_sha','config_sha','receipt'}
    assert (output['role'],output['source_sha'],output['config_sha'])==(role,request['source_sha'],request['config_sha'])
    receipt=output['receipt']
    assert set(receipt)=={'grant_sha256','source_sha','config_sha','role','extent','sha256'}
    assert (receipt['grant_sha256'],receipt['source_sha'],receipt['config_sha'],receipt['role'])==(
        request['seal'],request['source_sha'],request['config_sha'],role)
    assert type(receipt['extent']) is int and receipt['extent']==spec['extent']
    assert receipt['sha256']==spec['sha256']
    return dict(role=role,body=spec,source_sha=request['source_sha'],config_sha=request['config_sha'])

def bind_inputs(original_spec,body,proof):
    assert proof['verified'] is True and proof['producer_imported'] is False
    assert proof['evidence_inputs']==original_spec
    assert (proof['seed'],proof['group'],proof['version'],proof['software_only'])==(
        body['seed'],body['group'],body['version'],body['software_only'])
    assert [r['descriptor'] for r in proof['summaries']]==[r['descriptor'] for r in body['records']]
