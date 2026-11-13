"""Read-only EKA-0 arithmetic and census of already-closed Pressure71 data.

No organism, producer, referee, VM, sampler, or model imports/execution. Explicit
closed role roster only. Results describe expression, never causal usefulness.
"""
import argparse,hashlib,json
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path

def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,cap):
    assert p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=cap
    return p.read_bytes()

def census(lab):
    root=lab/'runs/pressure71-scientific-v2-20261014'
    custody=json.loads(read(lab/'reports/pressure71-independent-interpretation-v1-registration.json',1024**2))
    checked_inputs=[]
    for filename in ('pressure71-scientific-v2-registration.json','pressure71-scientific-v2-audit.json'):
        path=lab/'reports'/filename;raw=read(path,8*1024**2)
        expected=[h for n,h in custody['pins'].items() if Path(n).name==filename]
        assert len(expected)==1 and sha(raw)==expected[0]
        checked_inputs.append(dict(path=str(path.relative_to(lab)),sha256=sha(raw),extent=len(raw)))
        if filename.endswith('-registration.json'):registration=json.loads(raw)
        else:closed_audit=json.loads(raw)
    assert closed_audit['verified'] and closed_audit['archive_restored']
    report=lab/'reports/pressure71-independent-interpretation-v1.json'
    prior_raw=read(report,8*1024**2);prior=json.loads(prior_raw)
    assert prior['verified'] and prior['archive_restored']
    population=prior['result']['populations']
    names=sorted(n for n,v in population.items() if v['mode']=='mutating' and v['inheritance_mode']=='parent_copy')
    assert len(names)==16 and {population[n]['dose'] for n in names}=={1,8}
    pins=checked_inputs+[dict(path=str(report.relative_to(lab)),sha256=sha(prior_raw),extent=len(prior_raw))]
    source={}
    for n in ('experiments/digital_pressure71_population.py','experiments/digital_sharedlineage68_population.py','experiments/digital_mobile54.py'):
        raw=read(root/'raw/export'/n,256*1024);assert sha(raw)==registration['source_files'][n]
        source[n]=sha(raw)
    by_dose=defaultdict(Counter);details=[]
    for name in names:
        key='original/'+name+'/raw';receipt=json.loads(read(root/('raw/receipts/'+key+'.json'),65536))
        raw=read(root/('raw/data/'+key+'.json'),64*1024**2)
        assert len(raw)==receipt['extent'] and sha(raw)==receipt['sha256']==closed_audit['storage']['sha256']['raw/data/'+key+'.json']
        assert receipt['source_sha']==registration['source_sha256'] and receipt['config_sha']==registration['configuration_sha256']
        native=json.loads(read(root/('raw/native/'+key+'.json'),2*1024**2))
        assert native['exit_code']==0 and native['post_close_processes_exited'] and native['usage']['active_before_close']==0 and not native['timed_out'] and not native['output_truncated']
        # Check both archive restoration and independently executed source export.
        for duplicate in (root/('restore/full/raw/data/'+key+'.json'),root/('raw/data/restored/'+name+'/raw.json')):
            assert sha(read(duplicate,64*1024**2))==receipt['sha256']
        row=json.loads(raw);assert sha(enc(row['final']))==row['hash']
        assert row['mode']=='mutating' and row['inheritance_mode']=='parent_copy' and row['dose']==population[name]['dose']
        events=row['final']['events'];assert len(events)==row['final']['tick']
        born={0:dict(tick=0,code=sum(row['genesis_program'],[]))};executed=defaultdict(Counter);first_info={};first_op={};child_ticks=defaultdict(list);self_values={};copied_self={};inherited_self=set();mutations={};dead=set();effective_selfwrites=0
        for e in events:
            actor=e['actor'];assert actor in born
            op=e['decoded'][0];executed[actor][op]+=1;first_op.setdefault((actor,op),e['tick'])
            if op in (1,2,3,9):first_info.setdefault(actor,e['tick'])
            if 'self_write' in e:
                w=e['self_write'];self_values[actor,w['unit']]=(w['value'],e['tick']);effective_selfwrites+=int(w['old']!=w['value'])
            for w in e.get('writes',[]):
                mutations[w['write_id']]=w['mutated']
                value=self_values.get((actor,w['source_unit']))
                if value is not None and value[0]==w['source_value']==w['value'] and value[1]<e['tick']:
                    copied_self[w['write_id']]=(actor,value[1])
            if 'birth' in e:
                b=e['birth'];child=b['child'];assert child['id'] not in born
                born[child['id']]=dict(tick=e['tick'],code=[v[0] for v in child['code']],mutated=any(mutations[i] for i in b['write_ids']))
                child_ticks[actor].append(e['tick'])
                if any(i in copied_self for i in b['write_ids']):inherited_self.add(child['id'])
            if 'death' in e or 'expiry' in e:dead.add(actor)
        assert len(born)-1==population[name]['births'] and len(dead)==population[name]['deaths']
        c=Counter(populations=1,births=len(born)-1,actors=len(born),deaths=len(dead),paid_copy_words=sum(len(e.get('writes',[])) for e in events),mutations=sum(mutations.values()),executed_ticks=len(events))
        children=[i for i in born if i!=0]
        c['born_mutated']=sum(bool(born[i]['mutated']) for i in children)
        c['born_encoding_info_opcode']=sum(any(op in (1,2,3,9) for op in born[i]['code'][::3]) for i in children)
        c['born_expressing_info_opcode']=sum(i in first_info for i in children)
        c['born_died_without_info_expression']=sum(i in dead and i not in first_info for i in children)
        c['born_unexecuted']=sum(not executed[i] for i in children)
        c['born_reproduced_after_info_expression']=sum(i in first_info and any(t>first_info[i] for t in child_ticks[i]) for i in children)
        c['born_with_exact_unmutated_copy_of_previously_selfwritten_word']=len(inherited_self)
        c['effective_selfwrite_dispatches']=effective_selfwrites
        for op,label in [(1,'feedback'),(2,'memory_read'),(3,'memory_write'),(9,'selfwrite')]:
            c[label+'_dispatches']=sum(v[op] for v in executed.values())
            c['born_expressing_'+label]=sum(bool(executed[i][op]) for i in children)
            c['born_reproduced_after_'+label]=sum((i,op) in first_op and any(t>first_op[i,op] for t in child_ticks[i]) for i in children)
        assert c['paid_copy_words']==population[name]['paid_copy_words'] and c['mutations']==population[name]['mutations']
        by_dose[row['dose']].update(c);details.append(dict(closed_role=name,counts=dict(c)))
        pins.append(dict(path=str((root/('raw/data/'+key+'.json')).relative_to(lab)),sha256=receipt['sha256'],extent=receipt['extent']))
        del row,events,raw
    arithmetic=[];H=2**64
    for dose in (1,8):
        whole,tail=divmod(H,100);p_mut=Fraction(whole*dose+min(tail,dose),H)
        # A specified nonzero replacement delta uses quotient mod31. Exact
        # counts under a UNIFORM64-bit SHA-output assumption, not seed odds.
        cycles,rem=divmod(H,3100);delta_counts=[cycles*dose+max(0,min(dose,rem-100*k)) for k in range(31)]
        assert sum(delta_counts)==p_mut*H
        p_delta_max=Fraction(max(delta_counts),H)
        arithmetic.append(dict(dose=dose,uniform_hash_assumption_only=True,p_mutated_word=float(p_mut),p_any_mutation_27_independent_writes=1-float((1-p_mut)**27),p_exact_one_specified_replacement_no_other_changes=float(p_delta_max*(1-p_mut)**26),p_two_specified_replacements_no_other_changes=float(p_delta_max**2*(1-p_mut)**25),observed_paid_births=by_dose[dose]['births']))
    return dict(schema='ORA-EKA0-CLOSED-DATA-AUDIT-v1',verdict='UNKNOWN',population_execution='NO_GO_PENDING_FEASIBILITY',new_worlds=0,new_seed_queries=0,scientific_acceptance_changed=False,scope='Closed descriptive census plus conditional source arithmetic; expression or temporal co-occurrence is not learning, fitness, selection or novelty.',source_revision=registration['source_head'],source_manifest_sha256=registration['source_sha256'],source_pins=source,input_pins=pins,complete_mutating_parent_copy_roster=names,counts_by_dose={str(k):dict(v) for k,v in by_dose.items()},details=details,conditional_mutation_arithmetic=arithmetic,source_only_bounds=dict(ancestor_words=27,instruction_slots=9,one_word_substitutions=27*31,direct_information_opcode_replacements=9*4,mutable_information_opcodes=[1,2,3,9],state_material_units=16,mature_body_material=43,material_only_mature_population_upper_bound=512//43,minimum_copy_dispatches_per_birth=9,minimum_copy_division_dispatches_per_birth=10,minimum_parent_energy_expenditure_copy_division=9+27+1+30,copy_division_heat_excluding_child_transfer=9+27+1+18,newborn_energy=12,nominal_packet_energy=20,food_successes_energy_lower_bound_without_incoming_transfers=3,minimum_net_energy_input_copy_division_excluding_other_costs=55,own_turn_expiry=256),limits=['Hash outputs and lineage draws are deterministic; probabilistic arithmetic needs an explicit uniformity/independence premise.','Specified-sequence probability is not the probability of any useful phenotype. Multiple equivalent sequences and sequential neutral paths are not enumerated.','Direct opcode accessibility and energy/material bounds do not establish survival, a viable adaptive genotype or positive lower bound on useful inherited expression.','A self-written word need not contain acquired information; matching word-value provenance is descriptive only. Zero observed chains is not a general impossibility result.'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--lab',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(census(args.lab.resolve()),indent=2,sort_keys=True))
