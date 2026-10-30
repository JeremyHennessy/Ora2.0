"""Pinned AST/source contract. Never import or execute native organism code."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PINS={
 'prototypes/experience_affordance/census.py':'e6cc32bb0a39f16c00f66a6649139e98b75494863835c4e1c914ade60faa6d67',
 'prototypes/encoding_accessibility/census.py':'3fb32e465a5505ee74ee99b696253e3ec1f7129a08d215db72823301ab62b86b',
 'prototypes/encoding_accessibility/funding_bound.py':'436d703b9af268e2afc46b1d0fd41272181754517e50f40cc6551e066200c6a4',
 'prototypes/encoding_accessibility/lifetime_costs.py':'dffe8ea2c4d60e30b87a85aba0731496d80246fdc1ff490c395f1459b94c565b',
 'experiments/digital_pressure71_population.py':'cf22e109878bae6ac6b22e0563c8593f1c93e8ac03296a9ed9cd0cd43e1400de',
 'experiments/digital_sharedlineage68_population.py':'624e861387ceac70e4c2413ed852228db08f6b1ebd774e442732650ae2103609',
 'experiments/digital_mobile54.py':'245647ae7681a57b37d5d6e939c25d76a5df1365ccbdd98de3e4bd3cbb5ae1a3'}
FUNCTIONS=[['transition','evaluate','cost'],['expand','copy_bits'],['ledger'],['replay','first_probe_headroom'],
           ['World.step'],['World.__init__','World.body','World.check','World.input'],['budget']]


def node_at(tree,name):
    for part in name.split('.'):
        tree=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==part)
    return tree


def audit(root=ROOT):
    bindings=[]
    for (name,pin),functions in zip(PINS.items(),FUNCTIONS):
        raw=(root/name).read_bytes()
        if len(raw)>1024*1024 or hashlib.sha256(raw).hexdigest()!=pin:
            raise ValueError('Source pin mismatch: '+name)
        text=raw.decode();tree=ast.parse(text);lines=text.splitlines(keepends=True)
        spans=[]
        for function in functions:
            node=node_at(tree,function)
            segment=''.join(lines[node.lineno-1:node.end_lineno])
            spans.append(dict(function=function,line=node.lineno,end_line=node.end_lineno,
                segment_sha256=hashlib.sha256(segment.encode()).hexdigest()))
        bindings.append(dict(path=name,sha256=pin,functions=spans))
        if name.endswith('digital_mobile54.py'):
            program=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='PROGRAM' for t in n.targets)))
            assert len(program)==9 and all(len(row)==3 for row in program)
    return dict(schema='ORA-SOURCE-LIFETIME-CONTRACT-v1',source_bindings=bindings,
        compact_model=dict(status='DECLARED_OPERATION_CHARGES_CLOSED_LIFECYCLE_TIMING_UNDEFINED',
            transition_including_lookup=1,feedback_sensing_extra=1,changed_state_write_extra=1,
            selected_storage_price=0,formation_per_code_or_state_bit=1,
            required_separate_decoder_tax=False,
            correction='Prior unknown decoder/storage slots are not proof of missing ecological fees. Physical calibration is separate.',
            first_probe=dict(known_bill='4+d',dispatches='3+d',startup=8,
                extra_cost_headroom='4-d',meaning='Sensitivity to hypothetical added charges, not missing-fee evidence'),
            known_copy=dict(bits=6,read_heat=6,DNA_formation_heat=6,state_formation_heat=1,
                division_heat=1,startup_transfer=8,total=22),
            undefined=['copy clock and resource-phase progression','expiry during copying',
                'parent-owned material acquisition and stock','complete same-world lifecycle and offspring continuation']),
        native_source=dict(status='STATIC_LAW_COST_AND_ORDER_CLOSED_ACTUAL_LIFECYCLE_UNVERIFIED',
            source_law='Pressure71 step over SharedLineage68 constructor/input/body/check',
            order=['select actor','increment global tick','input/release','decode instruction',
                'debit base1','execute opcode and atomic gain','death if zero','increment actor turns','expiry at256'],
            base_dispatch_fee=1,READ_or_memory_or_SELFWRITE_additional_fee=0,
            successful_forage=dict(packet_energy=20,actor_energy_cap=64,base_debit_before_gain=True,
                successful_zero_after_base_can_be_rescued=True),
            before_first_success=dict(startup=12,necessary_total_debits_at_successful_forage_at_most=12,
                previous_completed_prefixes_strictly_below=12,
                scope='No earlier transfers/food; base and opcode extras count; necessary not successful-program evidence'),
            COPY=dict(words_per_dispatch=3,base=1,extra=3,materials=3),
            DIVIDE=dict(base=1,extra=30,extra_heat=18,child_transfer=12,state_materials=16),
            founder27_reproduction_floor=dict(copy_dispatches=9,division_dispatches=1,
                total_without_foraging_or_control=67,heat=55,child_transfer=12,materials=43,
                minimum_successful_food_packets_from_startup12=3,
                total_with_three_forage_base_fees=70,
                scope='Lower bound only; no program, mutation path, actual food access or viable lineage established'),
            clocks=dict(actor_expiry_dispatches=256,registered_global_horizon=4096,
                renewable_inflow_period_global_ticks=64,renewable_target_phase_boundary=2048),
            materials=dict(total_units=512,founder27_body=43,initial_free=469,
                source='Constructor pool, not a claimed evolved material acquisition capability')),
        host_resources=dict(status='SEPARATE_PHYSICAL_METERING_NOT_AN_INVENTED_ORGANISM_TAX',
            cpu_to_organism_energy_conversion=None,physical_efficiency_claim=False),
        full_lifecycle_qualified=False,scientific_admission=False,population_execution=False,
        verdict='COMPACT_ROUTE_NO_GO_AS_FULL_LIFECYCLE;NATIVE_FEASIBILITY_UNKNOWN')


def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args()
    result=audit()
    with args.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)


if __name__=='__main__':main()
