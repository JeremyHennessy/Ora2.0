"""Borrow a terminal MEMORY80 record without cloning its event history.

Trusted custody only, not a VM transition or a physics validator. The caller must
stop stepping the world until the existing streaming recorder has consumed this
view. No producer import, target access, new World, or learned state assistance.
"""
FIELDS = frozenset(('seed', 'mode', 'max_population', 'expansion_tick', 'tick',
                    'last', 'next_id', 'writes', 'births', 'deaths', 'offered',
                    'admitted', 'rejected', 'next_packet', 'heat',
                    'constructor_remaining', 'food', 'leases', 'free',
                    'entities', 'events'))
TABLES = ('food', 'leases', 'entities')


def terminal_view(raw):
    if type(raw) is not dict or set(raw) != FIELDS:
        raise ValueError('Exact frozen MEMORY80 terminal fields required')
    view = raw.copy()
    for name in TABLES:
        table = raw[name]
        if type(table) is not dict:
            raise ValueError('Plain terminal table required')
        converted = {}
        for key, value in table.items():
            if type(key) is int and key >= 0:
                text = str(key)
            elif type(key) is str and key.isascii() and key.isdigit() and str(int(key)) == key:
                text = key
            else:
                raise ValueError('Canonical nonnegative integer table key required')
            if text in converted:
                raise ValueError('Table key collision refused')
            converted[text] = value
        view[name] = converted
    return view
