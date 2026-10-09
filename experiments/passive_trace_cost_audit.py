"""Independent passive-price interpreter; no producer or action controller imported."""
import argparse
import hashlib
import json
from pathlib import Path
import random

ARMS=('candidate','fixed-reactive','memory-disabled','shuffled-history');HORIZONS=(0,16,64,128,224,256)
FILES=('experiments/passive_trace_cost.py','experiments/passive_trace_cost_audit.py','docs/TRACE-01-COST-CONTRACT.md')

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))

def require(x,reason):
    if not x:raise ValueError(reason)


def initial(arm):
    gen=random.Random(91004);bits=[gen.getrandbits(1) for _ in range(16)]
    return dict(arm=arm,fuel=list(range(256)),operator=list(range(64)),atoms=list(range(64)),heat=0,active={},traces={},next_trace=0,clocks=0,fixed=bits),gen.getstate()


def transition(s,r,t):
    op,site=r;arm=s['arm'];fuel=s['fuel'];operator=s['operator']
    if op=='write':
        count=1+(arm=='shuffled-history')
        if len(fuel)<2 or len(operator)<count:return dict(kind='unaffordable',operation='write')
        paid=[fuel.pop(0),fuel.pop(0)];pulse=[operator.pop(0) for _ in range(count)];s['heat']+=count
        target=(site+1)%16 if arm=='shuffled-history' else site;key=None
        if arm in ('candidate','shuffled-history') and target not in s['active']:
            key=s['next_trace'];s['next_trace']+=1;s['active'][target]=key
            s['traces'][key]=dict(site=target,born=t,parents=dict(fuel=paid,pulse=pulse),atoms=list(range(4*target,4*target+4)));s['heat']+=1
        else:s['heat']+=2
        return dict(kind='write',site=site,target=target,fuel=paid,pulse=pulse,trace=key)
    if op=='read':
        if not fuel:return dict(kind='unaffordable',operation='read',output=None)
        p=fuel.pop(0);s['heat']+=1;value=s['fixed'][site] if arm=='fixed-reactive' else int(site in s['active']) if arm!='memory-disabled' else 0
        return dict(kind='read',site=site,fuel=p,output=value)
    if op=='erase':
        key=s['active'].get(site)
        if key is not None:del s['active'][site];s['heat']+=1
        return dict(kind='erase',site=site,trace=key)
    require(op=='clock' and site is None,'Only passive requests');s['clocks']+=1
    if fuel:
        p=fuel.pop(0);s['heat']+=1;return dict(kind='clock',fuel=p)
    lost=sorted(s['active'].values());s['heat']+=len(lost);s['active'].clear();return dict(kind='unaffordable',operation='clock',lost=lost)


def trace(path,horizon,arm):
    data=json.loads(Path(path).read_bytes());s,rng=initial(arm)
    require(data['horizon']==horizon and data['arm']==arm and data['initial']==json.loads(canonical(s)) and data['initial_rng']==json.loads(canonical(rng)),'Exact authored unscreened component initialization')
    requests=[['write',i] for i in range(0,16,2)]+[['clock',None] for _ in range(horizon)]+[['read',i] for i in range(16)]+[['erase',i] for i in (0,4,8,12)]+[['read',i] for i in range(16)]+[['write',i] for i in (0,4,8,12)]
    require(len(data['events'])==len(requests),'Full authored request denominator');unpaid_clock=None;reads=[];paid_reads=0;writes=0
    for t,r in enumerate(requests):
        event=transition(s,r,t);require(data['events'][t]==dict(t=t,request=r,event=event,state=json.loads(canonical(s))),'Independent complete transition/ancestry')
        require(len(s['fuel'])+len(s['operator'])+len(s['active'])+s['heat']==320 and s['atoms']==list(range(64)),'Full material/endowment/operator/heat price')
        if r[0]=='read':reads.append(event['output']);paid_reads+=event['kind']=='read'
        if event['kind']=='write':writes+=1
        if r[0]=='clock' and event['kind']=='unaffordable' and unpaid_clock is None:unpaid_clock=s['clocks']
    require(data['final']==json.loads(canonical(s)) and data['final_rng']==json.loads(canonical(rng)),'Complete final state/no extra RNG draws')
    return dict(horizon=horizon,arm=arm,requests=len(requests),paid_reads=paid_reads,read_outputs=reads,paid_writes=writes,first_unpaid_clock=unpaid_clock,final_fuel=len(s['fuel']),final_operator=len(s['operator']),active_potentials=len(s['active']),heat=s['heat'],trace_identities=s['next_trace'])


def audit(folder,source,revision):
    folder,source=Path(folder),Path(source);m=json.loads((folder/'manifest.json').read_bytes());names=[f'{h}-{a}.json' for h in HORIZONS for a in ARMS]
    require(m['schema']=='trace01-cost-v1' and m['revision']==revision and m['arms']==list(ARMS) and m['horizons']==list(HORIZONS) and m['traces']==names,'All precommitted24 slots')
    require(set(m['files_sha256'])==set(names),'Exact raw trace denominator; no extra or missing slots')
    require(m['source_sha256']=={p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in FILES},'Exact component/independent interpreter/contract source')
    require(m['files_sha256']=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.name!='manifest.json'},'Complete raw evidence hashes')
    rows=[trace(folder/f'{h}-{a}.json',h,a) for h in HORIZONS for a in ARMS]
    return dict(schema='trace01-cost-audit-v1',traces=24,requests=sum(r['requests'] for r in rows),rows=rows,authored_component_only=True,controller_activated=False,natural_samples_executed=0,useful_action_demonstrated=False,learning_demonstrated=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);p.add_argument('--source-dir',required=True);p.add_argument('--source-revision',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    try:result=audit(a.output_dir,a.source_dir,a.source_revision)
    except (ValueError,OSError,KeyError,TypeError) as error:print('Rejected:',error);raise SystemExit(2)
    Path(a.report).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
