"""Independent event interpreter: deliberately does not import the worker."""
from fractions import Fraction
import json
import sys


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Ambiguous duplicate JSON field')
        result[key] = value
    return result


def state(record):
    if set(record) != {'members', 'recipient', 'binding', 'capacity', 'excitation', 'bound', 'contact'}:
        raise ValueError('State schema')
    members = record['members']
    if type(members) is not list or len(members) != 2:
        raise ValueError('Pair identities')
    identities = [*members, record['recipient']]
    if any(type(x) is not str or not x or not x.isascii() for x in identities) or len(set(identities)) != 3:
        raise ValueError('Material identities')
    if type(record['binding']) is not str:
        raise ValueError('Exact energy serialization')
    b = Fraction(record['binding'])
    if b <= 0 or str(b) != record['binding']:
        raise ValueError('Positive canonical rational energy')
    c, n = record['capacity'], record['excitation']
    if type(c) is not int or c <= 0 or type(n) is not int or not 0 <= n <= c:
        raise ValueError('Finite recipient capacity')
    if type(record['bound']) is not bool or type(record['contact']) is not bool:
        raise ValueError('Physical coordinates')
    return b, (n - int(record['bound'])) * b


def audit_event(event):
    if set(event) != {'schema', 'before', 'after', 'outcome', 'recipient_transfer', 'useful_work'} or event['schema'] != 'association-channel01-event':
        raise ValueError('Event schema')
    p, q = event['before'], event['after']
    b, ep = state(p)
    _, eq = state(q)
    for key in ('members', 'recipient', 'binding', 'capacity', 'contact'):
        if p[key] != q[key]:
            raise ValueError('Unrepresented material/contact/capacity intervention')
    if ep != eq:
        raise ValueError('Energy imbalance')
    # Derive the expected permutation from the registered local state table.
    expected = dict(p)
    if not p['contact']:
        direction = 'no-contact'
    elif p['bound'] and p['excitation'] == 0:
        direction = 'recipient-empty'
    elif not p['bound'] and p['excitation'] == p['capacity']:
        direction = 'recipient-full'
    else:
        direction = 'release' if p['bound'] else 'associate'
        expected['bound'] = not p['bound']
        expected['excitation'] += -1 if p['bound'] else 1
    if q != expected or event['outcome'] != direction:
        raise ValueError('Wrong transition')
    transfer = (q['excitation'] - p['excitation']) * b
    if event['recipient_transfer'] != str(transfer) or event['useful_work'] != '0':
        raise ValueError('Unpaid transfer or false useful-work claim')
    return dict(energy=str(ep), recipient_transfer=str(transfer), useful_work='0')


def audit_fixture(receipt):
    if set(receipt) != {'schema', 'events', 'scope', 'worlds', 'whole_life_surplus', 'post_damage_surplus', 'comparator_profit', 'self_maintenance'}:
        raise ValueError('Fixture schema')
    if receipt['schema'] != 'association-channel01-fixture' or receipt['scope'] != 'Prepared-contact reversible prerequisite only':
        raise ValueError('Fixture scope')
    if type(receipt['worlds']) is not int or receipt['worlds'] != 0 or receipt['self_maintenance'] is not False:
        raise ValueError('False admission')
    if any(receipt[k] is not None for k in ('whole_life_surplus', 'post_damage_surplus', 'comparator_profit')):
        raise ValueError('Unmeasured surplus')
    events = receipt['events']
    if type(events) is not list or len(events) != 5:
        raise ValueError('Registered five-event fixture required')
    interpreted = [audit_event(e) for e in events]
    initial = dict(members=['raw-a', 'raw-b'], recipient='raw-recipient', binding='3/2',
                   capacity=2, excitation=0, bound=False, contact=True)
    expected_inputs = [initial, dict(initial, bound=True, excitation=1),
                       dict(initial, excitation=2), dict(initial, bound=True),
                       dict(initial, contact=False)]
    if [e['before'] for e in events] != expected_inputs:
        raise ValueError('Fixture substitution')
    if events[0]['after'] != events[1]['before'] or events[1]['after'] != initial:
        raise ValueError('Reversal is not exact')
    return dict(verified=True, events=5, forward_transfer='3/2', reverse_transfer='-3/2',
                cycle_recipient_net='0', exported_work='0',
                retained_assembly=False, whole_life_surplus=None, comparator_profit=None,
                interpretation=interpreted)


if __name__ == '__main__':
    print(json.dumps(audit_fixture(json.load(sys.stdin, object_pairs_hook=unique_object)), sort_keys=True))
