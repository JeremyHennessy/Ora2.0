"""Separately structured cell-map provenance scan; no diagnostic/producer import."""


def trace(views, code_words=27):
    assert type(code_words) is int and 3<=code_words<=96 and code_words%3==0
    cells={};sizes={0:code_words};living={0:True};pending={0:set()};occupied_inbox=set();rows=[]
    def get(who,name,index=0):return cells.get((who,name,index),frozenset())
    def put(who,name,index,value):cells[(who,name,index)]=frozenset(value)
    previous=0
    for event in views:
        t=event['tick'];who=event['actor'];instruction=event['decoded'];op,x,y=instruction
        assert type(t) is int and t>previous and type(who) is int and living[who]
        assert all(type(v) is int and 0<=v<32 for v in instruction);previous=t
        address=event['pc_before'];assert type(address) is int and 0<=address<sizes[who]//3
        context=get(who,'pc')
        for offset in range(3):context=context|get(who,'code',address*3+offset)
        dependencies=context;reads=frozenset();left=get(who,'registers',x%2);right=get(who,'registers',y%2)
        if op==0:
            value=get(who,'position')|context;put(who,'cue',0,value);put(who,'registers',x%2,value);dependencies|=get(who,'position')
        if op==4:put(who,'registers',x%2,context)
        if op in (1,2,15):
            source='feedback' if op==1 else 'memory' if op==2 else 'inbox'
            slot=y%8 if op==2 else 0
            value=get(who,source,slot)
            if op!=15 or who in occupied_inbox:
                put(who,'registers',x%2,value|context);dependencies=dependencies|value
            if op==1:reads=value
            if op==15 and who in occupied_inbox:
                occupied_inbox.remove(who);cells.pop((who,'inbox',0),None)
        if op==3:
            put(who,'memory',x%8,right|context);dependencies=dependencies|right
        if op==5:
            put(who,'registers',x%2,left|right|context);dependencies=dependencies|left|right
        if op==6:
            dependencies=dependencies|left|get(who,'position');assert type(event['packet_present']) is bool
            put(who,'feedback',0,[(who,t)] if event['packet_present'] else [])
        if op in (7,8,11):
            control=context|(left if op==8 else frozenset())
            put(who,'pc',0,get(who,'pc')|control)
            if op==8:dependencies=dependencies|left
        if op==9:
            change=event['self_write'];slot=change['index']
            assert type(slot) is int and 0<=slot<sizes[who]
            value=left|context
            if change['old']==change['value']:value=value|get(who,'code',slot)
            put(who,'code',slot,value);dependencies=dependencies|left
        if op==10:
            for record in event.get('writes',[]):
                slot=record['index'];assert slot not in pending[who] and 0<=slot<sizes[who]
                pending[who].add(slot);put(who,'nursery',slot,get(who,'code',slot)|context)
        if event.get('birth') is not None:
            child=event['birth'];assert op==12 and type(child) is int and child not in sizes
            assert pending[who]==set(range(sizes[who]))
            sizes[child]=sizes[who];living[child]=True;pending[child]=set()
            put(child,'position',0,get(who,'position'))
            for slot in range(sizes[who]):
                put(child,'code',slot,get(who,'nursery',slot));cells.pop((who,'nursery',slot),None)
            pending[who].clear()
        if op==13:
            put(who,'position',0,get(who,'position')|left|context);dependencies|=left
        if op==14 and event.get('message') is not None:
            target=event['message'];assert living[target] and target not in occupied_inbox
            occupied_inbox.add(target);put(target,'inbox',0,left|context);dependencies=dependencies|left
        if event.get('death',False):living[who]=False
        rows.append(dict(tick=t,actor=who,read=[list(a) for a in sorted(reads)],used=[list(a) for a in sorted(dependencies)]))
    people={}
    for who in sizes:
        state={}
        for field,length in [('registers',2),('memory',8),('code',sizes[who])]:
            state[field]=[[list(a) for a in sorted(get(who,field,i))] for i in range(length)]
        state['nursery']={str(i):[list(a) for a in sorted(get(who,'nursery',i))] for i in sorted(pending[who])}
        for name in ('feedback','pc','cue','position'):state[name]=[list(a) for a in sorted(get(who,name))]
        state['inbox']=[list(a) for a in sorted(get(who,'inbox'))] if who in occupied_inbox else None
        state['alive']=living[who];people[str(who)]=state
    return dict(records=rows,actors=people,classification='conservative_origin_reachability_only',
                causal_effect='UNKNOWN',learning=False,stage_credit=False)
