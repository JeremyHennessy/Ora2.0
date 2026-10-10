"""Read-only phase accessibility diagnosis; never rescores frozen worlds."""
import argparse, hashlib, json
from .assemble_world import transition, heat

ORIGINAL='da7f2afc6b43025845aa78a6846af9ec769a4075'
ARMS=('candidate','independent','shuffled')
def packed(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()

def measure(r):
    virgin=set(range(10));phase=r['states'][0][:4]
    for e in r['events']:
        if e['step']>=2048:break
        phase=e['after'];k,j,d=e['action']
        if k in ('assemble','drive','waste'):virgin.discard(j)
    available=sorted(virgin);loss=next((e for e in r['events'] if e['action'][0]=='damage'),None)
    allvirgin=set(available);fates=[];charges=[];pending=None;loads=reverse=firstuse=0
    for e in r['events']:
        if e['step']<2048:continue
        k,j,d=e['action']
        if loss is None:continue
        if k in ('assemble','drive','waste'):
            untouched=j in allvirgin
            if untouched:fates.append(dict(token=j,step=e['step'],route=k,direction=d))
            allvirgin.discard(j)
            if k=='drive':
                if d==1 and untouched:
                    assert pending is None;pending=dict(token=j,step=e['step'],dimer=e['dimer'])
                elif d==-1 and pending is not None:
                    charges.append(dict(**pending,outcome='reverse_drive',end_step=e['step']));pending=None
        if k=='load':
            if d==1:
                loads+=2
                if e['dimer']==r['first_rebuilt']:firstuse+=2
                if pending is not None:charges.append(dict(**pending,outcome='fresh_load',end_step=e['step']));pending=None
            else:reverse+=2
        if k in ('assemble','passive','damage') and pending is not None:
            charges.append(dict(**pending,outcome='destruction_or_release',end_step=e['step']));pending=None
    if pending is not None:charges.append(dict(**pending,outcome='retained_without_output',end_step=4096))
    certificate=None
    if loss is not None and not available and phase[0]>=2:
        s=tuple(loss['after']);states=[list(s)+[heat(s)]]
        actions=[('passive',0,1)]+[a for j in (0,1) for a in [('drive',j,1),('relax',0,1),('load',0,1)]]
        for action in actions:
            nxt,rate=transition(s,action,r['arm']);assert rate>0;s=nxt;states.append(list(s)+[heat(s)])
        assert s[3]-loss['before'][3]==3 and heat(s)>=heat(loss['before'])
        certificate=dict(controlled_only=True,actions=[list(a) for a in actions],states=states,post_store_gain=3,load_output=4,formation_and_damage_bill=2,post_output_minus_bill=2,registered_fresh_output=0)
    return dict(seed=r['seed'],arm=r['arm'],phase_state=phase,untouched_tokens=available,actual_loss=loss is not None,registered_fresh_endpoint_impossible_after_loss=loss is not None and not available,first_post_loss_token_fates=fates,fresh_charges=charges,remaining_untouched=sorted(allvirgin) if loss else available,observed_post_load_gross=loads,observed_post_reverse_load=reverse,observed_first_rebuilt_gross_load=firstuse,controlled_regenerated_fuel_certificate=certificate)

def report(panel,revision):
    assert panel['schema']=='assemble01' and panel['mode']=='panel' and panel['source_revision']==ORIGINAL
    rows=[measure(r) for r in panel['records']];assert len(rows)==96
    summary={}
    for a in ARMS:
        group=[r for r in rows if r['arm']==a];assert len(group)==32
        summary[a]=dict(worlds=32,phase_untouched_total=sum(len(r['untouched_tokens']) for r in group),worlds_with_untouched=sum(bool(r['untouched_tokens']) for r in group),actual_losses=sum(r['actual_loss'] for r in group),zero_fresh_opportunity_losses=sum(r['registered_fresh_endpoint_impossible_after_loss'] for r in group),fresh_post_loss_charges=sum(len(r['fresh_charges']) for r in group),charge_outcomes={k:sum(c['outcome']==k for r in group for c in r['fresh_charges']) for k in ('fresh_load','reverse_drive','destruction_or_release','retained_without_output')},first_consumption_routes={k:sum(c['route']==k for r in group for c in r['first_post_loss_token_fates']) for k in ('assemble','drive','waste')},observed_post_load_gross=sum(r['observed_post_load_gross'] for r in group),observed_post_reverse_load=sum(r['observed_post_reverse_load'] for r in group),first_rebuilt_load_worlds=sum(r['observed_first_rebuilt_gross_load']>0 for r in group),controlled_regenerated_certificates=sum(r['controlled_regenerated_fuel_certificate'] is not None for r in group))
    return dict(schema='window01',source_revision=revision,original_source=ORIGINAL,input_sha256=hashlib.sha256(packed(panel)).hexdigest(),rows=rows,summary=summary,new_worlds=0,old_endpoints_changed=False,self_maintenance_demonstrated=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    with open(a.input,encoding='utf-8') as f:panel=json.load(f)
    print(json.dumps(report(panel,a.revision),sort_keys=True))
if __name__=='__main__':main()
