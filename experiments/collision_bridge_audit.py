"""Independent contract interpreter; does not import the producer."""
from fractions import Fraction as Q
import json
import sys

NAMES = ('a0', 'a1', 's0', 's1', 's2', 'load')
ARMS = ('candidate', 'direct', 'assembly_disabled', 'shuffle_identity', 'shuffle_exchange')


def unique(pairs):
    d = {}
    for key, value in pairs:
        if key in d:
            raise ValueError('Duplicate evidence name')
        d[key] = value
    return d


def m(p):
    return sum(4 if n == 'load' else 1 for n in p[1])


def k(p):
    return Q(m(p), 2)*p[3]*p[3]


def ordered(parts):
    return sorted(parts, key=lambda p: (p[2], min(NAMES.index(n) for n in p[1])))


def view(t, h, c, serial, bond, first, parts):
    return dict(time=str(t), heat=str(h), formation_bill=str(c), next_object=serial,
        next_bond=bond, first_source_contact={n: str(first[n]) for n in sorted(first)},
        objects=[dict(id=p[0], members=list(p[1]), x=str(p[2]), v=str(p[3]),
                      mass=m(p), bonds=list(p[4])) for p in ordered(parts)])


def audit_record(record, arm):
    if set(record) != {'arm', 'initial', 'events', 'score'} or record['arm'] != arm:
        raise ValueError('Wrong history schema or identity')
    locations = dict(s0=(-30, 2), s1=(-150, 2), s2=(-350, 2),
                     a0=(-1, 1), a1=(1, -1), load=(30, 0))
    if arm == 'direct':
        locations.update(a0=(-1400, 1), a1=(-1500, -1))
    if arm == 'shuffle_exchange':
        locations.update(a0=(-1, -1), a1=(1, 1))
    parts = [('raw:'+n, (n,), Q(x), Q(v), ()) for n, (x, v) in locations.items()]
    t = h = c = Q(0)
    serial = bond = 0
    first = {}
    lost = finished = False
    collisions = 0
    rebuilt = []
    rebuilt_work = Q(0)
    loss_c = loss_k = None
    loss_bonds = None
    unused = None
    initial = view(t, h, c, serial, bond, first, parts)
    if record['initial'] != initial or type(record['events']) is not list:
        raise ValueError('Source or raw initial state substituted')
    for observed in record['events']:
        if finished:
            raise ValueError('History beyond horizon')
        parts = ordered(parts)
        before = view(t, h, c, serial, bond, first, parts)
        choices = []
        # Independently derive the earliest unoccluded contact on the line.
        for i, p in enumerate(parts[:-1]):
            r = parts[i+1]
            speed, gap = p[3]-r[3], r[2]-p[2]
            if speed > 0:
                choices.append((gap/speed, i))
        choice = min(choices) if choices else None
        boundary = Q(512 if lost else 128)
        if choice is None or choice[0] >= boundary-t:
            dt, kind, index = boundary-t, ('finish' if lost else 'damage'), None
        else:
            dt, index = choice
            kind = 'collision'
        load_before = next(k(p) for p in parts if 'load' in p[1])
        old_h, old_c = h, c
        parts = [(p[0], p[1], p[2]+dt*p[3], p[3], p[4]) for p in parts]
        t += dt
        parents = []
        newborn = None
        if kind == 'collision':
            collisions += 1
            if collisions > 512:
                raise ValueError('Collision cap exceeded')
            p, r = parts[index:index+2]
            if p[2] != r[2]:
                raise ValueError('Nonlocal collision')
            parents = [p[0], r[0]]
            for name in (*p[1], *r[1]):
                if name in ('s0', 's1', 's2') and name not in first:
                    first[name] = t
            total_mass = m(p)+m(r)
            velocity = (m(p)*p[3]+m(r)*r[3])/total_mass
            relative = k(p)+k(r)-Q(total_mass, 2)*velocity**2
            if arm != 'assembly_disabled' and 'load' not in (*p[1], *r[1]) and relative >= 1:
                newborn = 'object:'+str(serial)
                serial += 1
                members = tuple(sorted((*p[1], *r[1]), key=NAMES.index))
                links = (*p[4], *r[4], 'bond:'+str(bond))
                bond += 1
                parts[index:index+2] = [(newborn, members, p[2], velocity, links)]
                c += relative
                h += relative-1
                channel = 'associate'
                if lost and 'a0' in members and 'a1' in members:
                    rebuilt.append(newborn)
            else:
                difference = p[3]-r[3]
                parts[index] = (p[0], p[1], p[2], velocity-Q(m(r), total_mass)*difference, p[4])
                parts[index+1] = (r[0], r[1], r[2], velocity+Q(m(p), total_mass)*difference, r[4])
                channel = 'elastic'
                if lost and 'load' in (*p[1], *r[1]):
                    partner = r if 'load' in p[1] else p
                    if partner[0] in rebuilt:
                        rebuilt_work += next(k(z) for z in parts if 'load' in z[1])-load_before
        elif kind == 'damage':
            loss_c, loss_k = c, load_before
            loss_bonds = sum(len(p[4]) for p in parts)
            unused = sorted(n for n in ('s0', 's1', 's2') if n not in first)
            dissolved = []
            for p in parts:
                if not p[4]:
                    dissolved.append(p)
                    continue
                parents.append(p[0])
                h += len(p[4])
                for n in p[1]:
                    dissolved.append(('object:'+str(serial), (n,), p[2], p[3], ()))
                    serial += 1
            parts = dissolved
            lost = True
            channel = 'all_bonds_to_heat'
        else:
            channel = 'finite_horizon'
            finished = True
        if sorted(n for p in parts for n in p[1]) != sorted(NAMES):
            raise ValueError('Material ownership')
        if sum(m(p)*p[3] for p in parts) != 6 or sum(k(p)+len(p[4]) for p in parts)+h != 7:
            raise ValueError('Conservation')
        load_after = next(k(p) for p in parts if 'load' in p[1])
        expected = dict(kind=kind, delta=str(dt), channel=channel, parents=parents,
            newborn=newborn, formation_debit=str(c-old_c), heat_delta=str(h-old_h),
            load_work=str(load_after-load_before), before=before,
            after=view(t, h, c, serial, bond, first, parts))
        if expected != observed:
            raise ValueError('Event, ancestry, transport or transfer mismatch')
    if not finished or not lost:
        raise ValueError('Incomplete history')
    load = next(k(p) for p in parts if 'load' in p[1])
    whole, post = load-c, load-loss_k-(c-loss_c)
    score = dict(retained_load=str(load), whole_formation=str(c), whole_margin=str(whole),
        post_load=str(load-loss_k), post_formation=str(c-loss_c), post_margin=str(post),
        loss_bonds=loss_bonds, unused_sources_at_loss=unused, rebuilt_objects=rebuilt,
        rebuilt_load_work=str(rebuilt_work),
        success=bool(loss_bonds and rebuilt and rebuilt_work > 0 and whole > 0 and post > 0 and unused))
    if score != record['score'] or type(record['score'].get('success')) is not bool:
        raise ValueError('False endpoint')
    return dict(arm=arm, collisions=collisions, heat=str(h), score=score)


def audit(receipt):
    if set(receipt) != {'schema', 'scope', 'natural_worlds', 'records'} or receipt['schema'] != 'collision-bridge01-v1':
        raise ValueError('Fixture schema')
    if receipt['scope'] != 'Five authored finite digital-law histories' or type(receipt['natural_worlds']) is not int or receipt['natural_worlds'] != 0:
        raise ValueError('Fixture scope')
    if type(receipt['records']) is not list or len(receipt['records']) != 5:
        raise ValueError('Five histories required')
    rows = [audit_record(r, a) for r, a in zip(receipt['records'], ARMS)]
    scores = {r['arm']: r['score'] for r in rows}
    p, alias = receipt['records'][0], receipt['records'][3]
    if {k: v for k, v in p.items() if k != 'arm'} != {k: v for k, v in alias.items() if k != 'arm'}:
        raise ValueError('Identity shuffle differs')
    candidate, direct, shuffle = (scores[n] for n in ('candidate', 'direct', 'shuffle_exchange'))
    profitable = all(Q(direct[n]) > 0 for n in ('whole_margin', 'post_margin'))
    advantage = all(Q(candidate[n]) > Q(direct[n]) and Q(candidate[n]) > Q(shuffle[n])
                    for n in ('whole_margin', 'post_margin'))
    admitted = candidate['success'] and profitable and advantage
    return dict(verified=True, records=rows, direct_profitable=profitable,
        candidate_advantage=advantage, admitted=admitted, natural_worlds=0,
        scope='Exact authored digital-law feasibility, not life or emergence')


if __name__ == '__main__':
    print(json.dumps(audit(json.load(sys.stdin, object_pairs_hook=unique)), sort_keys=True, indent=2))
