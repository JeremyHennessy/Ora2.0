"""Exact word enumeration, independent of producer entropy/DP formulae."""
from fractions import Fraction
import itertools
import math


def audit(data):
    assert data['schema']=='correlation-capacity01-v1' and data['natural_worlds']==0
    assert data['classification']=='INFORMATION_CAPACITY_ONLY_NOT_ADMITTED'
    assert data['full_input_shuffle_equal_resource_control'] is False
    assert data['controller_installed'] is False
    keys={(n,q,b) for n in (8,12) for q in range(5) for b in (4,8,16)}
    assert len(data['rows'])==30
    assert {(r['n'],r['q_numerator'],r['bath_cap']) for r in data['rows']}==keys
    for r in data['rows']:
        assert r['measured_work'] is None and r['mechanism_admitted'] is False
        assert r['unknown_costs']==['formation','memory_reset','input_transport','coupling',
                                    'load_conversion','upkeep','release_and_reconstruction']
    examined=0;zero=0;changed=0;records={}
    def H(distribution):
        return math.fsum(-float(p)*math.log2(float(p)) for p in distribution if p)
    for n,q_num in itertools.product((8,12),range(5)):
        q=Fraction(q_num,4);word_mass={};weight_mass=[Fraction() for _ in range(n+1)]
        for word in itertools.product((0,1),repeat=n):
            examined+=1;p=Fraction(1,2)
            for left,right in zip(word,word[1:]):p*=q if left!=right else 1-q
            word_mass[word]=p;weight_mass[sum(word)]+=p
        assert sum(word_mass.values())==1
        assert all(sum(p for word,p in word_mass.items() if word[i])==Fraction(1,2) for i in range(n))
        joint=H(word_mass.values());input_capacity=n-joint
        shuffled=H(weight_mass[sum(word)]/math.comb(n,sum(word)) for word in word_mass)
        assert shuffled+1e-10>=joint
        blocks={}
        for size in (2,4):
            marginal={}
            for word,p in word_mass.items():
                block=word[:size];marginal[block]=marginal.get(block,Fraction())+p
            blocks[size]=n/size*(size-H(marginal.values()))
        records[n,q_num]=(joint,input_capacity,shuffled,blocks)
    for r in data['rows']:
        n,q,b=r['n'],r['q_numerator'],r['bath_cap']
        assert r['q_denominator']==4
        joint,cap,shuffle,blocks=records[n,q]
        expected=dict(joint_entropy=joint,input_capacity=cap,work_ceiling=min(b,cap),
                      block2_ceiling=min(b,blocks[2]),block4_ceiling=min(b,blocks[4]),
                      full_block_ceiling=min(b,cap),shuffled_entropy=shuffle,
                      shuffled_input_ceiling=min(b,max(0,n-shuffle)))
        assert all(type(r[k]) in (int,float) and math.isfinite(r[k]) and abs(r[k]-v)<1e-10 for k,v in expected.items())
        assert r['measured_work'] is None and r['mechanism_admitted'] is False
        assert r['unknown_costs']==['formation','memory_reset','input_transport','coupling',
                                    'load_conversion','upkeep','release_and_reconstruction']
        if cap<1e-10:zero+=1
        if shuffle>joint+1e-10:changed+=1
    return dict(verified=True,rows=30,words_examined=examined,zero_input_capacity=zero,
                input_shuffle_changes_resource=changed,full_block_matches_information_ceiling=30,
                actual_control_profitability_verified=False,measured_work=None,
                mechanism_admitted=False,worlds=0,decision='NEEDS_COMPLETE_PAID_APPARATUS_AND_ACTUAL_CONTROLS')
