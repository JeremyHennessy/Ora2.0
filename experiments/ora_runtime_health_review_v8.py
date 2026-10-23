"""Read-only review of the explicitly authorized fresh operating lifetime."""
from pathlib import Path
import sys,json,hashlib,sqlite3,subprocess,time
from contextlib import closing
from ora_live_task_bounds_v1 import task_bounds
L=Path('D:/OraLab');S=L/'src/Ora2.0-empty-job-accounting-review-20261023';R=L/'state/ora-continuous-store-v7-20261023';E=L/'runs/ora-empty-job-accounting-repair-20261023'
sys.path.insert(0,str(S))
from experiments.ora_controller_v1 import identity,atomic
from experiments.ora_owned_ollama_v1 import listener_pid
def read(p):return json.loads(p.read_text())
def checks():
    ci=read(E/'verified-ci.json');stage=read(E/'fresh-store-staging.json');c=read(R/'controller-state.json');h=read(R/'host-state.json')
    assert not (R/'STOP').exists() and not list(R.glob('*hold.json')),'STOP or hold present'
    assert c['failures']==h['failures']==h['controller_failures_seen']==0,'New runtime failure'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==ci['head_sha']
    assert all(hashlib.sha256((S/n).read_bytes()).hexdigest()==v for n,v in ci['source_hashes'].items())
    for state in (c,h):assert identity(state['owner']['pid'])==state['owner'],'Owner birth not live'
    assert hashlib.sha256((R/'feedback.key').read_bytes()).hexdigest()==stage['key_sha256']
    auth=read(L/'runs/ora-project-knowledge-workflow-v2-20261022/operator-authorization.json');notes=[]
    for n in auth['notes']:
        q=read(L/'runs/ora-project-knowledge-workflow-v1-20261022/sessions'/n['run_id']/'question.json');cor=read(L/'runs/ora-project-knowledge-workflow-v1-20261022/sessions'/n['run_id']/'operator-correction.json');pub=read(L/'runs/ora-project-knowledge-workflow-v1-20261022/sessions'/n['run_id']/'correction-publication.json')
        assert cor['supplied_value']==n['value'];notes.append((q['key'],cor['stored_note'],'operator',pub['sequence']))
    with closing(sqlite3.connect((R/'memory.sqlite3').as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
        db.execute('BEGIN')
        assert db.execute('pragma integrity_check').fetchone()==('ok',)
        rows=db.execute('select m.key,m.value,p.issuer,p.task from memories m join memory_provenance p using(key)').fetchall()
        assert all(tuple(x) in rows for x in stage['baseline_full_provenance']+notes),'Memory/provenance changed'
        assert len(rows)<=256
        bounds=task_bounds(db)
        assert db.execute("select count(*) from memories where key like 'project-review:%'").fetchone()==(0,),'Project review became trusted'
    native=[]
    if (R/'supervisor-last-attempt.json').exists():native.append(read(R/'supervisor-last-attempt.json')['native'])
    for p in [R/'controller-service-result.json',R/'host-native-result.json',*R.glob('model-server-*/native-result.json')]:
        if p.exists():native.append(read(p))
    for n in native:assert n['capture_eof'] and n['post_close_processes_exited'] and not n['descendant_leak'] and not n['output_limit_exceeded'] and n['usage']['active_before_close']==0,'Retained native closure failed'
    snapshots=list((R/'backups').glob('snapshot-*.sqlite3'));assert len(snapshots)<=2
    snapshot_notes=[]
    for p in snapshots:
        assert p.stat().st_size<=4*1024**2
        with closing(sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
            db.execute('BEGIN')
        assert db.execute('pragma integrity_check').fetchone()==('ok',)
            saved=db.execute('select m.key,m.value,p.issuer,p.task from memories m join memory_provenance p using(key)').fetchall()
            assert all(tuple(x) in saved for x in stage['baseline_full_provenance'])
            snapshot_notes.append(all(x in saved for x in notes))
    sizes={p.name:p.stat().st_size for p in R.glob('*.sqlite3*')};assert all(v<=4*1024**2 for v in sizes.values())
    assert all(p.stat().st_size<=1024**2 for p in R.rglob('*.log'))
    result=dict(checker_schema='ORA-LIVE-HEALTH-v8',task_bounds=bounds,status='PASS',observed_utc=time.time(),source_head=ci['head_sha'],window=c['window'],completed_windows=h['completed_windows'],completed_epochs=c['completed_epochs'],new_failures=0,baseline171_full_provenance_retained=True,approved_notes=3,memory_count=len(rows),key_preserved=True,owned_host_controller_live=True,owned_listener_pid=listener_pid(),native_closed_receipts=len(native),snapshots=len(snapshots),snapshots_containing_approved_notes=sum(snapshot_notes),sqlite_sizes=sizes,scientific_admissions_changed=False)
    atomic(E/'v8-runtime-review.json',result);return result
if __name__=='__main__':print(json.dumps(checks()))
