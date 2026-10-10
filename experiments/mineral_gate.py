"""Primary-source conditional material/charge admission; no physical dynamics."""
import argparse,hashlib,json,re
from fractions import Fraction
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]/'data/mineral01/source-facts.json'
REACTIONS=[({'NiS':1,'H+':2,'e-':2},{'Ni':1,'H2S':1}),
 ({'CO2':1,'CH3SH':2,'H+':2,'e-':2},{'CH3COSCH3':1,'H2O':1,'H2S':1}),
 ({'Ni':1,'O':1},{'NiO':1}),({'NiO':1,'H+':2,'e-':2},{'Ni':1,'H2O':1}),
 ({'CO2':1,'H2':3},{'CH3OH':1,'H2O':1})]
def atoms(formula):
    if formula=='e-':return {'charge':-1}
    result={};body=formula.rstrip('+-')
    for element,n in re.findall(r'([A-Z][a-z]?)(\d*)',body):result[element]=result.get(element,0)+int(n or 1)
    result['charge']=int(formula.endswith('+'))-int(formula.endswith('-'));return result
def vector(side):
    result={}
    for species,count in side.items():
        for atom,n in atoms(species).items():result[atom]=result.get(atom,0)+n*count
    return {k:v for k,v in result.items() if v}
def balanced(left,right):return vector(left)==vector(right)
def nickel(n,t,h,e):
    ceiling=max(0,min(n,t//2,(h-4)//2,(e-4)//2))
    return [n,t,h,e,ceiling if ceiling>=2 else 0,ceiling-1 if ceiling>=2 else 0]
def cell_work(working,counter,charge):
    if any(x is None for x in (working,counter,charge)):return None
    return abs(Fraction(working)-Fraction(counter))*Fraction(charge)
def record(revision):
    assert all(balanced(l,r) for l,r in REACTIONS)
    facts=json.loads(SOURCE.read_bytes());nrows=[nickel(n,t,h,e) for n in range(5) for t in range(9) for h in range(13) for e in range(13)]
    frows=[[n,h,min(n,h//3)] for n in range(5) for h in range(13)]
    ni=facts['ni'];fe=facts['fe'];lower=Fraction(ni['flow_ml_per_min'])*(ni['electrolysis_days']*24*60+ni['prior_flow_minutes_minimum'])/1000
    return dict(schema='mineral01-admission',source_revision=revision,source_facts_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),natural_worlds=0,physical_mechanism_installed=False,
        reactions=[dict(left=l,right=r) for l,r in REACTIONS],ni_rows=nrows,fe_rows=frows,
        flow=dict(ni_minimum_litres=str(lower),fe_illustrative_hour_total_litres='6/5',fe_illustrative_hour_co2_litres='3/10',fe_illustrative_hour_h2_litres='9/10',moles_inferred=False),
        work=dict(ni_terminal_work_J=None,fe_terminal_work_J=None,usable_output_J=None,full_repair_cost_J=None,reference_potential_alone_sufficient=False,temperature_alone_sufficient=False),
        unknowns={key:facts[key]['unknown_for_ora'] for key in ('ni','fe')},admission_passed=False,classification='NOT_ADMITTED_MISSING_CALIBRATION',paper_hypotheses_disproved=False)
def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args();print(json.dumps(record(a.revision),sort_keys=True))
if __name__=='__main__':main()
