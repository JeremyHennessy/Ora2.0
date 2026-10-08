"""Independent ENERGY-02 semantic interpreter; imports no worker."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/ENERGY-02-PROTOCOL.md', 'experiments/precursor_coupling.py', 'experiments/precursor_coupling_audit.py')
MODES = ('coupled', 'uncoupled', 'ghost', 'untemplated')


def text(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def sha(value):
    return hashlib.sha256(text(value).encode()).hexdigest()


def need(value, message):
    if not value:
        raise ValueError(message)


def unique(pairs):
    out = {}
    for key, value in pairs:
        need(key not in out, 'Duplicate key')
        out[key] = value
    return out


def panel():
    for size in range(2, 5):
        for bit_tuple in itertools.product('01', repeat=size):
            template = ''.join(bit_tuple)
            alternatives = [template, str(1-int(template[0]))+template[1:], template[:-1]+str(1-int(template[-1]))]
            for sequence in alternatives:
                for budget in range(size+1):
                    for fuel in [0, size, size*2]:
                        for mode in MODES:
                            for source in ['producer', 'external']:
                                yield dict(kind='primary', bits=template, candidate=sequence, budget=budget, fuel=fuel, mode=mode, source=source, phases=1)
            for mode in MODES:
                for source in ['producer', 'external', 'withdrawn']:
                    yield dict(kind='renewal', bits=template, candidate=template, budget=size, fuel=size*2, mode=mode, source=source, phases=2)


def schedule(c):
    out = []
    for p in range(c['phases']):
        parent = 'C' if p == 0 else 'D0'
        for slot in range(len(c['bits'])):
            out.extend([['harvest', parent, f'F{p}.{slot*2}', None],
                        ['harvest', parent, f'F{p}.{slot*2+1}', None],
                        ['activate', parent, f'M{p}.{slot}', f'A{p}.{slot}']])
        for slot in range(len(c['bits'])):
            out.extend([['recognize', parent, f'M{p}.{slot}', None], ['ligate', parent, None, None]])
        out.extend([['release', parent, f'D{p}', None], ['probe', f'D{p}', f'P{p}', None]])
    return out


def subsidized(c, p):
    return c['source'] == 'external' or (p == 0 and c['source'] == 'withdrawn')


def empty_channel():
    return {'atoms': [], 'pending': None, 'bonds': [], 'debits': []}


def genesis(c):
    s = {key: {} for key in ['atoms', 'units', 'objects', 'history', 'activation', 'environment']}
    s.update(channels={'C': empty_channel()}, ready=[], food=[], waste=[], heat=0, captures=[])
    n = len(c['bits'])
    ids = ['B'+str(i) for i in range(n)]
    for i, aid in enumerate(ids):
        s['atoms'][aid] = {'bit': c['bits'][i], 'kind': 'template', 'root': 'external_supply'}
    energy = ['G'+str(i) for i in range(c['budget'])]
    for uid in energy:
        s['units'][uid] = {'origin': 'genesis', 'actor': 'C', 'food': None, 'carrier': None, 'tick': -1}
    s['objects']['C'] = {'bits': c['bits'], 'atoms': ids, 'work': energy, 'bonds': [], 'supplied_bonds': n-1}
    s['history']['C'] = {'origin': 'supplied_template', 'producer': None, 'template': None, 'born_tick': -1,
                         'bits': c['bits'], 'atoms': list(ids), 'work': list(energy), 'bonds': [], 'supplied_bonds': n-1,
                         'construction_debits': [], 'matching': None, 'producer_funded': False,
                         'components': [{'atom': aid, 'activation_units': []} for aid in ids]}
    for p in range(c['phases']):
        for i in range(n):
            aid = f'M{p}.{i}'
            s['atoms'][aid] = {'bit': c['candidate'][i], 'kind': 'precursor', 'root': 'external_supply'}
            s['activation'][aid] = []
            s['ready'].append(aid)
        for food in [f'A{p}.{i}' for i in range(n)]+[f'F{p}.{i}' for i in range(c['fuel'])]+[f'P{p}']:
            s['atoms'][food] = {'bit': str(1-int(c['bits'][-1])), 'kind': 'food', 'root': 'external_supply'}
            s['food'].append(food)
        work = [f'E{p}.{i}' for i in range(n*2)] if subsidized(c, p) else []
        s['environment'][str(p)] = work
        for uid in work:
            s['units'][uid] = {'origin': 'external_work', 'actor': f'environment{p}', 'food': None, 'carrier': None, 'tick': -1}
    return s


def balance(s):
    material = list(s['ready'])+s['food']+s['waste']
    energy = []
    supplied = 0
    for oid, obj in s['objects'].items():
        material.extend(obj['atoms'])
        energy.extend(obj['work']+obj['bonds'])
        supplied += obj['supplied_bonds']
        need(len(obj['work']) <= len(obj['atoms']), 'Private capacity')
        need(''.join(s['atoms'][a]['bit'] for a in obj['atoms']) == obj['bits'], 'Immutable composition')
        need(len(obj['bonds'])+obj['supplied_bonds'] == len(obj['atoms'])-1, 'Structural accounting')
        need(oid in s['history'], 'Object birth missing')
    for ch in s['channels'].values():
        material.extend(ch['atoms'])
        if ch['pending'] is not None:
            material.append(ch['pending'])
        energy.extend(ch['bonds'])
        need(len(ch['bonds']) == max(0, len(ch['atoms'])-1), 'Channel bonds')
    for aid, units in s['activation'].items():
        need(s['atoms'][aid]['kind'] == 'precursor' and len(units) <= 3, 'Local precursor storage')
        energy.extend(units)
    for account in s['environment'].values():
        energy.extend(account)
    need(len(material) == len(set(material)) and set(material) == set(s['atoms']), 'Unique material ownership')
    need(len(energy) == len(set(energy)) and set(energy) <= set(s['units']), 'Unique energy ownership')
    need(type(s['heat']) is int and s['heat'] >= 0, 'Heat')
    for uid in energy:
        meta = s['units'][uid]
        need(set(meta) == {'origin', 'actor', 'food', 'carrier', 'tick'}, 'Unit provenance shape')
        if meta['food'] is not None:
            need(s['atoms'][meta['food']]['kind'] == 'food', 'Food provenance')
        if meta['carrier'] is not None:
            need(s['atoms'][meta['carrier']]['kind'] == 'precursor', 'Carrier provenance')
    mass = tuple(sorted(Counter(s['atoms'][a]['bit'] for a in material).items()))
    return mass, len(energy)+supplied+s['heat']+8*len(s['food'])


def advance(state, c, tick, req):
    s = deepcopy(state)
    act, who, material, food = req
    parent = s['objects'].get(who)
    chamber = s['channels'].get(who)
    result = {'outcome': 'unavailable', 'spent': [], 'returned': [], 'endowed': [], 'overflow': [],
              'bond': None, 'heat': 0, 'product': None, 'producer_funded': False, 'matching': None}
    def charge(pool, count):
        used = []
        for _ in range(count):
            used.append(pool.pop(0))
        result['spent'] += used
        return used
    def emit_heat(count):
        s['heat'] += count
        result['heat'] += count
    if act in ['harvest', 'probe', 'activate']:
        is_activation = act == 'activate'
        donor = food if is_activation else material
        env = is_activation and subsidized(c, int(material[1]))
        reservoir = s['environment'][material[1]] if env else parent['work'] if parent else []
        affinity = bool(parent and len(parent['bits']) >= 2 and donor in s['food'] and
                        parent['bits'][-1] != s['atoms'][donor]['bit'])
        valid = donor in s['food'] and (env or affinity)
        if is_activation:
            valid = valid and material in s['ready'] and not s['activation'][material]
        if valid and len(reservoir) < 2:
            result['outcome'] = 'starved'
        elif valid:
            charge(reservoir, 2)
            s['food'].remove(donor)
            s['waste'].append(donor)
            actor = f'environment{material[1]}' if env else who
            carrier = material if is_activation else None
            ids = []
            for j in range(3):
                uid = f'R{donor}:{tick}:{j}'
                ids.append(uid)
                s['units'][uid] = {'origin': 'activation' if is_activation else 'harvest',
                                  'actor': actor, 'food': donor, 'carrier': carrier, 'tick': tick}
            if is_activation:
                s['activation'][material] += ids
                result['outcome'] = 'activated'
            else:
                room = len(parent['atoms'])-len(parent['work'])
                parent['work'] += ids[:room]
                result['overflow'] = ids[room:]
                result['outcome'] = 'captured'
            result['returned'] = ids
            emit_heat(7+len(result['overflow']))
            s['captures'].append({'actor': actor, 'food': donor, 'carrier': carrier, 'tick': tick, 'units': ids})
    elif act == 'recognize':
        if parent and chamber['pending'] is None and len(chamber['atoms']) < len(parent['atoms']) and material in s['ready']:
            reservoir = parent['work'] if c['mode'] == 'uncoupled' else s['activation'][material]
            if not reservoir:
                result['outcome'] = 'starved'
            else:
                chamber['debits'] += charge(reservoir, 1)
                emit_heat(1)
                if c['mode'] != 'untemplated' and parent['bits'][len(chamber['atoms'])] != s['atoms'][material]['bit']:
                    result['outcome'] = 'mismatch'
                else:
                    s['ready'].remove(material)
                    chamber['pending'] = material
                    result['outcome'] = 'recognized'
    elif act == 'ligate':
        if parent and chamber['pending'] is not None:
            pending = chamber['pending']
            reservoir = parent['work'] if c['mode'] == 'uncoupled' else s['activation'][pending]
            if chamber['atoms'] and len(reservoir) < 2:
                result['outcome'] = 'starved'
            else:
                if chamber['atoms']:
                    paid = charge(reservoir, 2)
                    chamber['debits'] += paid
                    chamber['bonds'].append(paid[-1])
                    result['bond'] = paid[-1]
                    emit_heat(1)
                    result['outcome'] = 'ligated'
                else:
                    result['outcome'] = 'first_bound'
                chamber['atoms'].append(pending)
                chamber['pending'] = None
    elif act == 'release' and parent and chamber['pending'] is None and len(chamber['atoms']) == len(parent['atoms']):
        reservoir = parent['work']
        stored = sum((s['activation'][aid] for aid in chamber['atoms']), [])
        enough = len(reservoir) >= (3 if c['mode'] == 'uncoupled' else 1) and (c['mode'] == 'uncoupled' or len(stored) >= 2)
        if not enough:
            result['outcome'] = 'starved'
        else:
            release_debit = charge(reservoir, 1)
            emit_heat(1)
            if c['mode'] == 'uncoupled':
                transfer = charge(reservoir, 2)
            else:
                transfer = stored[:2]
                for uid in transfer:
                    for aid in chamber['atoms']:
                        if uid in s['activation'][aid]:
                            s['activation'][aid].remove(uid)
                            break
                result['spent'] += transfer
            paid = chamber['debits']+release_debit+transfer
            need(len(paid) == 3*len(parent['atoms'])+1 and len(set(paid)) == len(paid), 'Unchanged full construction debit')
            own = all(s['units'][uid]['actor'] == who and s['units'][uid]['origin'] in ['harvest', 'activation'] for uid in paid)
            bits = ''.join(s['atoms'][aid]['bit'] for aid in chamber['atoms'])
            ghost = c['mode'] == 'ghost'
            endowed = [] if ghost else list(transfer)
            if ghost:
                emit_heat(2)
            history = {'origin': 'ghost' if ghost else 'construction', 'producer': who,
                       'template': None if c['mode'] == 'untemplated' else who, 'born_tick': tick,
                       'bits': bits, 'atoms': list(chamber['atoms']), 'work': list(endowed),
                       'bonds': list(chamber['bonds']), 'supplied_bonds': 0, 'construction_debits': paid,
                       'matching': bits == parent['bits'], 'producer_funded': own,
                       'components': [{'atom': aid, 'activation_units': [uid for uid, v in s['units'].items() if v['carrier'] == aid]} for aid in chamber['atoms']]}
            s['history'][material] = history
            s['objects'][material] = {'bits': bits, 'atoms': list(chamber['atoms']), 'work': list(endowed), 'bonds': list(chamber['bonds']), 'supplied_bonds': 0}
            s['channels'][who] = empty_channel()
            s['channels'][material] = empty_channel()
            result.update(outcome='ghost_constructed' if ghost else 'constructed', endowed=endowed,
                          product=material, producer_funded=own, matching=history['matching'])
    return s, result


def verify_record(record, expected):
    need(record['config'] == expected, 'Registered configuration')
    state = genesis(expected)
    need(record['initial'] == state, 'Genesis source/assets')
    conserved, chain = balance(state), sha(state)
    program = schedule(expected)
    need(len(record['events']) == len(program), 'Complete event sequence')
    for tick, (req, event) in enumerate(zip(program, record['events'])):
        before = sha(state)
        state, result = advance(state, expected, tick, req)
        need(balance(state) == conserved, 'Mass/energy conservation')
        predicted = dict(tick=tick, request=req, before=before, after=sha(state), previous=chain, result=result)
        predicted['sha256'] = sha(predicted)
        need(event == predicted, 'Semantic event/chain/provenance')
        chain = predicted['sha256']
    need(record['terminal'] == state, 'Terminal semantic state/ancestry')
    births = [state['history'][oid] for oid in ('D0', 'D1') if oid in state['history']]
    function = {event['request'][1] for event in record['events'] if event['request'][0] == 'probe' and event['result']['outcome'] == 'captured'}
    funded = {oid for oid in ('D0', 'D1') if oid in state['history'] and state['history'][oid]['origin'] == 'construction' and state['history'][oid]['matching'] and state['history'][oid]['producer_funded']}
    stats = dict(cases=1, constructions=sum(b['origin'] == 'construction' for b in births),
                 ghosts=sum(b['origin'] == 'ghost' for b in births), matching=sum(b['matching'] for b in births),
                 probe_functions=len(function), matching_functional=sum(oid in function and state['history'][oid]['matching'] for oid in ('D0', 'D1') if oid in state['history']),
                 producer_funded_functional=len(function & funded), renewed_functional=int({'D0', 'D1'} <= function & funded),
                 second_functional=int('D1' in function), second_producer_funded_functional=int('D1' in function & funded),
                 mismatches=sum(e['result']['outcome'] == 'mismatch' for e in record['events']),
                 starved=sum(e['result']['outcome'] == 'starved' for e in record['events']),
                 overflow=sum(len(e['result']['overflow']) for e in record['events']),
                 external_activation=sum(cap['carrier'] is not None and cap['actor'].startswith('environment') for cap in state['captures']),
                 terminal_heat=state['heat'])
    return stats


def audit(directory, revision):
    directory = Path(directory)
    need(len(revision) == 40 and all(x in '0123456789abcdef' for x in revision), 'Exact revision')
    summary = json.loads((directory/'summary.json').read_bytes(), object_pairs_hook=unique)
    need(summary['revision'] == revision and summary['schema'] == 'energy02-summary-v1', 'Source identity')
    expected_hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
    need(summary['source_sha256'] == expected_hashes, 'Frozen source hashes')
    groups, support, checksum, count, events = {}, {}, hashlib.sha256(), 0, 0
    with (directory/'records.jsonl').open('rb') as stream:
        for config in panel():
            line = stream.readline()
            need(line, 'Missing registered case')
            checksum.update(line)
            record = json.loads(line, object_pairs_hook=unique)
            stats = verify_record(record, config)
            key = '/'.join([config['kind'], str(len(config['bits'])), config['mode'], config['source']])
            row = groups.setdefault(key, {k: 0 for k in stats})
            for k, value in stats.items():
                row[k] += value
            if config['kind'] == 'primary' and config['mode'] == 'coupled' and config['source'] == 'producer' and stats['producer_funded_functional']:
                key = f"n{len(config['bits'])}/budget{config['budget']}/fuel{config['fuel']}"
                support[key] = support.get(key, 0)+1
            count += 1
            events += len(record['events'])
        need(not stream.read(1), 'Unexpected extra records')
    passed = any(k.startswith('primary/') and '/coupled/producer' in k and v['producer_funded_functional'] for k, v in groups.items())
    expected = dict(schema='energy02-summary-v1', revision=revision, source_sha256=expected_hashes,
                    records_sha256=checksum.hexdigest(), authored_cases=count, events=events, natural_worlds=0,
                    reserved_samples_executed=False, groups=groups, producer_feasible_conditions=support,
                    possibility_passed=bool(passed), decision='assess_startup_and_kinetics_before_neutral_protocol' if passed else 'close_negative_precursor_hypothesis',
                    no_natural_reproduction_claim=True)
    need(summary == expected and count == 9264 and events == 189120, 'Independent complete summary')
    return dict(schema='energy02-audit-v1', revision=revision, authored_cases=count, events=events,
                conservation_and_unique_provenance=True, elementary_prices_and_births_verified=True,
                external_subsidies_explicit=True, possibility_passed=bool(passed),
                records_sha256=checksum.hexdigest(), natural_worlds=0, no_emergence_claim=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.input_dir, args.source_revision), sort_keys=True))

