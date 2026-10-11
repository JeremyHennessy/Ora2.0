"""Authored finite digital ledger. Controlled commands, never an autonomous actor."""
import json


class Ledger:
    def __init__(self, energies, materials=4, capital=128):
        if any(type(e) is not int or e < 1 for e in energies):
            raise ValueError('Positive integer fuel quanta required')
        self.fuel = dict(enumerate(energies))
        self.initial_fuel = sum(energies)
        self.initial_capital = self.capital = capital
        self.raw = set(range(materials))
        self.initial_materials = materials
        self.roles = {}
        self.packets = {}
        self.heat = self.load = 0
        self.events = []

    def command(self, op, role=None, packet=None, kind=None):
        # Check every prerequisite before the paid action; failed requests do
        # not alter a ledger. Request selection is supplied, paid assistance.
        if op == 'form':
            if role in self.roles or not self.raw or kind not in ('C', 'L', 'B'):
                raise ValueError('Formation requires vacant role and raw material')
            cost = 6  # four structural quanta, one formation loss, one command.
        elif op == 'intake':
            if packet not in self.fuel:
                raise ValueError('Fuel already acquired or absent')
            cost = 1  # finite resource access, charged on every packet.
        elif op in ('convert', 'release', 'store', 'take', 'hold'):
            required = {'convert':'C', 'release':'L', 'store':'B', 'take':'B'}
            if role not in self.roles or (op in required and self.roles[role]['kind'] != required[op]):
                raise ValueError('Functional role absent')
            if packet not in self.packets:
                raise ValueError('Acquired packet absent')
            p = self.packets[packet]
            if op == 'convert' and (p['state'] != 'raw' or p['holder'] is not None or p['energy'] <= 2 or self.roles[role]['held'] is not None):
                raise ValueError('Conversion needs raw fuel and vacant converter')
            if op == 'release' and (p['state'] != 'product' or p['holder'] is None):
                raise ValueError('No converted output')
            if op == 'store' and (p['state'] != 'raw' or p['holder'] is not None or self.roles[role]['held'] is not None):
                raise ValueError('Storage needs free raw packet and empty buffer')
            if op in ('take', 'hold') and p['holder'] != role:
                raise ValueError('Packet is not held by this role')
            cost = 1
        else:
            raise ValueError('Unknown operation')
        if self.capital < cost:
            raise ValueError('Paid capital exhausted')
        self.capital -= cost
        self.heat += cost
        if op == 'form':
            material = min(self.raw); self.raw.remove(material)
            self.roles[role] = dict(kind=kind, material=material, binding=4, held=None)
            self.heat -= 4
        elif op == 'intake':
            self.packets[packet] = dict(energy=self.fuel.pop(packet), state='raw', holder=None, ancestors=[packet])
        else:
            p = self.packets[packet]
            if op == 'convert':
                p['energy'] -= 2; self.heat += 2
                p['state'] = 'product'; p['holder'] = role
                self.roles[role]['held'] = packet
            elif op == 'release':
                owner = p['holder']; self.roles[owner]['held'] = None
                self.load += p['energy']; del self.packets[packet]
            elif op == 'store':
                p['holder'] = role; self.roles[role]['held'] = packet
            elif op == 'take':
                p['holder'] = None; self.roles[role]['held'] = None
            r = self.roles[role]; r['binding'] -= 1; self.heat += 1
            if r['binding'] == 0:
                if r['held'] is not None:
                    self.heat += self.packets.pop(r['held'])['energy']
                self.raw.add(r['material']); del self.roles[role]
        self.check()
        self.events.append(dict(op=op, role=role, packet=packet, kind=kind, state=self.snapshot()))

    def check(self):
        total = self.capital + self.heat + self.load + sum(self.fuel.values())
        total += sum(p['energy'] for p in self.packets.values())
        total += sum(r['binding'] for r in self.roles.values())
        if total != self.initial_capital + self.initial_fuel:
            raise AssertionError('Energy creation or loss')
        if len(self.raw) + len(self.roles) != self.initial_materials:
            raise AssertionError('Material creation or loss')
        for name, r in self.roles.items():
            if r['held'] is not None and self.packets[r['held']]['holder'] != name:
                raise AssertionError('Duplicated or orphaned holder')
        for i, p in self.packets.items():
            if p['holder'] is not None and self.roles[p['holder']]['held'] != i:
                raise AssertionError('Orphaned packet')

    def snapshot(self):
        return dict(capital=self.capital, heat=self.heat, load=self.load,
                    raw=sorted(self.raw), fuel=dict(self.fuel),
                    roles={k:dict(v) for k,v in self.roles.items()},
                    packets={k:dict(v) for k,v in self.packets.items()})


def ordinary(energy):
    x = Ledger([energy]*4)
    x.command('form', 'converter', kind='C')
    x.command('form', 'receiver', kind='L')
    for p in range(4):
        x.command('intake', packet=p)
        if energy > 2:
            x.command('convert', 'converter', p)
            if p in x.packets:  # Exhausted converter destroys its last held output.
                x.command('release', 'receiver', p)
    return dict(energy=energy, gross=x.load, paid=x.initial_capital-x.capital,
                net=x.load-(x.initial_capital-x.capital), events=x.events, final=x.snapshot())


def preflight():
    # The positive witness goes through construction and the same endpoint.
    positive = ordinary(16)
    absent = Ledger([16]); absent.command('form', 'converter', kind='C')
    absent.command('intake', packet=0); absent.command('convert', 'converter', 0)
    before = absent.snapshot()
    try:
        absent.command('release', 'receiver', 0)
    except ValueError as e:
        refusal = str(e)
    else:
        raise AssertionError('Impossible receiver witness exported work')
    assert absent.snapshot() == before and absent.load == 0
    buffer = Ledger([16])
    for name, kind in [('c','C'), ('l','L'), ('b','B')]:
        buffer.command('form', name, kind=kind)
    buffer.command('intake', packet=0)
    for op in ('store', 'hold', 'take'):
        buffer.command(op, 'b', 0)
    buffer.command('convert', 'c', 0); buffer.command('release', 'l', 0)
    return dict(classification='CONTROLLED_ORDINARY_ROUTE_ONLY', positive=positive,
                missing_receiver=dict(refusal=refusal, final=absent.snapshot(), events=absent.events),
                buffer_witness=dict(events=buffer.events, final=buffer.snapshot()),
                all_source_sizes=[ordinary(e) for e in range(1,17)],
                candidate_whole=None, candidate_fresh=None, comparator_fresh=None,
                damage_exposure=None, fresh_replacement=None, natural_worlds=0)


if __name__ == '__main__':
    print(json.dumps(preflight(), sort_keys=True, separators=(',', ':')))
