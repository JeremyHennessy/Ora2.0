"""Necessary finite input capacity only. No engine or controller implemented."""
from fractions import Fraction
import json
import math


def entropy(probabilities):
    return -sum(float(p)*math.log2(float(p)) for p in probabilities if p)


def counts(n,q):
    # Count-distribution dynamic programming; independent audit enumerates words.
    states={(0,0):Fraction(1,2),(1,1):Fraction(1,2)}
    for _ in range(n-1):
        following={}
        for (last,k),p in states.items():
            for bit in (0,1):
                key=(bit,k+bit)
                following[key]=following.get(key,Fraction())+p*(q if bit!=last else 1-q)
        states=following
    return [sum((p for (_,k),p in states.items() if k==i),Fraction()) for i in range(n+1)]


def census():
    rows=[]
    for n in (8,12):
        for numerator in range(5):
            q=Fraction(numerator,4);h=entropy((q,1-q))
            joint=1+(n-1)*h;capacity=n-joint
            mass=counts(n,q)
            shuffled=entropy(mass)+sum(float(p)*math.log2(math.comb(n,k)) for k,p in enumerate(mass))
            for bath in (4,8,16):
                rows.append(dict(n=n,q_numerator=numerator,q_denominator=4,bath_cap=bath,
                    joint_entropy=joint,input_capacity=capacity,work_ceiling=min(bath,capacity),
                    block2_ceiling=min(bath,n/2*(1-h)),block4_ceiling=min(bath,3*n/4*(1-h)),
                    full_block_ceiling=min(bath,capacity),shuffled_entropy=shuffled,
                    shuffled_input_ceiling=min(bath,max(0,n-shuffled)),
                    unknown_costs=['formation','memory_reset','input_transport','coupling',
                                   'load_conversion','upkeep','release_and_reconstruction'],
                    measured_work=None,mechanism_admitted=False))
    return dict(schema='correlation-capacity01-v1',rows=rows,natural_worlds=0,
                classification='INFORMATION_CAPACITY_ONLY_NOT_ADMITTED',
                full_input_shuffle_equal_resource_control=False,controller_installed=False)


if __name__=='__main__':print(json.dumps(census(),sort_keys=True,separators=(',',':')))
