"""Independent resource, write-to-birth and instruction/state interpretation."""
import hashlib
import json
import sys

def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def audit_world(row):
    # Reference representation deliberately uses an owned-material set and
    # registered write certificates, rather than the producer's allocator.
    food={i:[i//16,int(h([row['seed'],'food',i])[:8],16)%2] for i in range(64)}
    org={0:dict(id=0,parent=None,generation=0,code=[[v,i] for i,v in enumerate([1,2,4,5,6,12])],mem=[0]*8,mem_units=list(range(6,14)),energy=12,pos=0,pc=0,r0=0,r1=0,read=0,nursery=[],inbox=None)}
    occupied=set(range(14));heat=0;writes={};births=deaths=0;last=-1;maximum=1;next_id=1
    for seq,event in enumerate(row['events']):
        assert event['tick']==seq+1
        ids=sorted(org);actor=next((i for i in ids if i>last),ids[0]);last=actor
        e=org[actor];op=e['code'][e['pc']][0]
        assert (event['actor'],event['op'],event['pc'],event['r0'],event['r1'],event['energy_before'])==(actor,op,e['pc'],e['r0'],e['r1'],e['energy'])
        e['energy']-=1;heat+=1;e['pc']=(e['pc']+1)%6
        neighbors=[org[i] for i in ids if i!=actor and org[i]['pos']==e['pos']]
        if op==1:
            local=sorted(i for i,p in food.items() if p[0]==e['pos']);e['r0']=food[local[0]][1] if local else 2
            assert event['cue']==e['r0']
        elif op==2:
            eligible=sorted(i for i,p in food.items() if p==[e['pos'],e['r0']%2]);e['r1']=int(bool(eligible))
            if eligible:
                assert event['food']==eligible[0];del food[eligible[0]]
                overflow=max(0,e['energy']+20-64);e['energy']+=20-overflow;heat+=overflow
            else:assert 'food' not in event
        elif op==3:e['pos']=(e['pos']+(1 if e['r0']%2 else -1))%4
        elif op==4:
            enabled=row['mode']!='copy_disabled' and e['read']<6 and len(occupied)<512 and e['energy']>=1
            if enabled:
                source=e['code'][e['read']];value=source[0];draw=int(h([row['seed'],'mutation',len(writes)])[:16],16)
                if row['mode']=='mutating' and draw%100<8:value=(value+1+(draw//100)%15)%16
                unit=min(set(range(512))-occupied);w=event['write']
                assert w==dict(source=source,destination=unit,index=e['read'],opcode=value,event_id=seq,mutated=value!=source[0])
                occupied.add(unit);e['nursery'].append([value,unit,e['read'],seq]);e['read']+=1;e['energy']-=1;heat+=1
                writes[seq]=(actor,value,unit)
            else:assert 'write' not in event
        elif op==5:
            if e['read']<6:e['pc']=0
        elif op==6:
            enabled=len(e['nursery'])==6 and e['energy']>=22 and 512-len(occupied)>=8 and len(org)<32
            if enabled:
                b=event['birth'];child=b['child'];units=sorted(set(range(512))-occupied)[:8]
                assert b['write_events']==[g[3] for g in e['nursery']]
                assert all(writes[g[3]]==(actor,g[0],g[1]) for g in e['nursery'])
                expected=dict(id=next_id,parent=actor,generation=e['generation']+1,code=[[g[0],g[1]] for g in e['nursery']],mem=[0]*8,mem_units=units,energy=12,pos=e['pos'],pc=0,r0=0,r1=0,read=0,nursery=[],inbox=None)
                assert child==expected;org[next_id]=json.loads(json.dumps(expected));next_id+=1
                occupied.update(units);e['energy']-=22;heat+=10;e['nursery']=[];e['read']=0;births+=1
            else:assert 'birth' not in event
        elif op==7:e['mem'][e['r0']%8]=e['r1']%16
        elif op==8:e['r0']=e['mem'][e['r1']%8]
        elif op==9:
            if e['energy']>=1:
                i=e['r0']%6;old=e['code'][i][0];new=e['r1']%16
                assert event['self_write']==dict(index=i,old=old,new=new,unit=e['code'][i][1])
                e['code'][i][0]=new;e['energy']-=1;heat+=1
        elif op==10:
            if neighbors and neighbors[0]['inbox'] is None:
                assert event['message']==dict(recipient=neighbors[0]['id'],value=e['r1']%16)
                neighbors[0]['inbox']=e['r1']%16
        elif op==11:
            if e['inbox'] is not None:e['r0']=e['inbox'];e['inbox']=None
        elif op==12:e['pc']=0
        elif op==13:e['r0']=(e['r0']+1)%16
        elif op==14:
            if neighbors and e['energy']>=1 and neighbors[0]['energy']<64:
                assert event['transfer']==neighbors[0]['id'];e['energy']-=1;neighbors[0]['energy']+=1
        elif op==15:heat+=e['energy'];e['energy']=0
        if e['energy']==0:
            units=[g[1] for g in e['code']]+e['mem_units']+[g[1] for g in e['nursery']]
            assert event['death']==units;occupied.difference_update(units);del org[actor];deaths+=1
        else:
            assert event['actor_after']==dict(energy=e['energy'],pc=e['pc'],pos=e['pos'],r0=e['r0'],r1=e['r1'],read=e['read'],program_hash=h(e['code']),genome_hash=h([g[0] for g in e['code']]),memory_hash=h(e['mem']))
        maximum=max(maximum,len(org));energy=sum(o['energy'] for o in org.values())
        assert energy+len(food)*20+heat==1292
        assert event['ledger']==dict(live_energy=energy,food=len(food),heat=heat,free=512-len(occupied),population=len(org))
    final=row['final'];assert {int(k):v for k,v in final['entities'].items()}==org
    assert {int(k):v for k,v in final['food'].items()}==food and final['heat']==heat
    assert final['free']==sorted(set(range(512))-occupied)
    assert (row['births'],row['deaths'],row['maximum_population'],row['ticks'])==(births,deaths,maximum,len(row['events']))
    assert row['state_hash']==h(final) and row['checkpoint_replay']
    return dict(seed=row['seed'],mode=row['mode'],births=births,deaths=deaths,max_population=maximum,mutations=sum(v['write']['mutated'] for v in row['events'] if 'write' in v),descendant_births=sum(v['actor']!=0 for v in row['events'] if 'birth' in v),ticks=row['ticks'])

def audit(data):
    assert data['schema']=='digital-ecosystem01-v1' and not data['persistent_world'] and not data['controller_activated']
    assert [(r['seed'],r['mode']) for r in data['rows']]==[(s,m) for s in range(24000,24004) for m in ('mutating','faithful','copy_disabled')]
    records=[audit_world(r) for r in data['rows']]
    assert all(r['births']==0 for r in records if r['mode']=='copy_disabled')
    assert all(r['mutations']==0 for r in records if r['mode']=='faithful')
    return dict(verified=True,records=records,worlds=12,ancestor_supplied=True,learning_demonstrated=False,evolution_demonstrated=False,repair_demonstrated=False,persistent_world=False)

if __name__=='__main__':print(json.dumps(audit(json.load(open(sys.argv[1],encoding='utf-8'))),sort_keys=True))
