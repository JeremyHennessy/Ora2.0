"""Independent set/position-tuple CONDENSE-01 interpreter, no producer import."""
import argparse
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path

PAIRS=((0,1),(0,2),(1,2))


def convert(s):
    f,a,b,p,w,q=s
    return f,frozenset(i for i in range(3) if a>>i&1),frozenset(PAIRS[j] for j in range(3) if b>>j&1),tuple(p>>i&1 for i in range(3)),w,q


def encode(s):
    f,active,bonds,pos,work,phase=s
    return f,sum(2**i for i in active),sum(2**PAIRS.index(p) for p in bonds),sum(pos[i]*2**i for i in range(3)),work,phase


def heat(s,arm):
    return 35-6*s[0]-2*len(s[1])+int(arm!='affinity-ghost')*len(s[2])-s[4]-(3 if s[5]==0 else 2)


def neighbors(s,i):return {p for p in s[2] if i in p}


def proposals(s,arm):
    f,active,bonds,pos,work,phase=s;result=[]
    for i in range(3):
        if not neighbors(s,i):
            d=-1 if i in active else 1;fresh=active^{i}
            if arm!='passive' and (f<4 and work>0 if d<0 else f>0):
                mark=2 if phase==1 and i==2 and d==1 and neighbors(s,0) else phase
                t=(f-d,fresh,bonds,pos,work+d,mark)
                if heat(t,arm)>=0:result.append(((0,i,d),t))
            t=(f,fresh,bonds,pos,work,phase)
            if heat(t,arm)>=0:result.append(((1,i,d),t))
        pair=PAIRS[i]
        if pair in bonds or set(pair)<=active and pos[pair[0]]==pos[pair[1]]:
            t=(f,active,bonds^{pair},pos,work,phase)
            if heat(t,arm)>=0:result.append(((2,i,-1 if pair in bonds else 1),t))
        group={i};todo=[i]
        while todo:
            current=todo.pop()
            for pair in neighbors(s,current):
                for other in pair:
                    if other not in group:group.add(other);todo.append(other)
        positions=tuple(1-x if j in group else x for j,x in enumerate(pos))
        for d in (-1,1):result.append(((3,i,d),(f,active,bonds,positions,work,phase)))
    if phase==0 and 0 in active and neighbors(s,0) and work>=1:
        result.append(((4,0,1),(f,active-{0},bonds-neighbors(s,0),pos,work,1)))
    return result


def rate(s,action,t,arm):
    c,i,d=action
    others=tuple(j for j in range(3) if j!=i)
    enzyme=arm!='catalysis-ghost' and others in s[2] and s[3][i]==s[3][others[0]]
    b=(1 if enzyme else 4) if c==0 else {1:3,2:2,3:1}[c]
    n=(s[0] if d>0 else 4-s[0]) if c==0 else 4
    return n,b+max(0,heat(s,arm)-heat(t,arm))


def qualifies(s,arm):return s[5]==2 and 0 in s[1] and bool(neighbors(s,0)) and s[4]>=3 and heat(s,arm)>=8


def graph(arm):
    seen={convert((4,0,0,p,0,0)) for p in range(8)};pending=list(seen);count=physical=0;signatures=set()
    while pending:
        s=pending.pop()
        for action,t in proposals(s,arm):
            count+=1
            if action[0]<4:
                physical+=1
                reverse=(action[0],action[1],-action[2])
                choices=[u for a,u in proposals(t,arm) if a==reverse and u[:5]==s[:5]]
                if len(choices)!=1:raise ValueError('Physical reverse absent')
                u=choices[0];n,e=rate(s,action,t,arm);m,k=rate(t,reverse,u,arm);dh=heat(t,arm)-heat(s,arm)
                sig=(s[0],t[0],n,e,m,k,dh)
                if sig not in signatures:
                    signatures.add(sig)
                    ratio=Fraction(comb(4,t[0]),comb(4,s[0]))*(Fraction(2**dh) if dh>=0 else Fraction(1,2**(-dh)))
                    if Fraction(n,96*2**e)/Fraction(m,96*2**k)!=ratio or not 0<Fraction(n,96*2**e)<=Fraction(1,24):
                        raise ValueError('Thermodynamic rate ratio')
            if t not in seen:seen.add(t);pending.append(t)
            if count>3000000 or len(seen)>150000:raise ValueError('Registered exhaustive cap')
    states=sorted(encode(s) for s in seen);endpoints=[s for s in seen if qualifies(s,arm)]
    packed=json.dumps(states,sort_keys=True,separators=(',',':')).encode()
    return dict(states=len(states),edges=count,physical_edges=physical,rate_signatures=len(signatures),
                state_sha256=hashlib.sha256(packed).hexdigest(),endpoint_states=len(endpoints),
                minimum_net_fuel=min((4-s[0] for s in endpoints),default=None))


def witness(value,arm):
    s=convert(value['start'])
    if value['start'] not in [[4,0,0,p,0,0] for p in range(8)]:raise ValueError('Supplied active founder')
    objects=[dict(id=i,atom=i,state='R',parent=None,food=None,alive=True) for i in range(3)]
    current=list(range(3));history=[[i] for i in range(3)]
    fuel=[dict(id=i,state='F',events=[]) for i in range(4)];bonds=[];live={};events=[];states=[list(encode(s))+[heat(s,arm)]]
    for action in value['path']:
        possibilities=dict(proposals(s,arm))
        if tuple(action) not in possibilities:raise ValueError('Unpriced witness transition')
        t=possibilities[tuple(action)];c,i,d=action;event=dict(action=action)
        if c in (0,1,4):
            parent=current[i];objects[parent]['alive']=False;selected=None
            if c==0:
                selected=min(x['id'] for x in fuel if x['state']==('F' if d>0 else 'S'))
                fuel[selected]['state']='S' if d>0 else 'F';fuel[selected]['events'].append(len(events))
            new=len(objects);objects.append(dict(id=new,atom=i,state='M' if c!=4 and d>0 else 'R',parent=parent,food=selected,alive=True));current[i]=new;history[i].append(new)
            event.update(parent=parent,object=new,food=selected)
            if c==4:
                lost=[]
                for pair in list(live):
                    if i in PAIRS[pair]:
                        identity=live.pop(pair);bonds[identity]['alive']=False;lost.append(identity)
                event['lost_bonds']=sorted(lost)
        elif c==2:
            if d>0:
                identity=len(bonds);bonds.append(dict(id=identity,atoms=list(PAIRS[i]),objects=[current[j] for j in PAIRS[i]],alive=True,stabilization=int(arm!='affinity-ghost')));live[i]=identity
            else:identity=live.pop(i);bonds[identity]['alive']=False
            event['bond']=identity
        else:
            event['moved_atoms']=sorted(j for j in range(3) if s[3][j]!=t[3][j])
        events.append(event);s=t;states.append(list(encode(s))+[heat(s,arm)])
    expected=dict(start=value['start'],path=value['path'],states=states,events=events,objects=objects,fuel=fuel,bonds=bonds,atom_history=history,total_energy=35,material_units=7,operator_spent=0 if s[5]==0 else 1,endpoint=qualifies(s,arm))
    if value!=expected or not qualifies(s,arm):raise ValueError('Energy/provenance/functional witness')


def hidden_drive():
    # Atom2 is unbound, while atoms0/1 form a local catalytic pair.
    s=convert((2,7,1,0,3,0));action=(0,2,-1);t=dict(proposals(s,'candidate'))[action]
    reverse=(0,2,1);n,e=rate(t,reverse,s,'candidate');m,k=rate(s,action,t,'candidate')
    actual=Fraction(n,96*2**e)/Fraction(m,96*2**(k+3))
    dh=heat(s,'candidate')-heat(t,'candidate')
    expected=Fraction(comb(4,s[0]),comb(4,t[0]))*2**dh
    if actual==expected or actual/expected!=8:raise ValueError('Invalid forward-only shortcut not detected')
    return dict(refused=True,unaccounted_ratio_multiplier=8,energy_ledger_balanced=True,
                explanation='Forward-only barrier decrease creates extra kinetic drive without a priced source')


def audit(value,revision):
    if value['schema']!='condense01' or value['source_revision']!=revision or value['natural_worlds']!=0 or value['raw_position_assignments']!=8:raise ValueError('Frozen manifest')
    arms=('candidate','affinity-ghost','catalysis-ghost','passive')
    if [r['arm'] for r in value['records']]!=list(arms):raise ValueError('Complete arms')
    rows=[]
    for r in value['records']:
        expected=graph(r['arm'])
        if any(r[k]!=v for k,v in expected.items()):raise ValueError('Complete state/rate digest')
        if expected['endpoint_states']:witness(r['witness'],r['arm'])
        elif r['witness'] is not None:raise ValueError('Invented endpoint')
        rows.append(dict(arm=r['arm'],**expected))
    passed=all(r['endpoint_states'] for r in rows[:3]) and rows[3]['endpoint_states']==0
    return dict(verified=True,source_revision=revision,natural_worlds=0,records=rows,
                physical_gate_pass=bool(passed),invalid_forward_only=hidden_drive(),
                autonomous_self_maintenance=False,kinetic_advantage_tested=False,
                decision='RAW-START POSSIBILITY AND THERMODYNAMIC GATE PASS; unscreened dynamics untested' if passed else 'STOP: physical/control gate failed')


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:print(json.dumps(audit(json.loads(Path(a.input).read_bytes()),a.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,TypeError) as e:
        print(json.dumps(dict(verified=False,error=str(e))));raise SystemExit(2)


if __name__=='__main__':main()
