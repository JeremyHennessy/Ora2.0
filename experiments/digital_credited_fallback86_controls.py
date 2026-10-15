"""Trusted late-history adapter over unchanged MEMORY80 paid transitions.

No execution admission is granted by importing this module or constructing a
runtime. World construction is reserved for separately registered custody roles.
Bookkeeping and intervention receipts are external to the physical World schema.
"""
import weakref
from experiments import digital_memory80 as engine
from experiments import digital_credited_fallback86_source as source

WARM = 48
DECISIONS = 60
HORIZON = 1024
_RUNTIME = weakref.WeakKeyDictionary()


class Runtime:
    def __init__(self, initial_route, control):
        assert type(initial_route) is str and initial_route in source.ENTRIES
        assert type(control) is str and control in source.CONTROLS
        self.initial_route = initial_route
        self.control = control
        self.completed = 0
        self.pending = None
        self.dispatch_pc = None
        self.ledger = []

    @property
    def active(self):
        return self.completed >= WARM

    def before(self, entity):
        assert type(entity) is dict and type(entity['pc']) is int and 0 <= entity['pc'] < 21
        entry = None
        if self.pending is not None:
            previous, actual = self.pending
            assert entity['pc'] == actual
            projected = source.entry_after_completed_decision(
                previous, actual, self.initial_route, self.control, self.active)
            entry = dict(previous_pc=previous, actual_entry=actual,
                         projected_entry=projected, completed=self.completed,
                         active=int(self.active))
            entity['pc'] = projected
            self.pending = None
        self.dispatch_pc = entity['pc']
        return entry

    def read(self, memory, index):
        assert type(index) is int and 0 <= index < 16
        assert type(self.dispatch_pc) is int and self.dispatch_pc in (7, 12)
        physical = list(memory)
        address = index % len(physical)
        origin = address
        if self.active and self.control in ('model_erased', 'history_disabled'):
            origin = None
        elif self.active and self.control == 'model_misbound':
            origin = (address + len(physical)//2) % len(physical)
        return dict(pc=self.dispatch_pc, index=index, address=address,
                    source_address=origin, truthful_cell=physical[address],
                    value=source.model_read(self.dispatch_pc, physical, index,
                                            self.control, self.active),
                    active=int(self.active))

    def after(self, event):
        assert self.pending is None
        after = event.get('after')
        completion = None
        if after is not None:
            assert type(after['pc']) is int and 0 <= after['pc'] < 21
            assert type(after['energy']) is int and after['energy'] > 0
        if after is not None and (self.dispatch_pc, after['pc']) in source.BOUNDARIES:
            self.completed += 1
            self.pending = (self.dispatch_pc, after['pc'])
            completion = dict(completed=self.completed, previous_pc=self.dispatch_pc,
                              entry=after['pc'], energy=after['energy'])
        return completion


class ModelView(list):
    def __init__(self, values, runtime):
        super().__init__(values)
        self.runtime = runtime

    def __getitem__(self, index):
        return self.runtime.read(self, index)['value']


class World(engine.World):
    def __init__(self, seed, capacity, initial_route, control):
        assert type(seed) is int and seed in engine.SOFTWARE
        runtime = Runtime(initial_route, control)
        programme = source.programme(capacity, initial_route)
        super().__init__(seed, capacity, 'no_variation', 1, 0, programme)
        self.entities[0]['memory'] = ModelView(self.entities[0]['memory'], runtime)
        _RUNTIME[self] = runtime

    def done(self):
        return not self.entities or self.tick >= HORIZON or _RUNTIME[self].completed >= DECISIONS

    def step(self):
        if self.done():
            return False
        runtime = _RUNTIME[self]
        entity = self.entities[0]
        completed_before = runtime.completed
        entry = runtime.before(entity)
        pc = runtime.dispatch_pc
        read = runtime.read(entity['memory'], entity['registers'][1]) if pc in (7, 12) else None
        assert engine.World.step(self)
        event = self.events[-1]
        completion = runtime.after(event)
        runtime.ledger.append(dict(tick=event['tick'], dispatch_pc=pc,
            completed_before=completed_before, entry=entry, read=read,
            completion=completion))
        return True

    def control_ledger(self):
        """Borrow only after the final step, under the terminal-view discipline."""
        return _RUNTIME[self].ledger

    def run(self, horizon=HORIZON):
        raise RuntimeError('Registered custody must use bounded step loop and terminal_view')
