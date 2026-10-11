"""COLLISION-BRIDGE-01: exact finite authored digital-physics histories."""
from fractions import Fraction as F
import json

ARMS = ('candidate', 'direct', 'assembly_disabled', 'shuffle_identity', 'shuffle_exchange')
RANK = {name: i for i, name in enumerate(('a0', 'a1', 's0', 's1', 's2', 'load'))}


def mass(body):
    return sum(4 if member == 'load' else 1 for member in body['members'])


def energy(body):
    return F(mass(body), 2) * body['v']**2


class World:
    def __init__(self, arm):
        if arm not in ARMS:
            raise ValueError('Unknown authored arm')
        self.arm = arm
        entries = [('s0', -30, 2), ('s1', -150, 2), ('s2', -350, 2),
                   ('a0', -1, 1), ('a1', 1, -1), ('load', 30, 0)]
        if arm == 'direct':
            entries[3:5] = [('a0', -1400, 1), ('a1', -1500, -1)]
        if arm == 'shuffle_exchange':
            entries[3:5] = [('a0', -1, -1), ('a1', 1, 1)]
        self.bodies = [dict(id='raw:'+n, members=[n], x=F(x), v=F(v), bonds=[])
                       for n, x, v in entries]
        self.t = F(0)
        self.heat = F(0)
        self.bill = F(0)
        self.serial = 0
        self.bond_serial = 0
        self.first = {}
        self.events = []
        self.lost = False
        self.loss_bill = None
        self.loss_load = None
        self.loss_bonds = None
        self.loss_unused = None
        self.rebuilt = []
        self.rebuilt_work = F(0)
        self.check()

    def order(self):
        self.bodies.sort(key=lambda b: (b['x'], min(RANK[n] for n in b['members'])))

    def load(self):
        b = next(b for b in self.bodies if 'load' in b['members'])
        if b['members'] != ['load']:
            raise ValueError('Load cannot associate')
        return energy(b)

    def check(self):
        names = [n for b in self.bodies for n in b['members']]
        assert sorted(names) == sorted(RANK)
        assert sum(mass(b) for b in self.bodies) == 9
        assert sum(mass(b)*b['v'] for b in self.bodies) == 6
        assert sum(energy(b)+len(b['bonds']) for b in self.bodies)+self.heat == 7
        assert self.heat >= 0 and self.bill >= 0

    def snapshot(self):
        self.order()
        return dict(time=str(self.t), heat=str(self.heat), formation_bill=str(self.bill),
            next_object=self.serial, next_bond=self.bond_serial,
            first_source_contact={k: str(v) for k, v in sorted(self.first.items())},
            objects=[dict(id=b['id'], members=b['members'], x=str(b['x']), v=str(b['v']),
                          mass=mass(b), bonds=b['bonds']) for b in self.bodies])

    def new_id(self):
        result = 'object:'+str(self.serial)
        self.serial += 1
        return result

    def contact(self):
        self.order()
        options = []
        for i in range(len(self.bodies)-1):
            a, b = self.bodies[i:i+2]
            if a['v'] > b['v']:
                options.append(((b['x']-a['x'])/(a['v']-b['v']), i))
        return min(options) if options else (None, None)

    def advance(self, delta):
        for b in self.bodies:
            b['x'] += b['v']*delta
        self.t += delta

    def step(self, kind, delta, index=None):
        before = self.snapshot()
        old_heat, old_bill, old_load = self.heat, self.bill, self.load()
        self.advance(delta)
        parents = []
        newborn = None
        if kind == 'collision':
            a, b = self.bodies[index:index+2]
            assert a['x'] == b['x'] and a['v'] > b['v']
            parents = [a['id'], b['id']]
            for name in a['members']+b['members']:
                if name.startswith('s') and name not in self.first:
                    self.first[name] = self.t
            m, n, u, v = mass(a), mass(b), a['v'], b['v']
            relative = F(m*n, 2*(m+n))*(u-v)**2
            if self.arm != 'assembly_disabled' and 'load' not in a['members']+b['members'] and relative >= 1:
                bid = 'bond:'+str(self.bond_serial)
                self.bond_serial += 1
                newborn = self.new_id()
                c = dict(id=newborn, members=sorted(a['members']+b['members'], key=RANK.get),
                    x=a['x'], v=(m*u+n*v)/(m+n), bonds=a['bonds']+b['bonds']+[bid])
                self.heat += relative-1
                self.bill += relative
                self.bodies[index:index+2] = [c]
                if self.lost and {'a0', 'a1'} <= set(c['members']):
                    self.rebuilt.append(newborn)
                channel = 'associate'
            else:
                a['v'], b['v'] = ((m-n)*u+2*n*v)/(m+n), (2*m*u+(n-m)*v)/(m+n)
                channel = 'elastic'
                if self.lost and ('load' in a['members']+b['members']):
                    partner = b if 'load' in a['members'] else a
                    if partner['id'] in self.rebuilt:
                        self.rebuilt_work += self.load()-old_load
        elif kind == 'damage':
            self.loss_bill, self.loss_load = self.bill, old_load
            self.loss_bonds = sum(len(b['bonds']) for b in self.bodies)
            self.loss_unused = sorted(set(('s0', 's1', 's2'))-set(self.first))
            replacement = []
            for b in self.bodies:
                if b['bonds']:
                    parents.append(b['id'])
                    self.heat += len(b['bonds'])
                    for name in b['members']:
                        replacement.append(dict(id=self.new_id(), members=[name], x=b['x'], v=b['v'], bonds=[]))
                else:
                    replacement.append(b)
            self.bodies = replacement
            self.lost = True
            channel = 'all_bonds_to_heat'
        elif kind == 'finish':
            channel = 'finite_horizon'
        else:
            raise ValueError('Unknown event')
        self.check()
        self.events.append(dict(kind=kind, delta=str(delta), channel=channel, parents=parents,
            newborn=newborn, formation_debit=str(self.bill-old_bill), heat_delta=str(self.heat-old_heat),
            load_work=str(self.load()-old_load), before=before, after=self.snapshot()))

    def run(self):
        for _ in range(514):
            delta, index = self.contact()
            boundary = F(128) if not self.lost else F(512)
            if delta is None or self.t+delta >= boundary:
                self.step('damage' if not self.lost else 'finish', boundary-self.t)
                if boundary == 512:
                    break
            else:
                if sum(e['kind'] == 'collision' for e in self.events) >= 512:
                    raise RuntimeError('Registered contact cap exceeded')
                self.step('collision', delta, index)
        else:
            raise RuntimeError('Registered event cap exceeded')
        whole = self.load()-self.bill
        post = self.load()-self.loss_load-(self.bill-self.loss_bill)
        score = dict(retained_load=str(self.load()), whole_formation=str(self.bill),
            whole_margin=str(whole), post_load=str(self.load()-self.loss_load),
            post_formation=str(self.bill-self.loss_bill), post_margin=str(post),
            loss_bonds=self.loss_bonds, unused_sources_at_loss=self.loss_unused,
            rebuilt_objects=self.rebuilt, rebuilt_load_work=str(self.rebuilt_work),
            success=bool(self.loss_bonds and self.rebuilt and self.rebuilt_work > 0
                         and whole > 0 and post > 0 and self.loss_unused))
        return dict(arm=self.arm, initial=self.events[0]['before'], events=self.events, score=score)


def fixtures():
    return dict(schema='collision-bridge01-v1', scope='Five authored finite digital-law histories',
                natural_worlds=0, records=[World(a).run() for a in ARMS])


if __name__ == '__main__':
    print(json.dumps(fixtures(), sort_keys=True, separators=(',', ':')))
