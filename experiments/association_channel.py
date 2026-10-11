"""Finite reversible digital recipient; no converter, movement or useful load."""
from dataclasses import dataclass, replace
from fractions import Fraction
import json


@dataclass(frozen=True)
class State:
    members: tuple[str, str]
    recipient: str
    binding: Fraction
    capacity: int
    excitation: int
    bound: bool
    contact: bool

    def __post_init__(self):
        if type(self.members) is not tuple or len(self.members) != 2:
            raise ValueError('Two material members required')
        ids = (*self.members, self.recipient)
        if any(type(x) is not str or not x or not x.isascii() for x in ids) or len(set(ids)) != 3:
            raise ValueError('Three distinct explicit material identities required')
        if type(self.binding) is not Fraction or self.binding <= 0:
            raise ValueError('Exact positive rational binding energy required')
        if type(self.capacity) is not int or self.capacity <= 0:
            raise ValueError('Finite positive integer capacity required')
        if type(self.excitation) is not int or not 0 <= self.excitation <= self.capacity:
            raise ValueError('Recipient outside finite state space')
        if type(self.bound) is not bool or type(self.contact) is not bool:
            raise ValueError('Explicit binding and contact coordinates required')

    def record(self):
        return dict(members=list(self.members), recipient=self.recipient,
                    binding=str(self.binding), capacity=self.capacity,
                    excitation=self.excitation, bound=self.bound, contact=self.contact)

    def energy(self):
        return (self.excitation - int(self.bound)) * self.binding


def step(before: State) -> dict:
    """One time-symmetric local state permutation, with bounded refusals."""
    after = before
    transfer = Fraction(0)
    if not before.contact:
        outcome = 'no-contact'
    elif not before.bound and before.excitation == before.capacity:
        outcome = 'recipient-full'
    elif before.bound and before.excitation == 0:
        outcome = 'recipient-empty'
    elif before.bound:
        outcome = 'release'
        after = replace(before, bound=False, excitation=before.excitation - 1)
        transfer = -before.binding
    else:
        outcome = 'associate'
        after = replace(before, bound=True, excitation=before.excitation + 1)
        transfer = before.binding
    if after.energy() != before.energy():
        raise ArithmeticError('Energy conservation violated')
    return dict(schema='association-channel01-event', before=before.record(),
                after=after.record(), outcome=outcome,
                recipient_transfer=str(transfer), useful_work='0')


def fixtures() -> dict:
    initial = State(('raw-a', 'raw-b'), 'raw-recipient', Fraction(3, 2), 2, 0, False, True)
    first = step(initial)
    intermediate = replace(initial, bound=True, excitation=1)
    events = [first, step(intermediate),
              step(replace(initial, excitation=2)),
              step(replace(initial, bound=True)),
              step(replace(initial, contact=False))]
    return dict(schema='association-channel01-fixture', events=events,
                scope='Prepared-contact reversible prerequisite only', worlds=0,
                whole_life_surplus=None, post_damage_surplus=None,
                comparator_profit=None, self_maintenance=False)


if __name__ == '__main__':
    print(json.dumps(fixtures(), sort_keys=True, separators=(',', ':')))
