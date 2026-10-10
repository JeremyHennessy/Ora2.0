"""Separate species-ledger interpreter and DFS census for EXPORT-01 admission."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from functools import lru_cache

NAMES=('candidate','independent','shuffled','bulk-diagnostic')

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()

def thermal(x):
    chemical=6*x[0]
    body={0:0,1:1,2:4,3:3}[x[1]]
    mechanical=2*sum(x[5:7])
    return 68-chemical-body-mechanical

def moves(x,name,only=None):
    """Yield channel, destination, microscopic proposal multiplicity and rate."""
    def make(key, delta, count, barrier=16):
        if only is not None and key!=only:
            return
        y=tuple(a+b for a,b in zip(x,delta))
        if count and 0<=y[0]<=10 and min(y[3:])>=0 and thermal(y)>=0:
            yield key,y,count,Fraction(barrier,64)*Fraction(2)**min(0,thermal(y)-thermal(x))
    af={'candidate':32,'independent':17,'shuffled':2,'bulk-diagnostic':32}[name]
    wf=34-af
    for direction in (-1,1):
        amount=x[0] if direction==1 else 10-x[0]
        if x[1]==(0 if direction==1 else 1) and x[2] in (0,3):
            yield from make(('assemble',0,direction),(-direction,direction,0,0,0,0,0),amount,af)
        if x[1]==(1 if direction==1 else 2):
            yield from make(('drive',0,direction),(-direction,direction,0,0,0,0,0),amount)
        yield from make(('waste',0,direction),(-direction,0,0,0,0,0,0),amount,wf)
        if x[1]==(0 if direction==1 else 1) and x[2] in (0,3):
            yield from make(('passive',0,direction),(0,direction,0,0,0,0,0),1)
        if x[1]==(2 if direction==1 else 3):
            yield from make(('relax',0,direction),(0,direction,0,0,0,0,0),1)
        if x[1]==(3 if direction==1 else 1):
            for site in (0,1):
                if name!='bulk-diagnostic' and x[2]!=3*site:
                    continue
                delta=[0,-2*direction,0,0,0,0,0]
                delta[3+site]=-direction
                delta[5+site]=direction
                count=x[3+site] if direction==1 else x[5+site]
                yield from make(('load',site,direction),delta,count)
    for group in range(4):
        delta=[0]*7
        delta[3+group]=-1
        delta[3+(group^1)]=1
        yield from make(('lhop',group,1),delta,x[3+group])
    for atom in range(2):
        if x[1] and atom:
            continue
        destination=x[2]^(3 if x[1] else 1<<atom)
        yield from make(('hop',atom,1),(0,0,destination-x[2],0,0,0,0),1)

@lru_cache(maxsize=100000)
def weight(s):
    coefficient=math.factorial(10)//math.prod(math.factorial(v) for v in s[3:])
    return math.comb(10,s[0])*coefficient*2**thermal(s)

def census(name):
    # DFS, independently authored stoichiometry and weighted reverse check.
    pending=[(10,0,p,u,10-u,0,0) for u in range(11) for p in range(4)]
    visited=set(pending)
    channels=proposals=0
    while pending:
        x=pending.pop()
        for key,y,count,rate in moves(x,name):
            kind,index,sign=key
            inverse=(kind,index^1 if kind=='lhop' else index,1 if kind in ('lhop','hop') else -sign)
            reverse=next(moves(y,name,inverse),None)
            assert reverse is not None and reverse[1]==x
            assert weight(x)*count*rate==weight(y)*reverse[2]*reverse[3]
            channels+=1
            proposals+=count
            if y not in visited:
                visited.add(y)
                pending.append(y)
            assert len(visited)<=100000 and channels<=2000000
    return dict(arm=name,states=len(visited),directed_channels=channels,labelled_proposals=proposals,
                state_sha256=hashlib.sha256(canonical(sorted(visited))).hexdigest(),
                maximum_stored_work_with_heat_protected=max(2*sum(x[5:]) for x in visited if thermal(x)>=8),
                complete_reverse_and_balance_checks=True)

def verify_certificate(record):
    name=record['arm']
    fuel=[True]*10
    unused=[True]*10
    carriers=[{'site':0,'work':0} for _ in range(10)]
    phase=position=0
    provenance=None
    gross=debits=postgross=postdebits=0
    loss=False
    initial_loss_heat=initial_loss_work=None
    def aggregate():
        counts=[sum(v['site']==i%2 and v['work']==(2 if i>=2 else 0) for v in carriers) for i in range(4)]
        return (sum(fuel),phase,position,*counts)
    for row in record['rows']:
        old=aggregate()
        assert row['before']==list(old)
        kind,label,sign=row['action']
        if kind=='damage':
            assert phase and label==0 and position==0 and carriers[0]=={'site':0,'work':2} and not loss
            initial_loss_heat=thermal(old)
            initial_loss_work=sum(v['work'] for v in carriers)
            carriers[0]['work']=0
            phase=0
            provenance=None
            loss=True
            debits+=2
            postdebits+=2
        else:
            group=carriers[label]['site']+(2 if carriers[label]['work'] else 0) if kind=='lhop' else carriers[label]['site'] if kind=='load' else 0
            channel=(kind,group,sign)
            expected=next((v for v in moves(old,name) if v[0]==channel),None)
            assert expected is not None
            phase,position=expected[1][1:3]
            if kind in ('assemble','drive','waste'):
                assert fuel[label]==(sign==1)
                if kind=='drive':
                    provenance=unused[label] if sign==1 else None
                fuel[label]=sign==-1
                unused[label]=False
            if kind=='lhop':
                carriers[label]['site']=1-carriers[label]['site']
            if kind=='load':
                assert carriers[label]['work']==(0 if sign==1 else 2)
                carriers[label]['work']=2 if sign==1 else 0
                work=2*sign if sign==-1 or provenance else 0
                gross+=work
                postgross+=work*int(loss)
                provenance=None if sign==1 else False
            cost=6*sign if kind=='assemble' else sign if kind=='passive' else 0
            debits+=cost
            postdebits+=cost*int(loss)
            assert aggregate()==expected[1]
        now=aggregate()
        assert row['after']==list(now) and row['heat']==thermal(now)>=0
        assert 6*sum(fuel)+{0:0,1:1,2:4,3:3}[phase]+sum(v['work'] for v in carriers)+thermal(now)==68
    work=sum(v['work'] for v in carriers)
    expected_score=dict(whole_stored_work=work,post_store_gain=work-initial_loss_work,
                        fresh_gross_work=gross,formation_damage_bill=debits,linked_surplus=gross-debits,
                        post_fresh_work=postgross,post_bill=postdebits,post_linked_surplus=postgross-postdebits,
                        final_heat=thermal(aggregate()),predamage_heat=initial_loss_heat,
                        endpoint=bool(work>0 and work-initial_loss_work>0 and gross-debits>0 and postgross-postdebits>0 and thermal(aggregate())>=max(8,initial_loss_heat) and phase==1))
    assert record['score']==expected_score
    assert record['load_sites']==[v['site'] for v in carriers]
    assert record['loaded']==[bool(v['work']) for v in carriers]
    assert record['tokens']==[int(not v) for v in fuel] and record['virgin']==unused
    assert record['controlled_only'] is True
    assert record['resource_yoked_repair_state']==next(row['after'] for row in record['rows'] if row['action'][0]=='damage')
    assert expected_score['endpoint']
    return expected_score

def audit(record,revision):
    assert record['schema']=='export01-admission' and record['source_revision']==revision and record['natural_worlds']==0
    assert [v['arm'] for v in record['graphs']]==list(NAMES)
    assert [v['arm'] for v in record['certificates']]==list(NAMES)
    scores=[verify_certificate(v) for v in record['certificates']]
    for item in record['graphs']:
        assert census(item['arm'])==item
    assert all(scores[0]==v for v in scores)
    yoked=[v['resource_yoked_repair_state'] for v in record['certificates']]
    assert all(yoked[0]==v for v in yoked)
    assert len({v['state_sha256'] for v in record['graphs']})==1
    return dict(schema='export01-decision',source_revision=revision,admission_passed=True,
                natural_worlds=0,all_four_full_censuses_independently_equal=True,
                all_four_controlled_endpoints_pass=True,resource_yoked_repair_state=yoked[0],
                controlled_score=scores[0],graphs=record['graphs'],
                self_maintenance_demonstrated=False,export_kinetic_advantage_demonstrated=False,
                next_decision='Freeze reviewed dynamics and independent full-history interpreter before the unscreened registered panel.')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True)
    p.add_argument('--revision',required=True)
    a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as stream:
            decision=audit(json.load(stream),a.revision)
        print(json.dumps(decision,sort_keys=True))
    except (AssertionError,ValueError,KeyError,TypeError,StopIteration) as error:
        print(json.dumps(dict(verified=False,error=str(error))))
        raise SystemExit(2)

if __name__=='__main__':
    main()
