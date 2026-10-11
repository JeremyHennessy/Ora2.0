"""Separate event interpreter; no import of the candidate implementation."""
import json
import sys


def interpret(events, energies):
    capital, heat, load = 128, 0, 0
    source = dict(enumerate(energies)); raw = {0,1,2,3}
    devices, packets = {}, {}
    for e in events:
        op, name, pid = e['op'], e['role'], e['packet']
        if op == 'form':
            assert name not in devices and raw and e['kind'] in ('C','L','B')
            material = min(raw); raw.remove(material)
            capital -= 6; heat += 2
            devices[name] = [e['kind'], material, 4, None]
        elif op == 'intake':
            assert pid in source and pid not in packets
            capital -= 1; heat += 1
            packets[pid] = [source.pop(pid), 'raw', None]
        else:
            assert name in devices and pid in packets
            d, p = devices[name], packets[pid]
            capital -= 1; heat += 2; d[2] -= 1
            if op == 'convert':
                assert d[0] == 'C' and d[3] is None and p[1:] == ['raw',None] and p[0] > 2
                p[0] -= 2; heat += 2; p[1:] = ['product',name]; d[3] = pid
            elif op == 'release':
                assert d[0] == 'L' and p[1] == 'product' and p[2] in devices
                devices[p[2]][3] = None; load += p[0]; del packets[pid]
            elif op == 'store':
                assert d[0] == 'B' and d[3] is None and p[1:] == ['raw',None]
                d[3] = pid; p[2] = name
            elif op == 'take':
                assert d[0] == 'B' and d[3] == pid and p[2] == name
                d[3] = None; p[2] = None
            elif op == 'hold':
                assert d[3] == pid and p[2] == name
            else:
                raise AssertionError('Unknown transition')
            if d[2] == 0:
                if d[3] is not None:
                    heat += packets.pop(d[3])[0]
                raw.add(d[1]); del devices[name]
        assert capital >= 0
        state = dict(capital=capital, heat=heat, load=load, raw=sorted(raw),
                     fuel={str(k):v for k,v in source.items()},
                     roles={k:dict(kind=v[0],material=v[1],binding=v[2],held=v[3]) for k,v in devices.items()},
                     packets={str(k):dict(energy=v[0],state=v[1],holder=v[2],ancestors=[k]) for k,v in packets.items()})
        assert state == e['state'], (op, state, e['state'])
        assert capital+heat+load+sum(source.values())+sum(p[0] for p in packets.values())+sum(d[2] for d in devices.values()) == 128+sum(energies)
        assert len(raw)+len(devices) == 4
    return state


def audit(data):
    assert data['classification'] == 'CONTROLLED_ORDINARY_ROUTE_ONLY'
    rows = data['all_source_sizes']; assert [r['energy'] for r in rows] == list(range(1,17))
    for r in rows + [data['positive']]:
        assert interpret(r['events'], [r['energy']]*4) == r['final']
        # Independently derived endpoint: four uses exhaust C; the fourth
        # product is lost before release, so three retained conversions.
        expected = 3*(r['energy']-2) if r['energy'] > 2 else 0
        paid = 23 if r['energy'] > 2 else 16
        assert (r['gross'],r['paid'],r['net']) == (expected,paid,expected-paid)
    for name in ('missing_receiver', 'buffer_witness'):
        assert interpret(data[name]['events'], [16]) == data[name]['final']
    assert data['missing_receiver']['final']['load'] == 0
    assert 'absent' in data['missing_receiver']['refusal']
    assert data['buffer_witness']['final']['load'] == 14
    assert all(data[k] is None for k in ('candidate_whole','candidate_fresh','comparator_fresh','damage_exposure','fresh_replacement'))
    assert data['natural_worlds'] == 0
    return dict(independent_replay=True, ordinary_whole=19, ordinary_gross=42,
                ordinary_paid=23, profitable_source_sizes=list(range(10,17)),
                candidate_whole=None, fresh_net=None, damage_exposure=None,
                decision='ORDINARY_ROUTE_FEASIBLE_DIGITAL_ONLY', next_dependency='Common timing/expiration law and paid assistance withdrawal')


if __name__ == '__main__':
    print(json.dumps(audit(json.load(open(sys.argv[1], encoding='utf-8'))),sort_keys=True))
