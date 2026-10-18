"""NEW finite source-readiness role; no VM/loader/World/old test invocation."""
import copy,sys
from pathlib import Path
from experiments import digital_pressure71_scientific_child as boundary
from experiments import digital_pilot74_publication_reader_v2 as physical
from experiments import digital_pilot74_finite_requests_v2 as requests
from experiments import digital_pilot74_finite_inventory_v2 as inventory
from experiments import evidence_write_grant68 as transport

def admit(r):
    assert type(r) is dict and set(r)=={'schema','configuration','revision','source_files','source_sha256','configuration_sha256','export','role','source_rows','operator_lock','output'}
    assert r['schema']=='PILOT74-SOURCE-READINESS-REQUEST-v2' and r['export'] in ('original','restored') and r['role']==r['export']+'/prepared'
    assert physical.encode(r['configuration'])==physical.encode(requests.CONFIG) and physical.digest(physical.encode(r['configuration']))==r['configuration_sha256']
    assert type(r['revision']) is str and len(r['revision'])==40 and all(c in '0123456789abcdef' for c in r['revision'])
    assert boundary.verify_source(Path.cwd(),r['source_files'])==r['source_sha256']
    assert r['source_files']=={row['name']:row['sha256'] for row in r['source_rows']}
    plan=inventory.plan(r['source_rows']);assert len(plan['roles'])==26
    item=r['output'];assert type(item) is dict and set(item)=={'grant','seal'}
    boundary.validate_grant(dict(grant=item['grant'],grant_seal=item['seal'],configuration_sha256=r['configuration_sha256'],role=r['role']),r['source_sha256'],'proof')
    assert item['grant']['phase']=='raw' and item['grant']['name']=='receipts/'+r['role']+'.json' and item['grant']['limit']==128*1024
    lock=r['operator_lock'];assert set(lock)=={'path','extent','sha256','device','inode'} and Path(lock['path'])==Path('D:/OraLab/state/operator.lock')
    _,identity=physical.read_exact(lock['path'],{k:lock[k] for k in ('extent','sha256')},16384);assert identity[:2]==(lock['device'],lock['inode'])
    boundary.module_origins(Path.cwd(),r['source_files'])
    assert 'experiments.digital_pressure71_population' not in sys.modules and 'experiments.digital_pilot74_population' not in sys.modules
    return plan

def main():
    try:
        assert len(sys.argv)==4
        raw=physical.external(dict(path=sys.argv[1],extent=int(sys.argv[2]),sha256=sys.argv[3]),1024**2);r=physical.parse(raw,1024**2)
        plan=admit(r);refused=[]
        for key in ('schema','role','configuration_sha256','source_sha256'):
            bad=copy.deepcopy(r);bad[key]='refused-new-readiness-value'
            try:admit(bad)
            except (AssertionError,ValueError):refused.append(key)
            else:raise AssertionError('New source/readiness refusal missing')
        proof=dict(schema='PILOT74-SOURCE-READINESS-PROOF-v2',role=r['role'],source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],new_refusals=refused,counts=dict(genesis=0,ordinary_steps=0,hydrations=0),worlds=0,vm_steps=0,execution_admitted=False)
        item=r['output'];written=transport.record(item['grant'],item['seal'],r['source_sha256'],r['configuration_sha256'],r['role'],proof)
        print(physical.encode(dict(role=r['role'],proof=written,worlds=0,vm_steps=0)).decode('ascii'))
    except BaseException as error:
        print(physical.encode(dict(failed=True,first_exception=repr(error),worlds=0,vm_steps=0)).decode('ascii'),file=sys.stderr);raise

if __name__=='__main__':main()
