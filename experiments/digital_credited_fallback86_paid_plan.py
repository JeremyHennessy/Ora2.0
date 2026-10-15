"""Pure finite custody layout. No producer, referee or environmental inputs."""
M = 1024**2
ROLES = tuple(role for seed in (2100080,2100081,2100082,2100083) for role in
              (f'original:{seed}:generate',f'original:{seed}:audit',f'restored:{seed}:generate'))


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
    failure = {'outcome.json': 8*M, 'budget.json': 8*M}
    limits = dict(raw=sum(raw.values()), failure=sum(failure.values()),
                  restore=sum(raw.values())+sum(failure.values()),
                  archive=sum(raw.values())+sum(failure.values())+4*M)
    assert all(limits[k] <= v*M for k, v in dict(raw=112, archive=144, restore=144, failure=16).items())
    assert sum(limits.values()) <= 416*M
    return raw, failure, limits


def recording_bound():
    # Nine histories, each with up to four sixteen-offer input events.
    return 9*256*3072+9*8192+9*32768+65536


def admit_ci(receipt, source_head, worktree_status):
    assert type(receipt) is dict
    assert receipt.get('passed') is True and receipt.get('conclusion') == 'success'
    assert receipt.get('source_head') == source_head
    assert type(worktree_status) is str and worktree_status == ''
