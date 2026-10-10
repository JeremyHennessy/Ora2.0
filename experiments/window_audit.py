"""Independent full-world audit plus phase inventory and charge interpreter."""
import argparse, hashlib, json
from .assemble_audit import audit as original_audit, interpret, thermal

LAW='da7f2afc6b43025845aa78a6846af9ec769a4075'
NAMES=('candidate','independent','shuffled')
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()

def inspect(record):
    first={};phase=record['states'][0][:4];tokens=[0]*10
    for e in record['events']:
        k,j,d=e['action']
        if k in ('assemble','drive','waste') and j not in first:first[j]=e
        if e['step']<2048:
            phase=e['after']
            if k in ('assemble','drive','waste'):tokens[j]=1 if d==1 else 0
    virgin=sorted(j for j in range(10) if j not in first or first[j]['step']>=2048)
    destruction=[e for e in record['events'] if e['action'][0]=='damage'];assert len(destruction)<=1
    loss=bool(destruction);charge=None;ends=[];fates=[];gross=returns=rebuiltgross=0
    available=set(virgin)
    if loss:
        for e in record['events']:
            if e['step']<2048:continue
            kind,j,d=e['action']
            if kind in ('assemble','drive','waste'):
                new=first[j] is e
                if new:fates.append(dict(token=j,step=e['step'],route=kind,direction=d));available.remove(j)
                if kind=='drive' and d==1 and new:
                    assert charge is None;charge=dict(token=j,step=e['step'],dimer=e['dimer'])
                if kind=='drive' and d==-1 and charge is not None:
                    ends.append(dict(**charge,outcome='reverse_drive',end_step=e['step']));charge=None
            elif kind=='load':
                if d==1:
                    gross+=2;rebuiltgross+=2*int(e['dimer']==record['first_rebuilt'])
                    if charge is not None:ends.append(dict(**charge,outcome='fresh_load',end_step=e['step']));charge=None
                else:returns+=2
            if kind in ('assemble','passive','damage') and charge is not None:
                ends.append(dict(**charge,outcome='destruction_or_release',end_step=e['step']));charge=None
        if charge is not None:ends.append(dict(**charge,outcome='retained_without_output',end_step=4096))
    certificate=None
    if loss and not virgin and phase[0]>=2:
        damage=destruction[0];v=tuple(damage['after']);states=[list(v)+[thermal(v)]]
        fuel_ids=sorted(j for j in range(10) if tokens[j]==0);assert len(fuel_ids)==phase[0]
        actions=[['passive',0,1]]
        for j in fuel_ids[:2]:actions.extend([['drive',j,1],['relax',0,1],['load',0,1]])
        for action in actions:
            v,rate=interpret(v,action,record['arm']);assert rate>0;states.append(list(v)+[thermal(v)])
        assert v[3]==damage['before'][3]+3 and thermal(v)>=thermal(damage['before'])
        certificate=dict(controlled_only=True,actions=actions,states=states,post_store_gain=3,load_output=4,formation_and_damage_bill=2,post_output_minus_bill=2,registered_fresh_output=0)
    return dict(seed=record['seed'],arm=record['arm'],phase_state=phase,untouched_tokens=virgin,actual_loss=loss,registered_fresh_endpoint_impossible_after_loss=loss and not virgin,first_post_loss_token_fates=fates,fresh_charges=ends,remaining_untouched=sorted(available),observed_post_load_gross=gross,observed_post_reverse_load=returns,observed_first_rebuilt_gross_load=rebuiltgross,controlled_regenerated_fuel_certificate=certificate)

def audit(panel,result,revision):
    old=original_audit(panel,LAW);assert old['verified'] and old['raw_start_worlds']==96
    assert result['schema']=='window01' and result['source_revision']==revision and result['original_source']==LAW
    rows=[inspect(r) for r in panel['records']];assert rows==result['rows']
    totals={}
    for name in NAMES:
        group=[r for r in rows if r['arm']==name]
        totals[name]=dict(worlds=len(group),phase_untouched_total=sum(len(r['untouched_tokens']) for r in group),worlds_with_untouched=sum(len(r['untouched_tokens'])>0 for r in group),actual_losses=sum(r['actual_loss'] for r in group),zero_fresh_opportunity_losses=sum(r['actual_loss'] and len(r['untouched_tokens'])==0 for r in group),fresh_post_loss_charges=sum(len(r['fresh_charges']) for r in group),charge_outcomes={x:sum(c['outcome']==x for r in group for c in r['fresh_charges']) for x in ('fresh_load','reverse_drive','destruction_or_release','retained_without_output')},first_consumption_routes={x:sum(c['route']==x for r in group for c in r['first_post_loss_token_fates']) for x in ('assemble','drive','waste')},observed_post_load_gross=sum(r['observed_post_load_gross'] for r in group),observed_post_reverse_load=sum(r['observed_post_reverse_load'] for r in group),first_rebuilt_load_worlds=sum(r['observed_first_rebuilt_gross_load']>0 for r in group),controlled_regenerated_certificates=sum(r['controlled_regenerated_fuel_certificate'] is not None for r in group))
    assert totals==result['summary'] and result['input_sha256']==hashlib.sha256(encoded(panel)).hexdigest()
    assert result['new_worlds']==0 and not result['old_endpoints_changed'] and not result['self_maintenance_demonstrated']
    return dict(verified=True,source_revision=revision,original_source=LAW,new_worlds=0,original_panel_revalidated=True,old_endpoints_changed=False,summary=totals,self_maintenance_demonstrated=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--result',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:panel=json.load(f)
        with open(a.result,encoding='utf-8') as f:result=json.load(f)
        print(json.dumps(audit(panel,result,a.revision),sort_keys=True))
    except (AssertionError,ValueError,KeyError,IndexError,TypeError) as e:print(json.dumps(dict(verified=False,error=str(e))));raise SystemExit(2)
if __name__=='__main__':main()
