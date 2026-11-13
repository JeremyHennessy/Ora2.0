"""New genotype-representation projection and paid-copy fixtures.

Consumes frozen #325 outcomes, never executes its controllers or any World.
No population, ecological reproduction, selection dynamics or new validation.
"""
from collections import deque
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT/'data/experience-affordance-20261026/complete-census.json.gz'
RAW_SHA = '0a6ba8975f364cf04cf23916b72f9c12a00f68c14fc2e1bb6f8d19727f8962e6'
PROTOCOL = {
    'schema': 'ORA-ENCODING-ACCESSIBILITY-PROJECTION-v1',
    'original_outcomes': RAW_SHA,
    'task_and_reward': 'UNCHANGED #325 retained data, reward8/storage0 only',
    'encodings': {
        'moore8': 'bits0,1 blank action bystate; bits2..7 nextstate by3*state+signal; feedback outputs0',
        'event6': 'bits0,1 blank action bystate; bits2..5 nextstate by2*state+feedback; blank holds state; feedback outputs0'},
    'hardware_prior': 'Unused feedback outputs fixed0; event6 additionally supplies blank-state persistence. Neither is evolved.',
    'formation_sensitivity': [6, 8, 12],
    'fitness_scope': 'Retained score minus quoted formation/transition/sensor/write costs, NOT survival or reproductive fitness',
    'paths': 'blind genotype0, ascending singlebit neighbors, nondecreasing legacy-development net; all endpoints retained',
    'strong_control': 'win-stay/lose-shift same6/8/12bit quote as candidate at each comparison',
    'copy_fixtures': {'read_cpu': 1, 'write_formation': 1, 'blank_state_formation': 1,
                      'division_cpu': 1, 'daughter_startup_transfer': 8,
                      'budgets': '0,required-1,required for every genotype and faithful/every one-bit mutation'},
    'copy_limit': 'Fixture copying, no phenotype execution/life/food/competition/offspring success; no future-income spending',
    'claims': 'New representation/accounting/bit-copy software qualification only. Prior heldout data reused, not fresh evidence.',
    'population_admission': False,
}


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def expand(genome, bits):
    assert bits in (6, 8) and type(genome) is int and 0 <= genome < 1 << bits
    full = 0
    for state in (0, 1):
        for signal in range(3):
            output = (genome >> state) & 1 if signal == 2 else 0
            if bits == 6:
                next_state = state if signal == 2 else (genome >> (2+2*state+signal)) & 1
            else:
                next_state = (genome >> (2+3*state+signal)) & 1
            full |= (output | next_state << 1) << (2*(3*state+signal))
    return full


def cost(row, bits, state_bits=1):
    return row['sequences'] * (bits+state_bits) + row['transitions'] + row['senses'] + row['writes']


def net(row, bits, state_bits=1):
    return 8*row['correct'] - cost(row, bits, state_bits)


def copy_bits(genome, bits, budget, flip=None):
    """Explicit bit-by-bit debits; retain unfinished nursery and resource accounting."""
    assert bits in (6, 8, 12) and type(genome) is int and 0 <= genome < 1 << bits and type(budget) is int and budget >= 0
    assert flip is None or type(flip) is int and 0 <= flip < bits
    remaining, heat, nursery = budget, 0, []
    for i in range(bits):
        if remaining < 2:
            break
        remaining -= 2
        heat += 2
        nursery.append(((genome >> i) & 1) ^ int(i == flip))
    born = len(nursery) == bits and remaining >= 10
    child, memory, child_energy = None, None, 0
    if born:
        remaining -= 10
        heat += 2  # state formation and division CPU; startup is a transfer, not heat
        child_energy = 8
        child = sum(v << i for i, v in enumerate(nursery))
        memory = 0
    free_units = bits+1-len(nursery)-int(born)
    assert remaining >= 0 and remaining+heat+child_energy == budget
    assert free_units+len(nursery)+int(born) == bits+1
    if born:
        assert child == genome ^ (0 if flip is None else 1 << flip)
    return dict(parent=genome, bits=bits, initial_budget=budget, flip=flip,
                complete_fixture_child=born, child=child, child_memory=memory,
                child_energy=child_energy, remaining=remaining, heat=heat,
                copied_bits=nursery, free_units=free_units,
                energy_conserved=True, material_conserved=True)


def analyze():
    raw = gzip.decompress(INPUT.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == RAW_SHA
    old = json.loads(raw)
    assert [r['genome'] for r in old['all_controller_records']] == list(range(4096))
    reference_dominance = {}
    for split, refs in old['controls'].items():
        fixed = max(net(r['row'], r['code_bits'], r['state_bits']) for r in refs if r['name'].startswith('fixed'))
        rows = [dict(name=r['name'], code_bits=r['code_bits'], state_bits=r['state_bits'],
                     net=net(r['row'], r['code_bits'], r['state_bits'])) for r in refs]
        assert all(r['net'] <= fixed for r in rows if r['name'].startswith('memoryless'))
        reference_dominance[split] = dict(all_reference_quotes=rows, fixed_net=fixed,
                                         fixed_dominates_all_eight_memoryless=True)
    families, fixtures = {}, []
    for bits in (6, 8):
        rows = []
        for genome in range(1 << bits):
            full = expand(genome, bits)
            source = old['all_controller_records'][full]
            row = dict(genome=genome, original12=full, splits={})
            for split in ('development', 'validation'):
                retained = source[split]
                refs = old['controls'][split]
                fixed = max(net(r['row'], r['code_bits'], r['state_bits']) for r in refs if r['name'].startswith('fixed'))
                strong = next(r['row'] for r in refs if r['name']=='win_stay_lose_shift')
                accounting = []
                for quote in (6, 8, 12):
                    accounting.append(dict(code_bit_quote=quote, net=net(retained['true'], quote),
                        fixed_net=fixed, strong_net=net(strong, quote),
                        delta_fixed=net(retained['true'], quote)-fixed,
                        delta_strong=net(retained['true'], quote)-net(strong, quote)))
                row['splits'][split] = dict(retained_all_arms=retained,
                    same_phenotype_code_quote_sensitivity=accounting,
                    own_quote_net=net(retained['true'], bits),
                    own_quote_delta_fixed=net(retained['true'], bits)-fixed,
                    own_quote_delta_strong=net(retained['true'], bits)-net(strong, bits))
            rows.append(row)
            required = 2*bits+10
            for budget in (0, required-1, required):
                for flip in (None, *range(bits)):
                    fixtures.append(copy_bits(genome, bits, budget, flip))
        score = [r['splits']['development']['own_quote_net'] for r in rows]
        parents, queue = {0: None}, deque([0])
        while queue:
            g = queue.popleft()
            for bit in range(bits):
                child = g ^ (1 << bit)
                if child not in parents and score[child] >= score[g]:
                    parents[child] = g
                    queue.append(child)
        # Legacy development selects the lowest-ID strict fixed-beating reachable endpoint.
        endpoints = [g for g in parents if rows[g]['splits']['development']['own_quote_delta_fixed'] > 0]
        chosen = min(endpoints) if endpoints else None
        path = []
        g = chosen
        while g is not None:
            path.append(dict(genome=g, development_net=score[g],
                reused_validation_net=rows[g]['splits']['validation']['own_quote_net']))
            g = parents[g]
        path.reverse()
        summary = {}
        for split in ('development', 'validation'):
            summary[split] = dict(founder_net=rows[0]['splits'][split]['own_quote_net'],
                beats_fixed=sum(r['splits'][split]['own_quote_delta_fixed'] > 0 for r in rows),
                beats_strong=sum(r['splits'][split]['own_quote_delta_strong'] > 0 for r in rows),
                best_net=max(r['splits'][split]['own_quote_net'] for r in rows),
                nonpositive_net=sum(r['splits'][split]['own_quote_net'] <= 0 for r in rows))
        families[str(bits)] = dict(genotypes=len(rows), undirected_edges=bits*(1<<bits)//2,
            all_rows=rows, summary=summary, reachable=len(parents),
            development_selected_endpoint=chosen, development_path=path,
            path_is_observed_evolution=False, fixed_reward=8)
    # Unchanged twelve-bit reference: copy qualification only, not another phenotype census.
    for genome in (0, 17):
        for budget in (0, 33, 34):
            for flip in (None, *range(12)):
                fixtures.append(copy_bits(genome, 12, budget, flip))
    fixture_summary = dict(total=len(fixtures), complete=sum(x['complete_fixture_child'] for x in fixtures),
        incomplete=sum(not x['complete_fixture_child'] for x in fixtures),
        minimum_complete_copy_budget={'6':22,'8':26,'12':34}, actual_organism_births=0,
        twelve_bit_scope='two arbitrary reference genotypes, all single-bit locations; no phenotype execution')
    return dict(protocol=PROTOCOL, protocol_sha256=sha(PROTOCOL), source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        retained_input_sha256=RAW_SHA, original_experiment_changed=False,
        controller_executions=0, native_VM_steps=0, populations=0, evolution_demonstrated=False,
        original_reference_records=old['controls'], reference_dominance=reference_dominance,
        families=families, copy_fixture_summary=fixture_summary, all_copy_fixtures=fixtures,
        note='All previous validation outcomes reused exploratorily; quoted scores are not lifetimes or reproductive fitness.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x', encoding='utf8') as output:
        try:
            json.dump(analyze(), output, indent=2)
        except BaseException as exc:
            json.dump({'status':'INCOMPLETE','exception':repr(exc),'protocol_sha256':sha(PROTOCOL)}, output)
            raise


if __name__=='__main__':
    main()
