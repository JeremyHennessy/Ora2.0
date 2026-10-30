"""Prospective Pressure71-v2 COPY adapter; no scientific execution admission.

All frozen68 operations retained. The copied step changes only COPY dispatch
to an explicitly bound dose. New dose identity is authenticated in state hashes.
Integer organism programs cannot address host objects or dose metadata.
"""
from experiments.digital_sharedlineage68_population import (
    World as BaseWorld, PROGRAMS, ANCESTOR_WORDS, h, clone, state_types,
    validate_copy_configuration)

VERSION = 'DIGITAL-PRESSURE-SELECTION-71-POPULATION-v2'


def copy_result(seed, write_id, parent_value, index, mode, inheritance_mode, dose):
    validate_copy_configuration(seed, mode, inheritance_mode)
    assert type(dose) is int and dose in (1, 8)
    assert type(write_id) is int and write_id >= 0
    assert type(parent_value) is int and 0 <= parent_value < 32
    assert type(index) is int and 0 <= index < 27
    effective = parent_value if inheritance_mode == 'parent_copy' else ANCESTOR_WORDS[index]
    draw = int(h([seed, 'mutation', write_id])[:16], 16)
    value = ((effective + 1 + (draw // 100) % 31) % 32
             if mode == 'mutating' and draw % 100 < dose else effective)
    return effective, draw, value


class World(BaseWorld):
    def __new__(cls, *args, **kwargs):
        # Keep allocation independent of an inherited __new__ guard's restored
        # Python slot. Initialization below still pays/checks the frozen laws.
        return object.__new__(cls)

    def __init__(self, seed, mode='faithful', route='ancestor', fuel_mode='renewed',
                 inheritance_mode='parent_copy', *, dose=8):
        self._dose = dose
        super().__init__(seed, mode, route, fuel_mode, inheritance_mode)

    def __setattr__(self, name, value):
        if name == '_dose':
            assert type(value) is int and value in (1, 8)
            if '_dose' in self.__dict__:
                raise AttributeError('COPY dose is immutable')
        super().__setattr__(name, value)

    @property
    def dose(self):
        return self._dose

    def check(self):
        assert type(self.dose) is int and self.dose in (1, 8)
        super().check()

    def step(self):
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
        elif opcode==1:reg[a%2]=e['feedback']
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

    @classmethod
    def restore(cls, state):
        state_types(state)
        assert type(state['_dose']) is int and state['_dose'] in (1, 8)
        assert type(state['tick']) is int and 0 <= state['tick'] <= 4096
        routes = [name for name, program in PROGRAMS.items()
                  if sum(program, []) == [cell['value'] for cell in state['formation'][:3*len(program)]]
                  and len(state['formation']) == 3*len(program)+16]
        assert len(routes) == 1
        world = cls(state['seed'], state['mode'], routes[0], state['fuel_mode'],
                    state['inheritance_mode'], dose=state['_dose'])
        while world.tick < state['tick']:
            assert world.step()
        assert h(world.snapshot()) == h(state)
        return world


def history(seed, route='ancestor', mode='faithful', fuel_mode='renewed',
            inheritance_mode='parent_copy', *, dose=8, horizon=4096, software_only=False):
    assert type(software_only) is bool
    assert type(horizon) is int and 64 <= horizon <= 4096
    if software_only:
        assert type(seed) is int and seed in (1, 2)
    else:
        assert horizon == 4096
    world = World(seed, mode, route, fuel_mode, inheritance_mode, dose=dose)
    while world.tick < 64 and world.step():
        pass
    checkpoint = world.snapshot()
    resumed = World.restore(checkpoint)
    final = world.run(horizon)
    assert final == resumed.run(horizon)
    return dict(version=VERSION, seed=seed, mode=mode, inheritance_mode=inheritance_mode,
                fuel_mode=fuel_mode, route=route, dose=dose, horizon=horizon,
                software_only=software_only, genesis_program=clone(PROGRAMS[route]),
                checkpoint=checkpoint, final=final, hash=h(final), ancestor_supplied=True,
                checkpoint_replay=True, learning_demonstrated=False)
