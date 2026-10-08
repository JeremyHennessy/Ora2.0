"""ENERGY-02 authored finite precursor coupling; no natural worlds."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/ENERGY-02-PROTOCOL.md', 'experiments/precursor_coupling.py', 'experiments/precursor_coupling_audit.py')
MODES = ('coupled', 'uncoupled', 'ghost', 'untemplated')


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def configs():
    for n in (2, 3, 4):
        for pattern in itertools.product('01', repeat=n):
            bits = ''.join(pattern)
            candidates = (bits, str(1-int(bits[0]))+bits[1:], bits[:-1]+str(1-int(bits[-1])))
            for candidate, budget, fuel, mode, source in itertools.product(candidates, range(n+1), (0, n, 2*n), MODES, ('producer', 'external')):
                yield dict(kind='primary', bits=bits, candidate=candidate, budget=budget, fuel=fuel, mode=mode, source=source, phases=1)
            for mode, source in itertools.product(MODES, ('producer', 'external', 'withdrawn')):
                yield dict(kind='renewal', bits=bits, candidate=bits, budget=n, fuel=2*n, mode=mode, source=source, phases=2)


def requests(c):
    n = len(c['bits'])
    for phase in range(c['phases']):
        actor = 'C' if phase == 0 else 'D0'
        for i in range(n):
            yield ['harvest', actor, f'F{phase}.{2*i}', None]
            yield ['harvest', actor, f'F{phase}.{2*i+1}', None]
            yield ['activate', actor, f'M{phase}.{i}', f'A{phase}.{i}']
        for i in range(n):
            yield ['recognize', actor, f'M{phase}.{i}', None]
            yield ['ligate', actor, None, None]
        yield ['release', actor, f'D{phase}', None]
        yield ['probe', f'D{phase}', f'P{phase}', None]


def external(c, phase):
    return c['source'] == 'external' or c['source'] == 'withdrawn' and phase == 0


def channel():
    return dict(atoms=[], pending=None, bonds=[], debits=[])


def initial(c):
    n = len(c['bits'])
    s = dict(atoms={}, units={}, objects={}, history={}, channels={'C': channel()},
             activation={}, environment={}, ready=[], food=[], waste=[], heat=0, captures=[])
    body = [f'B{i}' for i in range(n)]
    for aid, bit in zip(body, c['bits']):
        s['atoms'][aid] = dict(bit=bit, kind='template', root='external_supply')
    work = [f'G{i}' for i in range(c['budget'])]
    for uid in work:
        s['units'][uid] = dict(origin='genesis', actor='C', food=None, carrier=None, tick=-1)
    obj = dict(bits=c['bits'], atoms=body, work=work, bonds=[], supplied_bonds=n-1)
    s['objects']['C'] = obj
    s['history']['C'] = dict(origin='supplied_template', producer=None, template=None,
                            born_tick=-1, bits=c['bits'], atoms=list(body), work=list(work),
                            bonds=[], supplied_bonds=n-1, construction_debits=[], matching=None,
                            producer_funded=False, components=[dict(atom=a, activation_units=[]) for a in body])
    for phase in range(c['phases']):
        for i, bit in enumerate(c['candidate']):
            aid = f'M{phase}.{i}'
            s['atoms'][aid] = dict(bit=bit, kind='precursor', root='external_supply')
            s['ready'].append(aid)
            s['activation'][aid] = []
        foods = [f'A{phase}.{i}' for i in range(n)]+[f'F{phase}.{i}' for i in range(c['fuel'])]+[f'P{phase}']
        for aid in foods:
            s['atoms'][aid] = dict(bit=str(1-int(c['bits'][-1])), kind='food', root='external_supply')
        s['food'].extend(foods)
        account = [f'E{phase}.{i}' for i in range(2*n)] if external(c, phase) else []
        s['environment'][str(phase)] = account
        for uid in account:
            s['units'][uid] = dict(origin='external_work', actor=f'environment{phase}', food=None, carrier=None, tick=-1)
    return s


def step(old, c, tick, request):
    s = copy.deepcopy(old)
    action, actor, target, donor = request
    obj, ch = s['objects'].get(actor), s['channels'].get(actor)
    r = dict(outcome='unavailable', spent=[], returned=[], endowed=[], overflow=[],
             bond=None, heat=0, product=None, producer_funded=False, matching=None)
    def take(pool, count):
        used = pool[:count]
        del pool[:count]
        r['spent'].extend(used)
        return used
    def warm(amount):
        s['heat'] += amount
        r['heat'] += amount
    def complementary(food):
        return obj is not None and len(obj['bits']) >= 2 and obj['bits'][-1] != s['atoms'][food]['bit']
    if action in ('harvest', 'probe'):
        if target in s['food'] and complementary(target) and len(obj['work']) >= 2:
            take(obj['work'], 2)
            s['food'].remove(target)
            s['waste'].append(target)
            made = [f'R{target}:{tick}:{j}' for j in range(3)]
            for uid in made:
                s['units'][uid] = dict(origin='harvest', actor=actor, food=target, carrier=None, tick=tick)
            count = max(0, len(obj['bits'])-len(obj['work']))
            obj['work'].extend(made[:count])
            r.update(outcome='captured', returned=made, overflow=made[count:])
            warm(7+len(r['overflow']))
            s['captures'].append(dict(actor=actor, food=target, carrier=None, tick=tick, units=made))
        elif target in s['food'] and complementary(target):
            r['outcome'] = 'starved'
    elif action == 'activate':
        phase = int(target[1])
        account = s['environment'][str(phase)] if external(c, phase) else obj['work'] if obj else []
        eligible = external(c, phase) or donor in s['food'] and complementary(donor)
        if target in s['ready'] and not s['activation'][target] and donor in s['food'] and eligible:
            if len(account) >= 2:
                take(account, 2)
                s['food'].remove(donor)
                s['waste'].append(donor)
                producer = f'environment{phase}' if external(c, phase) else actor
                made = [f'R{donor}:{tick}:{j}' for j in range(3)]
                for uid in made:
                    s['units'][uid] = dict(origin='activation', actor=producer, food=donor, carrier=target, tick=tick)
                s['activation'][target].extend(made)
                warm(7)
                s['captures'].append(dict(actor=producer, food=donor, carrier=target, tick=tick, units=made))
                r.update(outcome='activated', returned=made)
            else:
                r['outcome'] = 'starved'
    elif action == 'recognize' and obj and ch['pending'] is None and len(ch['atoms']) < len(obj['bits']) and target in s['ready']:
        pool = obj['work'] if c['mode'] == 'uncoupled' else s['activation'][target]
        if pool:
            ch['debits'].extend(take(pool, 1))
            warm(1)
            if c['mode'] == 'untemplated' or s['atoms'][target]['bit'] == obj['bits'][len(ch['atoms'])]:
                ch['pending'] = target
                s['ready'].remove(target)
                r['outcome'] = 'recognized'
            else:
                r['outcome'] = 'mismatch'
        else:
            r['outcome'] = 'starved'
    elif action == 'ligate' and obj and ch['pending'] is not None:
        aid = ch['pending']
        if not ch['atoms']:
            ch['atoms'].append(aid)
            ch['pending'] = None
            r['outcome'] = 'first_bound'
        else:
            pool = obj['work'] if c['mode'] == 'uncoupled' else s['activation'][aid]
            if len(pool) >= 2:
                used = take(pool, 2)
                ch['debits'].extend(used)
                ch['atoms'].append(aid)
                ch['pending'] = None
                ch['bonds'].append(used[1])
                warm(1)
                r.update(outcome='ligated', bond=used[1])
            else:
                r['outcome'] = 'starved'
    elif action == 'release' and obj and ch['pending'] is None and len(ch['atoms']) == len(obj['bits']):
        potential = [u for aid in ch['atoms'] for u in s['activation'][aid]]
        ready = len(obj['work']) >= (3 if c['mode'] == 'uncoupled' else 1) and (c['mode'] == 'uncoupled' or len(potential) >= 2)
        if ready:
            release = take(obj['work'], 1)
            warm(1)
            if c['mode'] == 'uncoupled':
                endowment = take(obj['work'], 2)
            else:
                endowment = potential[:2]
                for aid in ch['atoms']:
                    s['activation'][aid] = [u for u in s['activation'][aid] if u not in endowment]
                r['spent'].extend(endowment)
            debits = ch['debits']+release+endowment
            funded = all(s['units'][u]['origin'] in ('activation', 'harvest') and s['units'][u]['actor'] == actor for u in debits)
            bits = ''.join(s['atoms'][a]['bit'] for a in ch['atoms'])
            work = endowment if c['mode'] != 'ghost' else []
            if c['mode'] == 'ghost':
                warm(2)
            components = [dict(atom=a, activation_units=[u for u, meta in s['units'].items() if meta['carrier'] == a]) for a in ch['atoms']]
            birth = dict(origin='ghost' if c['mode'] == 'ghost' else 'construction', producer=actor,
                         template=None if c['mode'] == 'untemplated' else actor, born_tick=tick,
                         bits=bits, atoms=list(ch['atoms']), work=list(work), bonds=list(ch['bonds']),
                         supplied_bonds=0, construction_debits=debits, matching=bits == obj['bits'],
                         producer_funded=funded, components=components)
            s['history'][target] = birth
            s['objects'][target] = dict(bits=bits, atoms=list(ch['atoms']), work=list(work), bonds=list(ch['bonds']), supplied_bonds=0)
            s['channels'][actor] = channel()
            s['channels'][target] = channel()
            r.update(outcome='ghost_constructed' if c['mode'] == 'ghost' else 'constructed',
                     endowed=list(work), product=target, producer_funded=funded, matching=birth['matching'])
        else:
            r['outcome'] = 'starved'
    return s, r


def simulate(c):
    s = initial(c)
    genesis = copy.deepcopy(s)
    events, chain = [], digest(s)
    for tick, request in enumerate(requests(c)):
        before = digest(s)
        s, result = step(s, c, tick, request)
        event = dict(tick=tick, request=request, before=before, after=digest(s), previous=chain, result=result)
        event['sha256'] = digest(event)
        events.append(event)
        chain = event['sha256']
    return dict(config=c, initial=genesis, events=events, terminal=s)


def counts(record):
    born = [e['result'] for e in record['events'] if e['result']['product']]
    probes = {e['request'][1] for e in record['events'] if e['request'][0] == 'probe' and e['result']['outcome'] == 'captured'}
    histories = record['terminal']['history']
    funded = [r['product'] for r in born if r['matching'] and r['producer_funded'] and r['outcome'] == 'constructed']
    return dict(cases=1, constructions=sum(r['outcome'] == 'constructed' for r in born),
                ghosts=sum(r['outcome'] == 'ghost_constructed' for r in born),
                matching=sum(r['matching'] is True for r in born),
                probe_functions=len(probes), matching_functional=sum(o in probes for o in histories if o != 'C' and histories[o]['matching']),
                producer_funded_functional=sum(o in probes for o in funded),
                renewed_functional=int('D1' in probes and 'D0' in probes and 'D1' in funded and 'D0' in funded),
                second_functional=int('D1' in probes), mismatches=sum(e['result']['outcome'] == 'mismatch' for e in record['events']),
                second_producer_funded_functional=int('D1' in probes and 'D1' in funded),
                starved=sum(e['result']['outcome'] == 'starved' for e in record['events']),
                overflow=sum(len(e['result']['overflow']) for e in record['events']),
                external_activation=sum(e['result']['outcome'] == 'activated' and record['terminal']['units'][e['result']['returned'][0]]['actor'].startswith('environment') for e in record['events']),
                terminal_heat=record['terminal']['heat'])


def run(output, revision):
    if len(revision) != 40 or any(x not in '0123456789abcdef' for x in revision):
        raise ValueError('Exact source revision required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    total, events, rows, support, digestor = 0, 0, {}, {}, hashlib.sha256()
    with (output/'records.jsonl').open('wb') as stream:
        for c in configs():
            record = simulate(c)
            raw = (encode(record)+'\n').encode()
            stream.write(raw)
            digestor.update(raw)
            total += 1
            events += len(record['events'])
            key = '/'.join((c['kind'], str(len(c['bits'])), c['mode'], c['source']))
            row = rows.setdefault(key, {k: 0 for k in counts(record)})
            for k, value in counts(record).items():
                row[k] += value
            if c['kind'] == 'primary' and c['mode'] == 'coupled' and c['source'] == 'producer' and counts(record)['producer_funded_functional']:
                condition = f"n{len(c['bits'])}/budget{c['budget']}/fuel{c['fuel']}"
                support[condition] = support.get(condition, 0)+1
    feasible = any(key.startswith('primary/') and '/coupled/producer' in key and value['producer_funded_functional'] > 0 for key, value in rows.items())
    summary = dict(schema='energy02-summary-v1', revision=revision,
                   source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},
                   records_sha256=digestor.hexdigest(), authored_cases=total, events=events,
                   natural_worlds=0, reserved_samples_executed=False, groups=rows,
                   producer_feasible_conditions=support,
                   possibility_passed=feasible, decision='assess_startup_and_kinetics_before_neutral_protocol' if feasible else 'close_negative_precursor_hypothesis',
                   no_natural_reproduction_claim=True)
    (output/'summary.json').write_bytes((encode(summary)+'\n').encode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    run(args.output_dir, args.source_revision)
