"""Separate explicit ledger-path enumeration and atom/charge interpreter."""
import argparse,hashlib,json
from pathlib import Path
from fractions import Fraction

FORMULAS={'NiS':{'Ni':1,'S':1},'Ni':{'Ni':1},'NiO':{'Ni':1,'O':1},'O':{'O':1},'H+':{'H':1,'q':1},'e-':{'q':-1},'H2S':{'H':2,'S':1},'CO2':{'C':1,'O':2},'CH3SH':{'C':1,'H':4,'S':1},'CH3COSCH3':{'C':3,'H':6,'O':1,'S':1},'H2O':{'H':2,'O':1},'H2':{'H':2},'CH3OH':{'C':1,'H':4,'O':1}}
EQUATIONS=[({'NiS':1,'H+':2,'e-':2},{'Ni':1,'H2S':1}),({'CO2':1,'CH3SH':2,'H+':2,'e-':2},{'CH3COSCH3':1,'H2O':1,'H2S':1}),({'Ni':1,'O':1},{'NiO':1}),({'NiO':1,'H+':2,'e-':2},{'Ni':1,'H2O':1}),({'CO2':1,'H2':3},{'CH3OH':1,'H2O':1})]
def inventory(side):return tuple(sum(count*FORMULAS[s].get(a,0) for s,count in side.items()) for a in ('Ni','C','H','O','S','q'))
def check_atoms(left,right):assert inventory(left)==inventory(right)
def ledger(n,t,h,e):
    initial=(0,n,t,h,e,0,0);stack=[initial];seen={initial};best=postbest=0
    original=inventory({'NiS':1,'O':1,'CO2':n,'CH3SH':t,'H+':h,'e-':e})
    while stack:
        stage,c,thiol,protons,electrons,pre,post=stack.pop();products=pre+post
        material={'CO2':c,'CH3SH':thiol,'H+':protons,'e-':electrons,'CH3COSCH3':products,'H2S':products+int(stage>0),'H2O':products+int(stage==3)}
        material[{0:'NiS',1:'Ni',2:'NiO',3:'Ni'}[stage]]=1
        if stage<2:material['O']=1
        assert inventory(material)==original
        if stage==3 and post>0:best=max(best,products);postbest=max(postbest,post)
        following=[]
        if stage in (0,2) and min(protons,electrons)>=2:following.append((stage+1,c,thiol,protons-2,electrons-2,pre,post))
        if stage in (1,3) and c>=1 and thiol>=2 and min(protons,electrons)>=2:following.append((stage,c-1,thiol-2,protons-2,electrons-2,pre+(stage==1),post+(stage==3)))
        if stage==1 and pre>=1:following.append((2,c,thiol,protons,electrons,pre,post))
        for s in following:
            if s not in seen:seen.add(s);stack.append(s)
    return [n,t,h,e,best,postbest]
def methanol(n,h):
    start=(n,h,0);todo=[start];seen={start};best=0
    while todo:
        c,g,p=todo.pop();assert inventory({'CO2':c,'H2':g,'CH3OH':p,'H2O':p})==inventory({'CO2':n,'H2':h})
        best=max(best,p)
        if c and g>=3:
            s=(c-1,g-3,p+1)
            if s not in seen:seen.add(s);todo.append(s)
    return [n,h,best]
def audit(r,revision):
    f=Path(__file__).resolve().parents[1]/'data/mineral01/source-facts.json';facts=json.loads(f.read_bytes())
    assert r['schema']=='mineral01-admission' and r['source_revision']==revision and r['source_facts_sha256']==hashlib.sha256(f.read_bytes()).hexdigest()
    assert r['natural_worlds']==0 and r['physical_mechanism_installed'] is False
    assert r['reactions']==[dict(left=l,right=x) for l,x in EQUATIONS]
    for l,x in EQUATIONS:check_atoms(l,x)
    ni=[ledger(n,t,h,e) for n in range(5) for t in range(9) for h in range(13) for e in range(13)];fe=[methanol(n,h) for n in range(5) for h in range(13)]
    assert r['ni_rows']==ni and r['fe_rows']==fe
    flow=facts['ni']['flow_ml_per_min']*(facts['ni']['electrolysis_days']*1440+facts['ni']['prior_flow_minutes_minimum'])
    assert Fraction(r['flow']['ni_minimum_litres'])==Fraction(flow,1000)
    rate=facts['fe']['flow_ml_per_min'];total=Fraction(rate*60,1000);parts=facts['fe']['co2_volume_parts']+facts['fe']['h2_volume_parts']
    assert r['flow']==dict(ni_minimum_litres=str(Fraction(flow,1000)),fe_illustrative_hour_total_litres=str(total),fe_illustrative_hour_co2_litres=str(total*facts['fe']['co2_volume_parts']/parts),fe_illustrative_hour_h2_litres=str(total*facts['fe']['h2_volume_parts']/parts),moles_inferred=False)
    assert r['work']==dict(ni_terminal_work_J=None,fe_terminal_work_J=None,usable_output_J=None,full_repair_cost_J=None,reference_potential_alone_sufficient=False,temperature_alone_sufficient=False)
    assert r['unknowns']=={k:facts[k]['unknown_for_ora'] for k in ('ni','fe')}
    assert r['admission_passed'] is False and r['classification']=='NOT_ADMITTED_MISSING_CALIBRATION' and r['paper_hypotheses_disproved'] is False
    return dict(verified=True,source_revision=revision,natural_worlds=0,conditional_accounting_cases=len(ni)+len(fe),ni_cases=len(ni),fe_cases=len(fe),ni_paired_use_possible_cases=sum(x[4]>0 for x in ni),ni_maximum_total_products=max(x[4] for x in ni),ni_maximum_post_products=max(x[5] for x in ni),fe_maximum_products=max(x[2] for x in fe),flow=r['flow'],work=r['work'],missing_calibration=r['unknowns'],admission_passed=False,classification=r['classification'],source_papers_reproduced=False,self_maintenance_demonstrated=False)
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:r=json.load(f)
        print(json.dumps(audit(r,a.revision),sort_keys=True))
    except (AssertionError,KeyError,ValueError,TypeError) as e:print(json.dumps(dict(refused=True,error=str(e))));raise SystemExit(2)
if __name__=='__main__':main()
