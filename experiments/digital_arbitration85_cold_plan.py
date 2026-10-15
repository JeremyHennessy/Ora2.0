"""Pure finite custody layout. No producer, referee or environmental inputs."""
M = 1024**2
ROLES = ('original:generate', 'original:audit', 'restored:generate')


def registration_capacity(compact_extent):
    # The on-disk registration is pretty JSON with Windows newlines, not the
    # compact request encoding. Reserve its declared transport ceiling.
    assert type(compact_extent) is int and 0 < compact_extent <= 32*1024
    return 64*1024


def capacity(role):
    assert role in ROLES
    return (8 if role.endswith('generate') else 1)*M


def layout(sources, owners, registration_size):
    assert sum(sources.values())*2 <= 2*M and sum(owners.values()) <= M
    assert type(registration_size) is int and 0 < registration_size <= 64*1024
    raw = {'registration.json': registration_size, 'source.zip': M}
    for name, size in sources.items():
        assert type(size) is int and 0 < size <= M
        for export in ('original', 'restored'):
            raw[export+'/'+name] = size
    for name, size in owners.items():
        assert type(size) is int and 0 < size <= M
        raw['owners/'+name] = size
    for role in ROLES:
        raw['data/'+role.replace(':', '-')+'.json'] = capacity(role)
    for stem in [r.replace(':', '-') for r in ROLES]+['refused'+str(i) for i in range(4)]:
        raw['native/'+stem+'.json'] = M
        raw['request/'+stem+'.json'] = 64*1024
    failure = {'outcome.json': 4*M, 'budget.json': 4*M}
    limits = dict(raw=sum(raw.values()), failure=sum(failure.values()),
                  restore=sum(raw.values())+sum(failure.values()),
                  archive=sum(raw.values())+sum(failure.values())+4*M)
    assert all(limits[k] <= v*M for k, v in dict(raw=32, archive=48, restore=48, failure=8).items())
    assert sum(limits.values()) <= 136*M
    return raw, failure, limits
