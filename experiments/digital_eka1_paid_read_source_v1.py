"""Unexecuted single paid READ dispatch derivative; no discovery or launcher.

Caller must separately authenticate the common original prefix with the original
restore/replay and own registered native authority. This function checks only a
supplied source/state binding. Derived history is not original history. It is
not accepted by the old original-history loader. No grant is created here.
"""
from experiments.digital_pressure71_population import World, copy_result, h, clone

SOURCE = 'cf22e109878bae6ac6b22e0563c8593f1c93e8ac03296a9ed9cd0cd43e1400de'
FIELDS = {'schema', 'source_sha256', 'common_pre_state_sha256', 'actor',
          'tick', 'own_turns', 'pc', 'decoded', 'original_world_id', 'branch_ids'}
ARMS = ('true', 'identity_sham', 'xor1')


def verify_context(world, binding, arm):
    """No mutation, source step, replay, hash draw, seed query or authority."""
    if type(world) is not World or type(binding) is not dict or set(binding) != FIELDS:
        raise ValueError('Exact original source object and binding required')
    if binding['schema'] != 'ORA-EKA1-COMMON-PRE-READ-v1' or binding['source_sha256'] != SOURCE:
        raise ValueError('Source/schema mismatch')
    if type(arm) is not str or arm not in ARMS:
        raise ValueError('Role')
    digest = binding['common_pre_state_sha256']
    if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Common prefix SHA256')
    ids = binding['branch_ids']; origin = binding['original_world_id']
    if (type(origin) is not str or not 0 < len(origin) <= 128
            or type(ids) is not dict or set(ids) != set(ARMS)
            or any(type(v) is not str or not 0 < len(v) <= 128 for v in ids.values())
            or len(set(ids.values())) != 3 or origin in ids.values()):
        raise ValueError('Distinct prospective branch labels')
    for field in ('actor', 'tick', 'own_turns', 'pc'):
        if type(binding[field]) is not int or binding[field] < 0:
            raise ValueError('Exact nonnegative integer context')
    if not world.entities:
        raise ValueError('No scheduled actor')
    actor_ids = sorted(world.entities)
    actor = next((i for i in actor_ids if i > world.last), actor_ids[0])
    entity = world.entities[actor]
    decoded = binding['decoded']
    if (type(decoded) is not list or len(decoded) != 3
            or any(type(x) is not int or not 0 <= x < 32 for x in decoded)
            or decoded[0] != 1 or entity['feedback'] not in (0, 1)):
        raise ValueError('Truthful feedback READ only')
    if (actor != binding['actor'] or world.tick != binding['tick']
            or world.turns[actor] != binding['own_turns'] or entity['pc'] != binding['pc']
            or [v[0] for v in entity['code'][3*entity['pc']:3*entity['pc']+3]] != decoded):
        raise ValueError('Scheduled pre-READ context changed')
    world.check()
    if h(world.snapshot()) != digest:
        raise ValueError('Complete original prefix changed')
    return digest, ids[arm]


def paid_read_dispatch(self, binding, arm):
    pre_hash, branch_id = verify_context(self, binding, arm)
    if not self.entities:return False
    ids=sorted(self.entities);actor=next((i for i in ids if i>self.last),ids[0]);self.last=actor
    e=self.entities[actor];self.tick+=1;n=len(e['code'])//3
    offers=self.input()
    release=None
    if self.tick==64:
        assert self.constructor_remaining>=16
        self.constructor_remaining-=16;self.heat+=16
        release=dict(packets=list(range(16,32)),energy=16,assistance='supplied exogenous stock boundary')
    opcode,a,b=[v[0] for v in e['code'][3*e['pc']:3*e['pc']+3]]
    event=dict(tick=self.tick,actor=actor,decoded=[opcode,a,b],before=h(e),outcome='executed')
    if offers is not None:event['input']=offers
    if release:event['release']=release
    e['energy']-=1;self.heat+=1;e['pc']=(e['pc']+1)%n
    reg=e['registers'];neighbors=[self.entities[i] for i in ids if i!=actor and self.entities[i]['pos']==e['pos']]
    local=sorted(i for i,v in self.food.items() if v[0]==e['pos'] and (not 16<=i<32 or self.tick>=64))
    if opcode==0:
        e['cue']=e['pos'];reg[a%2]=e['cue'];event['cue']=e['cue']
    elif opcode==1:
        truthful = e['feedback']
        delivered = truthful ^ int(arm == 'xor1')
        reg[a%2] = delivered
        event['eka1_read'] = dict(schema='ORA-EKA1-PAID-READ-DELTA-v1',
            original_world_id=binding['original_world_id'], derived_branch_id=branch_id,
            binding_sha256=h(binding), common_pre_state_sha256=pre_hash,
            source_sha256=SOURCE, arm=arm, destination=a%2,
            original_feedback=truthful, delivered_value=delivered,
            authentic_original_history_verified=False,
            derived_checkpoint_authority_granted=False, execution_authorized=False)
    elif opcode==2:reg[a%2]=e['memory'][b%8]
    elif opcode==3:e['memory'][a%8]=reg[b%2]
    elif opcode==4:reg[a%2]=b%16
    elif opcode==5:reg[a%2]^=reg[b%2]
    elif opcode==6:
        e['feedback']=0
        if local:
            packet=local[0];position,kind=self.food[packet];target=((self.seed%2 ^ (int(h([self.seed//2,'latent15'])[:8],16)%2) ^ int(int(h([self.seed//2,'noise15',packet])[:8],16)%16==0)) if position==0 and 16<=packet<32 else (self.seed%2 if position==0 else int(h([self.seed,'site-port',position])[:8],16)%2)^int(self.tick>=64))
            if packet>=64:target=self.seed%2 ^ (int(h([self.seed//2,'renew-port',position])[:8],16)%2) ^ int(self.tick>=2048)
            e['feedback']=int(reg[a%2]%2==target)
            event['attempt']=dict(packet=packet,position=position,cue=kind,port=reg[a%2]%2,target=target,success=e['feedback'])
            if e['feedback']:
                del self.food[packet]
                gain=min(20,64-e['energy']);e['energy']+=gain;self.heat+=20-gain
        event['feedback']=e['feedback']
    elif opcode==7:e['pc']=b%n
    elif opcode==8:
        if reg[a%2]==0:e['pc']=b%n
    elif opcode==9:
        address=b%len(e['code']);old=e['code'][address][0];e['code'][address][0]=reg[a%2]
        event['self_write']=dict(unit=e['code'][address][1],index=address,old=old,value=reg[a%2])
    elif opcode==10:
        if self.mode!='copy_disabled' and len(e['nursery'])<len(e['code']) and len(self.free)>=3 and e['energy']>=3:
            writes=[]
            for index in range(len(e['nursery']),len(e['nursery'])+3):
                source=e['code'][index]
                effective,draw,value=copy_result(self.seed,self.writes,source[0],index,self.mode,self.inheritance_mode,self.dose)
                unit=self.free.pop(0)
                write=dict(unit=unit,value=value,index=index,tick=self.tick,source_unit=source[1],source_value=source[0],effective_source=self.inheritance_mode,effective_source_value=effective,mutation_draw=draw,write_id=self.writes,mutated=value!=effective)
                self.writes+=1;e['nursery'].append(write);writes.append(clone(write))
            e['energy']-=3;self.heat+=3;event['writes']=writes
        else:event['outcome']='copy_refused'
    elif opcode==11:
        if len(e['nursery'])<len(e['code']):e['pc']=b%n
    elif opcode==12:
        if len(e['nursery'])==len(e['code']) and e['energy']>=30 and len(self.free)>=16 and len(self.entities)<32:
            child=self.next_id;self.next_id+=1;units=self.free[:16];del self.free[:16]
            daughter=self.body(child,actor,e['generation']+1,[[w['value'],w['unit']] for w in e['nursery']],units,e['pos'])
            event['birth']=dict(child=clone(daughter),write_ids=[w['write_id'] for w in e['nursery']],state_formation=[dict(unit=u,value=e['pos'] if i==14 else 0,energy=1) for i,u in enumerate(units)],release_energy=2,startup_energy=12)
            self.entities[child]=daughter;self.turns[child]=0;e['energy']-=30;self.heat+=18;e['nursery']=[];self.births+=1
        else:event['outcome']='division_refused'
    elif opcode==13:e['pos']=(e['pos']+(1 if reg[a%2]%2 else -1))%4
    elif opcode==14:
        if neighbors and neighbors[0]['inbox'] is None:
            neighbors[0]['inbox']=reg[a%2];event['message']=dict(recipient=neighbors[0]['id'],value=reg[a%2])
    elif opcode==15:
        if e['inbox'] is not None:reg[a%2]=e['inbox'];e['inbox']=None
    elif opcode==16:
        if neighbors and e['energy']>=1 and neighbors[0]['energy']<64:e['energy']-=1;neighbors[0]['energy']+=1;event['transfer']=neighbors[0]['id']
    elif opcode==17:self.heat+=e['energy'];e['energy']=0;event['outcome']='halt'
    if e['energy']==0:
        released=[v[1] for v in e['code']]+e['state_units']+[w['unit'] for w in e['nursery']]
        self.free=sorted(self.free+released);del self.entities[actor];self.deaths+=1;event['death']=released
    else:event['after']=clone(e)
    self.maximum=max(self.maximum,len(self.entities));self.check()
    event['vm_state_hash']=h(self.snapshot(include_events=False))
    self.turns[actor]+=1
    if actor in self.entities and self.turns[actor]==256:
        released=[v[1] for v in e['code']]+e['state_units']+[w['unit'] for w in e['nursery']]
        event['expiry']=dict(actor=actor,turns=256,energy=e['energy'],units=released,body_before=h(e),reason='execution_budget')
        self.heat+=e['energy'];self.free=sorted(self.free+released);del self.entities[actor];self.deaths+=1
    self.check()
    event['state_hash']=h(self.snapshot(include_events=False));self.events.append(event);return True
