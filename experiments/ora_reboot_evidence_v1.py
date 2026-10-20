"""Capture before, verify after a real OS reboot. Never reboots or starts Ora."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
from experiments.ora_controller_v1 import atomic,boot_token,identity
from experiments.ora_owned_ollama_v1 import listener_pid

ROOT=Path(__file__).resolve().parents[1]


def memories(db):
    return {key:dict(value_sha256=hashlib.sha256(value.encode('utf8')).hexdigest(),issuer=issuer,task=task)
        for key,value,issuer,task in db.execute('SELECT m.key,m.value,p.issuer,p.task FROM memories m JOIN memory_provenance p USING(key)')}


def capture(directory):
    root=Path(directory); destination=root/'before-reboot.json'
    if destination.exists(): raise ValueError('Preserve existing reboot baseline')
    state=json.loads((root/'controller-state.json').read_text())
    if not state['unclean'] or state['phase']!='service-running' or identity(state['owner']['pid'])!=state['owner']:
        raise ValueError('Live owned controller required before reboot capture')
    with closing(sqlite3.connect((root/'memory.sqlite3').resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
        db.execute('BEGIN')
        baseline=memories(db); cursor=db.execute('SELECT submitted FROM meta').fetchone()[0]
        pending=db.execute("SELECT id,key,kind FROM tasks WHERE state!='done'").fetchall()
        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',): raise ValueError('Pre-reboot memory integrity failed')
    if not baseline or not pending: raise ValueError('Trusted memories and a pending task required to test both recovery paths')
    value=dict(schema='ORA-PRE-REBOOT-v1',boot=boot_token(),owner=state['owner'],failures=state['failures'],
        recoveries=state['recoveries'],memories=baseline,pending=pending,cursor=cursor,
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    atomic(destination,value); return dict(baseline=str(destination),pending=len(pending),memories=len(baseline),physical_reboot_performed=False)


def verify(directory):
    root=Path(directory); before=json.loads((root/'before-reboot.json').read_text())
    state=json.loads((root/'controller-state.json').read_text())
    checks=dict(boot_changed=boot_token()!=before['boot'],old_owner_gone=identity(before['owner']['pid'])!=before['owner'],
        new_controller=state['owner']!=before['owner'],recovery_classified=state.get('last_recovery')=='boot-changed',
        restart_charged=state['failures']==before['failures']+1 and state['recoveries']==before['recoveries']+1,
        stopped=state['phase']=='stopped' and not state['unclean'] and identity(state['owner']['pid'])!=state['owner'],
        owned_listener_absent=listener_pid() is None,
        source_unchanged=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['source_head'])
    with closing(sqlite3.connect((root/'memory.sqlite3').resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
        after=memories(db)
        checks['trusted_memory_and_provenance_retained']=all(after.get(key)==value for key,value in before['memories'].items())
        checks['integrity']=db.execute('PRAGMA integrity_check').fetchone()==('ok',)
        checks['producer_cursor_not_rolled_back']=db.execute('SELECT submitted FROM meta').fetchone()[0]>=before['cursor']
        checks['pending_tasks_completed']=all(db.execute('SELECT state FROM tasks WHERE id=?',(ident,)).fetchone()==('done',) for ident,key,kind in before['pending'])
        fresh_asks=[ident for ident,key,kind in before['pending'] if kind=='ask' and key not in before['memories']]
        checks['fresh_question_recovered_untrusted']=bool(fresh_asks) and all(
            (row:=db.execute('SELECT result FROM tasks WHERE id=?',(ident,)).fetchone()) and row[0] and json.loads(row[0]).get('trusted') is False for ident in fresh_asks)
        checks['no_project_self_approval']=db.execute("SELECT count(*) FROM memories WHERE key LIKE 'project-review:%'").fetchone()==(0,)
    receipts=[json.loads(p.read_text()) for p in root.glob('model-server-*/native-result.json')]
    checks['model_closed']=bool(receipts) and all(r['post_close_processes_exited'] and r['capture_eof'] and r['usage']['active_before_close']==0 for r in receipts)
    result=dict(schema='ORA-PHYSICAL-REBOOT-REVIEW-v1',physical_reboot_passed=all(checks.values()),checks=checks,
        before_boot=before['boot'],after_boot=boot_token(),source_head=before['source_head'],simulated=False)
    destination=root/'physical-reboot-review.json'
    if destination.exists(): raise ValueError('Preserve existing physical reboot review')
    atomic(destination,result); return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('action',choices=['capture','verify']); parser.add_argument('directory',type=Path)
    args=parser.parse_args(); print(json.dumps((capture if args.action=='capture' else verify)(args.directory)))
