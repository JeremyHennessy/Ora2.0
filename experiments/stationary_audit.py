"""Independent absolute-coordinate backward reward interpreter, no gate import."""
from fractions import Fraction
import json

def expectation(mobility,capture,decay,move):
    # Each state is the absolute catalyst position and intermediate position.
    R=8+4*mobility+capture+decay
    values={(a,i):Fraction(0) for a in range(4) for i in range(4)}
    for time in range(16):
        following={}
        for a,i in values:
            score=sum(4*values[a,(i+h)%4] for h in (-1,1))
            score+=sum(mobility*values[(a+h)%4 if move else a,i] for h in (-1,1))
            score+=2*mobility*values[a,i]
            score+=capture*(1 if i==a else values[a,i])
            # Decay terminates with zero future reward.
            following[a,i]=score/R
        values=following
    assert all(0<=v<=1 for v in values.values())
    return 8*values[0,0]

def calculate():
    rows=[]
    for m in [0,1,4,16]:
      for c in [1,4,16]:
       for loss in [0,1,4,16]:
        moving=expectation(m,c,loss,True);anchored=expectation(m,c,loss,False)
        if m==0:assert moving==anchored
        rows.append(dict(mu=m,k=c,d=loss,tether=str(moving),stationary=str(anchored),stationary_extra_work=str(4*(anchored-moving))))
    return rows

if __name__=='__main__':print(json.dumps(calculate(),sort_keys=True))
