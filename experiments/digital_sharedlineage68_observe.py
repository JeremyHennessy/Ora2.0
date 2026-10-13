"""Unqualified observations after full replay. Prepared witnesses are not histories.

No producer imports. Observer values stay outside every physical snapshot/hash.
"""
from fractions import Fraction
from experiments.digital_sharedlineage68_transition import actor_record,clone,h,ANCESTOR_WORDS,validate_provenance
from experiments.digital_sharedlineage68_admission import PRIMARY,UNSEEN,SEEDS,ordinary_gate

class Observation:
    def __init__(self):
        self.actors={};self.births=[];self.certificates={};self.competition=[];self.ownership={};self.pre=None

    def before(self,state,decoded):
        self.pre=clone(state);self.decoded=list(decoded)
        if not self.actors:
            founder=actor_record(state['entities'],0)
            self._born(founder,0)

    def _born(self,body,tick):
        identity=body['id'];assert identity not in self.actors
        program=[v[0] for v in body['code']]
        self.actors[identity]=dict(id=identity,parent=body['parent'],generation=body['generation'],
            birth_tick=tick,birth_site=body['pos'],born_program=program,born_program_hash=h(program),
            born_state_hash=h(body),born_memory_hash=h(body['memory']),turns=0,food=0,births=0,
            act_attempts=0,empty_act=0,pre_change_attempts=0,post_change_attempts=0,
            instruction_energy=0,copy_energy=0,division_energy=0,food_energy=0,cap_loss_energy=0,
            self_writes=[],signatures=[],death_tick=None,death_cause=None,censored=True)

    def after(self,state,event,terminal_body):
        """Called only by literal replay after complete event equality succeeds."""
        pre=self.pre;assert pre is not None and event['decoded']==self.decoded
        assert h(state)==event['state_hash']
        actor=event['actor'];before=actor_record(pre['entities'],actor);record=self.actors[actor]
        assert before['id']==actor and h(before)==event['before']
        record['turns']+=1;record['instruction_energy']+=1
        program=[v[0] for v in before['code']]
        for word in event.get('writes',[]):
            identity=word['write_id'];assert identity not in self.certificates
            self.certificates[identity]=dict(word,actor=actor,source_program_hash=h(program))
        if 'writes' in event:record['copy_energy']+=3
        if 'self_write' in event:record['self_writes'].append(dict(event['self_write'],tick=event['tick']))
        if 'birth' in event:
            birth=event['birth'];child=birth['child'];words=[self.certificates[i] for i in birth['write_ids']]
            assert len(words)==27 and all(w['actor']==actor and w['index']==i for i,w in enumerate(words))
            assert child['code']==[[w['value'],w['unit']] for w in words]
            self._born(child,event['tick']);record['births']+=1;record['division_energy']+=30
            self.births.append(dict(parent=actor,child=child['id'],generation=child['generation'],tick=event['tick'],
                parent_personal_food=record['food'],parent_turns=record['turns'],write_ids=list(birth['write_ids']),
                temporally_copied_source_program=[w['source_value'] for w in words],
                effective_source_program=[w['effective_source_value'] for w in words],
                newborn_program=[v[0] for v in child['code']],copy_source_program_hashes=[w['source_program_hash'] for w in words],
                certificates=clone(words),parent_program_at_division=program,
                actual_mutated_words=sum(w['mutated'] for w in words)))
        opcode,a,b=event['decoded']
        if opcode==6:
            record['signatures'].append(['ACT',before['pos'],before['registers'][a%2]%2])
            if 'attempt' not in event:record['empty_act']+=1
            else:
                record['act_attempts']+=1
                record['pre_change_attempts' if event['tick']<2048 else 'post_change_attempts']+=1
                if event['attempt']['success']:
                    record['food']+=1;gain=terminal_body['energy']-(before['energy']-1)
                    assert 0<=gain<=20
                    record['food_energy']+=gain;record['cap_loss_energy']+=20-gain
        if opcode==13:record['signatures'].append(['MOVE',terminal_body['pos']])
        self._competition(pre,event,before)
        if 'death' in event or 'expiry' in event:
            assert record['death_tick'] is None
            record.update(death_tick=event['tick'],death_cause='execution_budget' if 'expiry' in event else
                ('halt' if event['outcome']=='halt' else 'zero_energy'),censored=False)
            self._end(record,terminal_body)
        self.pre=None

    def _competition(self,pre,event,before):
        opcode=event['decoded'][0];free=len(pre['free']);energy=before['energy']-1
        actors=pre['entities'];eligible=False;required=None
        if opcode==10 and event['outcome']=='copy_refused':
            required=3;eligible=len(before['nursery'])<len(before['code']) and energy>=3
        if opcode==12 and event['outcome']=='division_refused':
            required=16;eligible=len(before['nursery'])==len(before['code']) and energy>=30 and len(actors)<32
        if not eligible or free>=required or len(actors)<2:return
        ownership={}
        for identity,body in actors.items():
            ownership[str(identity)]=dict(code=[w[1] for w in body['code']],state=list(body['state_units']),nursery=[w['unit'] for w in body['nursery']])
        owned=[u for value in ownership.values() for units in value.values() for u in units]
        assert len(owned)==len(set(owned)) and set(owned).isdisjoint(pre['free'])
        assert set(owned)|set(pre['free'])==set(range(512))
        key=h(ownership);self.ownership[key]=ownership
        self.competition.append(dict(tick=event['tick'],actor=event['actor'],opcode=opcode,outcome=event['outcome'],
            energy_after_instruction=energy,nursery_words=len(before['nursery']),program_words=len(before['code']),
            population=len(actors),free_units=free,required_units=required,ownership_hash=key,
            before_instruction_state_hash=h(pre),post_step_state_hash=event['state_hash']))

    def intervention(self,after,target):
        record=self.actors[target];assert record['turns']==0
        # Natural born identity remains recorded, alongside disclosed changed startup.
        body=actor_record(after['entities'],target)
        record['counterfactual_start_program']=[v[0] for v in body['code']]
        record['counterfactual_start_state_hash']=h(body)

    @staticmethod
    def _end(record,body):
        program=[v[0] for v in body['code']]
        record.update(end_program=program,end_program_hash=h(program),end_state_hash=h(body),
            end_memory_hash=h(body['memory']))

    def finish(self,final,summary):
        assert self.pre is None
        for body in final['entities'].values():self._end(self.actors[body['id']],body)
        assert len(self.births)==summary['births']
        assert sum(a['food'] for a in self.actors.values())==summary['successful_food']
        assert sum(a['turns'] for a in self.actors.values())==summary['ticks']
        assert sum(a['births'] for a in self.actors.values())==summary['births']
        assert sum(not a['censored'] for a in self.actors.values())==summary['deaths']
        for identity,record in self.actors.items():assert record['turns']==actor_record(summary['turns'],identity)
        return dict(actors=clone(self.actors),births=clone(self.births),material_competition=clone(self.competition),
            ownership=clone(self.ownership),endpoint_tick=final['tick'],stage_credit=False)

def representation(projection,target):
    """All finite observed parents, including zero offspring and censored actors."""
    candidate=actor_record(projection['actors'],target);generation=candidate['generation'];program=candidate['born_program']
    parents=[a for a in projection['actors'].values() if a['generation']==generation]
    edges=[b for b in projection['births'] if b['generation']==generation+1]
    assert parents
    z={a['id']:int(a['born_program']==program) for a in parents}
    offspring={a['id']:0 for a in parents}
    for edge in edges:offspring[edge['parent']]+=1
    for a in parents:assert offspring[a['id']]==a['births']
    p=Fraction(sum(z.values()),len(parents))
    base=dict(generation=generation,parent_ids=[a['id'] for a in parents],parents=len(parents),offspring=len(edges),
        parent_indicator=z,offspring_counts=offspring,censored_parent_ids=[a['id'] for a in parents if a['censored']],P=[p.numerator,p.denominator])
    if not edges:return dict(base,defined=False,W=None,C=None,identity=None,positive=False)
    w=Fraction(sum(z[i]*offspring[i] for i in z),len(edges))
    c=Fraction(sum(edge['newborn_program']==program for edge in edges),len(edges))
    assert c-p==(w-p)+(c-w)
    return dict(base,defined=True,W=[w.numerator,w.denominator],C=[c.numerator,c.denominator],
        identity=dict(total=[(c-p).numerator,(c-p).denominator],weighting=[(w-p).numerator,(w-p).denominator],
            transmission=[(c-w).numerator,(c-w).denominator]),positive=w>p and c>p)

def transmission(projection,target):
    program=actor_record(projection['actors'],target)['born_program'];chains=[]
    for first in projection['births']:
        if first['parent']!=target or first['temporally_copied_source_program']!=program or first['newborn_program']!=program:continue
        child=actor_record(projection['actors'],first['child'])
        if not(child['food']>0 and child['births']>0):continue
        for second in projection['births']:
            if second['parent']!=child['id'] or second['temporally_copied_source_program']!=program or second['newborn_program']!=program:continue
            grandchild=actor_record(projection['actors'],second['child'])
            if grandchild['food']>0 and grandchild['births']>0:
                chains.append([target,child['id'],grandchild['id']])
    return dict(exact_paid_chains=chains,positive=bool(chains))

def contrast(sham,control,changed):
    """Personally measured complete endpoints; NULL never enters this helper."""
    assert type(changed) is bool
    complete=not sham['censored'] and not control['censored']
    db=sham['births']-control['births'];df=sham['food']-control['food']
    useful=changed and complete and ((db>0 and df>=0) or (df>0 and db>=0))
    differences=[i for i,(a,b) in enumerate(zip(sham['signatures'],control['signatures'])) if a!=b]
    return dict(birth_difference=db,food_difference=df,complete=complete,changed=changed,
        conditional_useful_program=useful,shared_action_ordinals=len(list(zip(sham['signatures'],control['signatures']))),
        differing_action_ordinals=differences,new_resource_strategy=useful and bool(differences),
        disposition='censored' if not complete else 'noop' if not changed else 'gain' if useful else
            'tie' if db==df==0 else 'loss_or_tradeoff',stage_credit=False)

def overlapping_programs(projection):
    actors=[a for a in projection['actors'].values() if a['id']!=0 and a['turns']>=8]
    pairs=[]
    for i,a in enumerate(actors):
        for b in actors[i+1:]:
            end_a=a['death_tick'] if not a['censored'] else projection['endpoint_tick']
            end_b=b['death_tick'] if not b['censored'] else projection['endpoint_tick']
            if a['born_program']!=b['born_program'] and max(a['birth_tick'],b['birth_tick'])<min(end_a,end_b):
                pairs.append([a['id'],b['id']])
    return pairs

def audit_row(row,expected_provenance):
    """Full ordinary referee first; independent observed replay agrees on summary."""
    from experiments import digital_sharedlineage68_interpret as full
    from experiments import digital_sharedlineage68_fork_interpret as replay
    validate_provenance(expected_provenance)
    summary=full.audit(row);observation=Observation()
    measured=replay.audit_history(row,observations=observation)
    assert measured==summary
    projected=observation.finish(row['final'],measured)
    return dict(verified=True,summary=measured,projection=projected,history_hash=row['hash'],
        provenance=clone(expected_provenance),stage_credit=False)

def cohort(populations,forks,expected_provenance):
    """Complete original-role cohort after externally bound full-history audits.

    Restored engineering proofs must be compared by the finite caller and never
    counted here as independent populations. This helper cannot authenticate a
    supplied proof by its `verified` field alone.
    """
    validate_provenance(expected_provenance)
    assert type(populations) is list and len(populations)==24
    assert type(forks) is list and len(forks)==32
    rows={};branches={}
    roles=(('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy'))
    for proof in populations:
        assert proof['verified'] is True and proof['stage_credit'] is False and proof['provenance']==expected_provenance
        summary=proof['summary'];seed=summary['seed']
        assert type(seed) is int and seed in SEEDS
        key=(seed,summary['mode'],summary['inheritance_mode']);assert key not in rows
        assert key[1:] in roles and summary['verified'] is True and summary['route']=='ancestor' and summary['fuel_mode']=='renewed'
        assert summary['genesis_program_hash']==h(ANCESTOR_WORDS) and summary['formation_cost']==43
        if summary['mode']=='faithful':assert ordinary_gate(summary)
        rows[key]=proof
    assert set(rows)=={(seed,*role) for seed in SEEDS for role in roles}
    for proof in forks:
        assert proof['verified'] is True and proof['stage_credit'] is False and proof['provenance']==expected_provenance
        assert type(proof['seed']) is int and type(proof['generation']) is int
        key=(proof['seed'],proof['generation'],proof['role']);assert key not in branches
        assert proof['natural_history_hash']==rows[key[0],'mutating','parent_copy']['history_hash']
        branches[key]=proof
    assert set(branches)=={(seed,g,role) for seed in SEEDS for g in (1,2) for role in ('sham','ancestor_value_control')}
    slots=[]
    for seed in SEEDS:
        natural=rows[seed,'mutating','parent_copy']['projection']
        for generation in (1,2):
            sham=branches[seed,generation,'sham'];control=branches[seed,generation,'ancestor_value_control']
            assert sham['slot']==control['slot'] and sham['null']==control['null']
            slot=sham['slot']
            if slot is None:
                assert sham['null'] is True and control['null'] is True
                slots.append(dict(seed=seed,generation=generation,slot=None,null=True,candidate=False))
                continue
            assert sham['null'] is False
            target=slot['target'];born=actor_record(natural['actors'],target)
            assert born['generation']==generation and born['birth_tick']==slot['tick']
            changed=born['born_program']!=ANCESTOR_WORDS
            a=actor_record(sham['projection']['actors'],target);b=actor_record(control['projection']['actors'],target)
            for proof,actor in ((sham,a),(control,b)):
                assert actor['turns']==proof['target']['turns'] and actor['food']==proof['target']['food']
                assert actor['births']==proof['target']['births'] and actor['censored']==proof['target']['censored']
            comparison=contrast(a,b,changed);transmitted=transmission(natural,target);represented=representation(natural,target)
            competing=bool(natural['material_competition'])
            candidate=comparison['conditional_useful_program'] and comparison['new_resource_strategy'] and transmitted['positive'] and represented['positive'] and competing
            slots.append(dict(seed=seed,generation=generation,slot=slot,null=False,comparison=comparison,
                transmission=transmitted,representation=represented,material_competition=competing,candidate=candidate))
    contexts=[]
    for bank,seeds in (('primary',PRIMARY),('unseen',UNSEEN)):
        for first in seeds[::2]:
            effects=[]
            for seed in (first,first+1):
                fixed=rows[seed,'faithful','parent_copy'];natural=rows[seed,'mutating','parent_copy'];reset=rows[seed,'mutating','ancestor_copy']
                def endpoints(proof):
                    turnover=proof['summary']['turnover']
                    return turnover['post_founder_paid_personal_births'],turnover['post_founder_renewed_food']
                nb,nf=endpoints(natural);rb,rf=endpoints(reset);fb,ff=endpoints(fixed)
                turnover=natural['summary']['turnover'];projection=natural['projection']
                effects.append(dict(seed=seed,inheritance_birth_difference=nb-rb,inheritance_food_difference=nf-rf,
                    fixed_birth_difference=nb-fb,fixed_food_difference=nf-ff,
                    founder_expired=turnover['founder_expiry_tick'] is not None,
                    maximum_generation=turnover['maximum_generation'],overlapping_distinct_program_pairs=overlapping_programs(projection),
                    material_competition_witnesses=len(projection['material_competition'])))
            ib=sum(e['inheritance_birth_difference'] for e in effects);ifood=sum(e['inheritance_food_difference'] for e in effects)
            fb=sum(e['fixed_birth_difference'] for e in effects);ffood=sum(e['fixed_food_difference'] for e in effects)
            opportunities=all(e['founder_expired'] and e['maximum_generation']>=3 for e in effects) and any(e['overlapping_distinct_program_pairs'] for e in effects) and any(e['material_competition_witnesses'] for e in effects)
            contexts.append(dict(bank=bank,context=first//2,orientations=effects,opportunities=opportunities,
                inheritance_birth_difference=ib,inheritance_food_difference=ifood,fixed_birth_difference=fb,fixed_food_difference=ffood,
                inheritance_benefit=opportunities and ib>0 and ifood>=0,fixed_improvement=opportunities and fb>0 and ffood>=0))
    assert len(contexts)==4 and len(slots)==16
    replicated=any(s['candidate'] for s in slots if s['seed'] in PRIMARY) and any(s['candidate'] for s in slots if s['seed'] in UNSEEN)
    return dict(verified=True,contexts=contexts,neutral_slots=slots,original_population_roles=24,original_fork_roles=32,
        whole_inheritance_benefit=all(c['inheritance_benefit'] for c in contexts),whole_fixed_improvement=all(c['fixed_improvement'] for c in contexts),
        replicated_scoped_candidate=replicated,sustained_evolution=False,learning=False,stage_credit=False)
