"""Prepared provenance kernel; normalized views, not a VM integrity referee.

Origins are conservative computational dependencies, never causal learned benefit.
Caller must authenticate raw histories and construct checked views separately.
"""


def trace(views, code_words=27):
    assert type(code_words) is int and 3 <= code_words <= 96 and code_words%3==0
    def person(words):
        return dict(registers=[set(), set()], memory=[set() for _ in range(8)],
                    code=[set(x) for x in words], nursery={}, feedback=set(),
                    pc=set(), cue=set(), position=set(), inbox=None, alive=True)
    people={0:person([set() for _ in range(code_words)])};records=[];last=0
    for e in views:
        tick=e['tick'];identity=e['actor'];op,a,b=e['decoded']
        assert type(tick) is int and tick>last and type(identity) is int
        assert all(type(v) is int and 0<=v<32 for v in (op,a,b))
        last=tick;p=people[identity];assert p['alive']
        pc=e['pc_before'];assert type(pc) is int and 0<=pc<len(p['code'])//3
        instruction=set().union(*p['code'][3*pc:3*pc+3])|p['pc']
        r=p['registers'];used=set(instruction);read=[]
        if op==0:
            p['cue']=p['position']|instruction;r[a%2]=set(p['cue']);used|=p['position']
        elif op==1:
            read=sorted(p['feedback']);r[a%2]=p['feedback']|instruction;used|=p['feedback']
        elif op==2:r[a%2]=p['memory'][b%8]|instruction;used|=p['memory'][b%8]
        elif op==3:p['memory'][a%8]=r[b%2]|instruction;used|=r[b%2]
        elif op==4:r[a%2]=set(instruction)
        elif op==5:
            used|=r[a%2]|r[b%2];r[a%2]=r[a%2]|r[b%2]|instruction
        elif op==6:
            used|=r[a%2]|p['position'];assert type(e['packet_present']) is bool
            # Empty ACT clears feedback; no personally informative origin.
            p['feedback']={(identity,tick)} if e['packet_present'] else set()
        elif op==7:p['pc']|=instruction
        elif op==8:
            used|=r[a%2];p['pc']|=instruction|r[a%2]
        elif op==9:
            w=e['self_write'];index=w['index'];assert type(index) is int and 0<=index<len(p['code'])
            used|=r[a%2]
            old=p['code'][index] if w['old']==w['value'] else set()
            p['code'][index]=old|r[a%2]|instruction
        elif op==10:
            for w in e.get('writes',[]):
                index=w['index'];assert index not in p['nursery'] and 0<=index<len(p['code'])
                p['nursery'][index]=p['code'][index]|instruction
        elif op==11:p['pc']|=instruction
        elif op==13:
            used|=r[a%2];p['position']|=r[a%2]|instruction
        elif op==14 and e.get('message') is not None:
            recipient=people[e['message']];assert recipient['alive'] and recipient['inbox'] is None
            recipient['inbox']=r[a%2]|instruction;used|=r[a%2]
        elif op==15 and p['inbox'] is not None:
            used|=p['inbox'];r[a%2]=p['inbox']|instruction;p['inbox']=None
        if e.get('birth') is not None:
            assert op==12
            child=e['birth'];assert type(child) is int and child not in people
            assert set(p['nursery'])==set(range(len(p['code'])))
            people[child]=person([p['nursery'][i] for i in range(len(p['code']))]);people[child]['position']=set(p['position']);p['nursery']={}
        if e.get('death',False):p['alive']=False
        records.append(dict(tick=tick,actor=identity,read=[list(x) for x in read],
                            used=[list(x) for x in sorted(used)]))
    def snapshot(p):
        return {k:([[list(o) for o in sorted(s)] for s in v] if k in ('registers','memory','code') else
                   {str(i):[list(o) for o in sorted(s)] for i,s in sorted(v.items())} if k=='nursery' else
                   [list(o) for o in sorted(v)] if k in ('feedback','pc','cue','position') or k=='inbox' and v is not None else v)
                for k,v in p.items()}
    return dict(records=records,actors={str(i):snapshot(p) for i,p in people.items()},
                classification='conservative_origin_reachability_only',causal_effect='UNKNOWN',
                learning=False,stage_credit=False)
