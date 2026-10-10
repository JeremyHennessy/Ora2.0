"""Independent rational reaction interpreter and admission falsification audit."""
import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

def step(state,action,arm,contact):
    bath,load,species=state;name,direction=action
    potentials={'F':6,'I':4,'P':0}
    source,dest=('F','I') if name=='capture' else ('I','P')
    if direction<0:source,dest=dest,source
    if species!=source:return None
    delta_load=2*direction if name=='work' else 0
    delta_heat=potentials[source]-potentials[dest]-delta_load
    target=(bath+delta_heat,load+delta_load,dest)
    if target[0]<0 or target[1]<0:return None
    weights={'candidate':{0:2,1:32},'independent':{0:17,1:17},'shuffled':{0:32,1:2}}
    prefactor=Fraction(weights[arm][contact] if name=='work' else 4,64)
    if delta_heat<0:prefactor/=2**(-delta_heat)
    return target,prefactor

def encode(s):return [s[0],s[1],('F','I','P').index(s[2])]

def catalogue(arm,contact):
    digest=hashlib.sha256();count=0
    for species in ('F','I','P'):
        for bath in range(33):
            for load in range(33):
                state=(bath,load,species)
                for kind in ('capture','decay','work'):
                    for sign in (-1,1):
                        action=(kind,sign);result=step(state,action,arm,contact)
                        if result is None:continue
                        target,rate=result;back=step(target,(kind,-sign),arm,contact)
                        if back is None or back[0]!=state:raise ValueError('Missing physical reverse')
                        energy={'F':6,'I':4,'P':0}
                        if bath+load+energy[species]!=target[0]+target[1]+energy[target[2]]:raise ValueError('Energy creation')
                        if Fraction(2**bath)*rate!=Fraction(2**target[0])*back[1]:raise ValueError('Unpriced kinetic drive')
                        count+=1;digest.update(json.dumps([encode(state),list(action),encode(target),[rate.numerator,rate.denominator]],separators=(',',':')).encode()+b'\n')
    return dict(arm=arm,contact=contact,states=3267,edges=count,edge_sha256=digest.hexdigest())

def certificate(n,arm,contact):
    bath=8;load=0;matter=['F']*n;states=[[8,0,[0]*n]];events=[];fresh=thermal=0
    for identity in range(n):
        for number,action in enumerate((('capture',1),('work',1),('decay',-1),('work',1))):
            result=step((bath,load,matter[identity]),action,arm,contact)
            if result is None:raise ValueError('Unfunded witness')
            (bath,load,species),rate=result;matter[identity]=species
            event=dict(token=identity,action=list(action),rate=[rate.numerator,rate.denominator])
            if number==1:event['output_origin']='fresh-fuel';fresh+=2
            if number==3:event['output_origin']='thermal-reactivation';thermal+=2
            if bath+load+sum({'F':6,'I':4,'P':0}[x] for x in matter)!=6*n+8:raise ValueError('Ledger conservation')
            events.append(event);states.append([bath,load,[('F','I','P').index(x) for x in matter]])
    return dict(tokens=n,arm=arm,contact=contact,states=states,events=events,total_energy=6*n+8,material_units=n,fresh_fuel_work=fresh,thermal_work=thermal,gross_work=load,final_heat=bath,claimed_ceiling=2*n,conservation_ceiling=6*n,bound_falsified=load>2*n and bath>=8)

def audit(data,revision):
    expected=dict(schema='channel01',source_revision=revision,natural_worlds=0,controlled_certificates=48,full_costs_known=False,local_grids=[catalogue(a,b) for a in ('candidate','independent','shuffled') for b in (0,1)],certificates=[certificate(n,a,b) for n in range(1,9) for a in ('candidate','independent','shuffled') for b in (0,1)])
    if data!=expected:raise ValueError('Full unit-grid/rate/token/output-provenance mismatch')
    if not all(r['bound_falsified'] for r in data['certificates']):raise ValueError('Incomplete falsification')
    return dict(verified=True,source_revision=revision,controlled_certificates=48,natural_worlds=0,local_states=sum(r['states'] for r in data['local_grids']),local_edges=sum(r['edges'] for r in data['local_grids']),proposed_gross_output_ceiling_falsified=True,fresh_fuel_output_per_token=2,additional_thermal_output_per_token=2,initial_heat_capital_preserved=True,conservation_ceiling_per_token=6,exact_mean_benefit_demonstrated=False,full_assembly_transport_renewal_costs_known=False,mechanism_admitted=False,primary_pass=False,self_maintenance_demonstrated=False,reason='Reverse intermediate decay creates a paid thermal-to-work route; 2N is not a bound on total usable work. Full organizational costs are also absent. Stop prototype before natural dynamics.',next='Choose a separately registered complete conversion/assembly law; account for every reversible output path and complete renewal costs before sampling')

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:print(json.dumps(audit(json.loads(Path(a.input).read_bytes()),a.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,TypeError) as error:print(json.dumps(dict(verified=False,error=str(error))));raise SystemExit(2)

if __name__=='__main__':main()
