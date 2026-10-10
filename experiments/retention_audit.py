"""Independent absolute-coordinate integer transition interpreter; no producer import."""
from fractions import Fraction
import json

def experiment(mobility,reaction,loss,tethered,initial):
    rate=8+4*mobility+reaction+loss;pool={(0,initial,0,0):1}
    for tick in range(16):
        following={}
        for (a,b,i,status),count in pool.items():
            destinations=[]
            for step in (1,-1):
                destinations.append(((a,b,(i+step)%4,status) if status==0 else (a,b,0,status),4))
                if tethered:destinations.append((((a+step)%4,(b+step)%4,i,status) if status==0 else ((a+step)%4,(b+step)%4,0,status),mobility))
                else:
                    destinations.append((((a+step)%4,b,i,status) if status==0 else ((a+step)%4,b,0,status),mobility))
                    destinations.append(((a,(b+step)%4,i,status),mobility))
            if tethered:destinations.append(((a,b,i,status),2*mobility))
            destinations.extend([((a,b,0,1) if status==0 and i==b else (a,b,i,status),reaction),((a,b,0,2) if status==0 else (a,b,i,status),loss)])
            for state,weight in destinations:
                if weight:following[state]=following.get(state,0)+weight*count
        pool=following
    normalizer=rate**16;assert sum(pool.values())==normalizer
    ends=[Fraction(sum(w for (a,b,i,s),w in pool.items() if (b-a)%4==j),normalizer) for j in range(4)]
    captured=Fraction(sum(w for (a,b,i,s),w in pool.items() if s==1),normalizer)
    assert 0<=captured<=1
    return ends,captured

def calculate():
    results=[]
    for mobility in [0,1,4,16]:
      for reaction in [1,4,16]:
       for loss in [0,1,4,16]:
        bound,p=experiment(mobility,reaction,loss,True,0)
        transitions=[experiment(mobility,reaction,loss,False,initial) for initial in range(4)]
        assert p==transitions[0][1] and bound==[1,0,0,0]
        # Backward reward recursion differs from the forward-distribution producer.
        reward=[Fraction(0)]*4
        for packet in range(8):reward=[transitions[y][1]+sum(transitions[y][0][z]*reward[z] for z in range(4)) for y in range(4)]
        joined=8*p
        assert all(0<=v<=8 for v in reward+[joined])
        if mobility==0:assert joined==reward[0]
        results.append(dict(mu=mobility,k=reaction,d=loss,joined=str(joined),free_colocated=str(reward[0]),free_best=str(max(reward)),shuffle=str(sum(reward)/4),first_packet=str(p),extra_captures=str(joined-max(reward)),extra_work_budget=str(4*(joined-max(reward)))))
    return results

if __name__=='__main__':print(json.dumps(calculate(),sort_keys=True))
