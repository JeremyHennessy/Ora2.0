"""Finite advisory configuration-review pilot. No code execution or approvals.

All model arms use the existing isolated mailbox lane with the same selected
document. Only the bounded episode history differs. JSON receipts are evidence,
not an additional authoritative memory database. No scientific-world admission.
"""
import argparse, hashlib, json, random, time
from pathlib import Path

ARMS=('experience','no-history','disrupted-history')
TRAIN=[(120,8000,'60s'),(90,8000,'60s'),(120,17000,'60s'),(120,8000,'30s')]
TEST=[(120,16384,'60s'),(120,16385,'60s'),(119,15000,'60s'),(120,15000,'59s'),
      (120,0,'60s'),(120,8192,'60s'),(121,17000,'30s'),(120,16000,'60s')]

def digest(raw):return hashlib.sha256(raw).hexdigest()
def oracle(case):
    t,b,k=case
    if type(t) is not int or type(b) is not int or b<0 or type(k) is not str:raise ValueError('Invalid configuration fixture')
    return 'ACCEPT' if t==120 and b<=16384 and k=='60s' else 'REJECT'
def response(reply):
    try:
        value=json.loads(reply['answer'])
        if set(value)=={'answer','cite'} and value['answer'] in ('ACCEPT','REJECT') and value['cite']=='D1':return value['answer']
    except (ValueError,TypeError,KeyError):pass
    return 'INVALID'
def question(case,history):
    # History records: configuration, this arm's actual answer, verified score.
    q=('Advisory example-profile check,not live settings. ACCEPT only if timeout and keep_alive match D1 exactly and body bytes do not exceed its cap. Otherwise REJECT. '
       'Fields [timeout_seconds,body_bytes,keep_alive]. Past [fields,own_answer,correct]: '+json.dumps(history,separators=(',',':'))+
       '. New: '+json.dumps(case,separators=(',',':'))+'. answer ACCEPT or REJECT,cite D1.')
    if len(q.encode())>512:raise ValueError('Existing question bound exceeded')
    return q
def visible_history(arm,history):
    if arm=='no-history':return []
    if arm=='experience':return history
    if arm!='disrupted-history':raise ValueError('Unknown arm')
    # Same actual answers and scores, cyclically assigned to the wrong cases.
    # During training length1 has no available disruption; disclosed, unchanged.
    return [[history[(i+1)%len(history)][0],x[1],x[2]] for i,x in enumerate(history)] if history else []
def registration(document_sha256):
    return dict(schema='ORA-PROJECT-WORK-PILOT-v1',arms=list(ARMS),training=TRAIN,reserved_test=TEST,
        document='PREP_SOURCE',document_sha256=document_sha256,total_model_calls=36,wall_seconds=6600,
        feedback='Only deterministic correctness of this arm own training response;never model self-assessment. No test feedback until all test answers are sealed.',
        supplied_mechanisms='Existing local model,explicit task rule,selected example source,caller-owned bounded history and deterministic outcome checker. No weight updates.',
        control_limits='All three model arms ask-isolated,identical document and tasks. No-history removes experience tokens;disrupted keeps records but permutes case associations. Context length is not matched to no-history. Fixed rule oracle is a disclosed upper bound,not learned intelligence.',
        acceptance='Experience test correct>=6/8 and at least2 more correct than EACH no-history and disrupted-history. Report initial training and controls;ceiling or no difference means benefit not demonstrated. No retries or rescoring.',
        stopping='First runtime failure/hold,source/key/provenance change,deadline/call cap,pending competing measurement or uncertain publication stops pilot. Preserve partial attempt;no repeat.',
        authority='Advisory proposals only;no correct/approve tasks,no commands,no code changes,no scientific world execution.',
        prerequisites=['independent retained-note transfer verification PASS','exact candidate Windows CI success and raw source hashes','local oracle/control/budget tests','healthy v7 and preserved174 baseline','sealed registration and code','no previous pilot start','exclusive existing workflow measurement lock'])

def execute(plan,client,out,health):
    """Caller must hold measurement lock and check the sealed admission gate."""
    from experiments.ora_controller_v1 import atomic
    out=Path(out)
    if (out/'started.json').exists():raise ValueError('Prior attempt preserved;no repeat')
    atomic(out/'started.json',dict(utc=time.time(),model_call_cap=36))
    histories={a:[] for a in ARMS};records=[];end=time.monotonic()+plan['wall_seconds']
    try:
        for phase,cases in [('training',plan['training']),('test',plan['reserved_test'])]:
            for i,case in enumerate(cases):
                # Rotate arm order deterministically to reduce temporal confounding.
                for arm in ARMS[i%3:]+ARMS[:i%3]:
                    if len(records)>=36 or time.monotonic()>end-171:raise TimeoutError('Fixed call/wall bound')
                    health()
                    reply=client.ask(question(case,visible_history(arm,histories[arm])),plan['document'],True)
                    ans=response(reply);record=dict(index=len(records),phase=phase,case_index=i,arm=arm,case=case,reply=reply,answer=ans)
                    records.append(record);atomic(out/('answer-%02d.json'%record['index']),record)
                    if phase=='training':histories[arm].append([case,ans,ans==oracle(case)])
        # Score held-out tasks only after every answer is durably sealed.
        scores={a:sum(r['answer']==oracle(r['case']) for r in records if r['phase']=='test' and r['arm']==a) for a in ARMS}
        passed=scores['experience']>=6 and all(scores['experience']>=scores[a]+2 for a in ARMS[1:])
        health();atomic(out/'result.json',dict(completed=True,acceptance_passed=passed,scores=scores,model_calls=len(records),records=records,
            fixed_rule_reference_correct=8,own_history=histories,limits=plan['control_limits'],general_learning_or_evolution_proven=False))
    except BaseException as error:
        atomic(out/'failure.json',dict(error=repr(error),completed_calls=len(records),no_retry=True));raise
