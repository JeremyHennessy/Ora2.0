"""Independent task transition interpreter; never imports kernel or witnesses."""
import hashlib,json

def h(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def audit(row):
    orientation=row['orientation'];mode=row['mode'];assert type(orientation) is int and orientation in (0,1)
    assert mode in ('normal','memory_disabled') and row['flip']==32
    energy=12;heat=0;memory=[0]*8;food=list(range(64));index=0;alive=True;hits=0
    assert len(row['events'])<=256
    for tick,event in enumerate(row['events']):
        assert alive and index<64 and event['tick']==tick
        op=event['op'];arg=event['arg'];assert op in ('sense','read','write','act')
        energy-=1;heat+=1;out=None;packet=None
        if op=='sense':assert arg is None;out=index%2
        elif op=='read':
            assert type(arg) is int and 0<=arg<=7
            out=memory[arg] if mode=='normal' else 0
        elif op=='write':
            assert isinstance(arg,list) and len(arg)==2 and all(type(v) is int for v in arg) and 0<=arg[0]<=7 and 0<=arg[1]<=15
            memory[arg[0]]=arg[1] if mode=='normal' else 0
        else:
            assert type(arg) is int and arg in (0,1)
            correct=(index%2)^orientation^(1 if index>=32 else 0)
            out=int(arg==correct)
            if out:
                packet=index;food.remove(packet);hits+=1
                energy+=20
                if energy>64:heat+=energy-64;energy=64
            index+=1
        alive=energy>0
        expected=dict(tick=tick,op=op,arg=arg,out=out,food=packet,index=index,energy=energy,
                      heat=heat,memory_hash=h(memory),alive=alive)
        assert event==expected and energy+heat+20*len(food)==1292
    final=dict(index=index,energy=energy,heat=heat,memory=memory,food=food,cost=len(row['events']),alive=alive)
    assert row['final']==final and row['state_hash']==h(final)
    return dict(verified=True,orientation=orientation,mode=mode,actions=index,hits=hits,
                instructions=len(row['events']),energy=energy,heat=heat,unconsumed_food=len(food),
                organism_learning=False,ecosystem_worlds=0)

if __name__=='__main__':
    import sys
    rows=json.load(open(sys.argv[1],encoding='utf-8'));assert len(rows)==12
    print(json.dumps([audit(row) for row in rows],sort_keys=True))
