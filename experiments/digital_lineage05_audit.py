"""All-birth endpoint after independent transition interpretation, no producer import."""
import itertools,json,sys
from experiments.digital_descent04_audit import audit as interpret,clone

ANCESTOR=[0,0,0,6,0,0,10,0,0,12,0,0,4,1,1,13,1,0,7,0,0]

def endpoint(inventory):
    """Inventory must be derived from interpreter-verified paid world events."""
    assert len({x['id'] for x in inventory})==len(inventory)
    by_id={x['id']:x for x in inventory};qualified=[]
    for parent in inventory:
        if parent['parent'] is None or parent['genome']==ANCESTOR:continue
        choices={(p,port) for p,port in parent['successes'] if p!=0}
        if len(parent['successes'])<4:continue
        for left,right in itertools.combinations(sorted(choices),2):
            if left[0]==right[0] or left[1]==right[1]:continue
            if all(port==p%2 for p,port in (left,right)):continue
            for child in inventory:
                if child['parent']!=parent['id'] or child['genome']!=parent['genome']:continue
                if len(child['successes'])<4 or not child['children']:continue
                if left not in child['successes'] or right not in child['successes']:continue
                assert child['id'] in parent['children']
                assert all(k in by_id and by_id[k]['parent']==child['id'] for k in child['children'])
                qualified.append(dict(parent=parent['id'],child=child['id'],sites=[list(left),list(right)],genome=parent['genome']))
    return qualified

def audit(row):
    assert row['version']=='DIGITAL-LINEAGE-05-v1' and row['route'] in ('parity','fixed')
    original=clone(row);original['version']='DIGITAL-DESCENT-04-v1'
    measured=interpret(original)
    inventory=[dict(id=0,parent=None,generation=0,genome=sum(row['genesis_program'],[]),successes=[],children=[],birth_tick=0,writes=[],feedback_reads=0,memory_reads=0,memory_writes=0,self_writes=0)]
    by_id={0:inventory[0]}
    for event in row['final']['events']:
        actor=by_id[event['actor']];opcode=event['decoded'][0]
        for k,op in [('feedback_reads',1),('memory_reads',2),('memory_writes',3),('self_writes',9)]:actor[k]+=int(opcode==op)
        attempt=event.get('attempt')
        if attempt and attempt['success'] and attempt['position']!=0:actor['successes'].append([attempt['position'],attempt['port']])
        if 'birth' in event:
            certificate=event['birth'];c=certificate['child']
            item=dict(id=c['id'],parent=c['parent'],generation=c['generation'],genome=[x[0] for x in c['code']],successes=[],children=[],birth_tick=event['tick'],writes=certificate['write_ids'],feedback_reads=0,memory_reads=0,memory_writes=0,self_writes=0)
            assert c['id'] not in by_id;actor['children'].append(c['id']);inventory.append(item);by_id[c['id']]=item
    # Use immutable tuples inside the endpoint, retain ordinary JSON in evidence.
    prepared=clone(inventory)
    for item in prepared:item['successes']=[tuple(v) for v in item['successes']]
    qualified=endpoint(prepared)
    measured.update(inventory=inventory,qualified=qualified,qualified_pairs=len({(x['parent'],x['child']) for x in qualified}),born_novel=sum(x['genome']!=ANCESTOR for x in inventory[1:]))
    return measured

if __name__=='__main__':
    print(json.dumps([audit(row) for row in json.load(open(sys.argv[1],encoding='utf-8'))],sort_keys=True))
