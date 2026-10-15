"""Trusted remaining precharge/cache custody. No VM or label imports."""
import hashlib
import json
import zipfile
from pathlib import Path

from experiments import digital_inheritance83_custody as old
from experiments import digital_inheritance83_remaining as remaining

HASHES = ('34ee68c18a4b44374275337d74fc23ed30873578ac4ec3f12c7c2a0faab46158',
          'b6c3243baf947a29e13076f7354d7adef813fdc9f8cf3d040fae001fe435fae9',
          'f228fc923dfbd4c789a95e902c92b85b832df4c2f7af011be8b3bafab7d778b0')
RAW_BOUND = 10753624707


def precharge(budget, pins):
    from experiments.evidence_write_grant68 import seal
    source, config = old.digest(pins), old.digest(old.CONFIG)
    slots = {}; cached = {}
    for role in remaining.plan():
        stem = role.replace(':', '-')
        limit = (64 if role.endswith(':generate') else 8)*old.M
        grant, signature = seal(budget, 'raw', 'data/'+stem+'.json', limit, source, config, role)
        slots[role] = (grant, signature, stem)
        for directory, maximum in (('native', old.M), ('request', 65536)):
            with budget.create('raw', directory+'/'+stem+'.json', reserve=maximum): pass
    for seed in remaining.CACHED:
        cached[seed] = seal(budget, 'raw', f'cached-metrics/{seed}.json', 8*old.M,
                            source, config, f'cached:{seed}:metrics')
    for bad in ('role','configuration','source','seal'):
        for directory, maximum in (('native', old.M), ('request', 65536)):
            with budget.create('raw', directory+'/bad-'+bad+'.json', reserve=maximum): pass
    assert all(budget.files['raw/'+n] == v for n, v in remaining.allocations().items())
    assert budget.used['raw'] < RAW_BOUND
    return slots, cached


def archive_members(archive_spec, root, paths):
    """Exact original paths and source bytes must belong to the closed archive."""
    assert remaining.spec(archive_spec['path']) == archive_spec
    root = Path(root)
    seen = {}
    with zipfile.ZipFile(archive_spec['path']) as archive:
        for path in sorted(set(map(Path, paths)), key=str):
            actual = remaining.spec(path)
            h = hashlib.sha256()
            with archive.open(path.relative_to(root).as_posix()) as stream:
                for block in iter(lambda: stream.read(old.M), b''): h.update(block)
            assert h.hexdigest() == actual['sha256'], 'archive membership'
            seen[str(path)] = actual
    return seen


def chain_paths(chain):
    request = remaining.pinned_read(chain['request'], 65536)
    g = request['grant']; root = Path(g['root'])
    result = [Path(chain[k]['path']) for k in ('request','native')]
    result += [root/g['phase']/g['name']]
    result += [root/'raw'/request['role'].split(':')[0]/name for name in request['source_files']]
    return result


def authenticate(bundle):
    """Read-only complete mixed-source chain binding before any new producer."""
    from experiments.digital_inheritance83_remaining_child import SCOPE
    from experiments import evidence_write_grant68 as transport
    from experiments import digital_cognitive76_child as boundary
    assert set(bundle) == {'manifest','interface_report','interface_archive','interface_chains'}
    manifest = bundle['manifest']
    assert old.digest(manifest) == SCOPE['cache_manifest_sha256']
    assert bundle['interface_archive']['sha256'] == SCOPE['cache_archive_sha256']
    expected_batches = remaining.cached_batches(manifest, SCOPE['cache_manifest_sha256'])
    report = remaining.pinned_read(bundle['interface_report'], 8*old.M, canonical=False)
    assert report['verified'] and report['interface_qualified'] and report['archive_exact']
    assert report['new_worlds'] == report['target_queries'] == 0 and report['native_calls'] == 2
    assert report['remaining_execution_admitted'] is False
    assert report['archive_sha256'] == SCOPE['cache_archive_sha256']
    all_paths = []; original_paths = []; qualified_paths = []; interface_paths = []
    for cell in manifest['cells']:
        for key in ('original_generate','restored_generate','original_audit'):
            original_paths += chain_paths(cell[key])
    for export in ('original','restored'):
        chain = manifest['qualified'][export]
        qualified_paths += chain_paths(chain)
        req = remaining.pinned_read(chain['request'],65536)
        for item in req['inputs']:
            for row in item['rows']:
                qualified_paths += [Path(row[k]['path']) for k in ('record','proof')]
            if item['old_metric']:
                qualified_paths.append(Path(item['old_metric']['path']))
        qualified_paths.append(Path(req['old_child']['path']))
    outputs = []
    assert set(bundle['interface_chains']) == {'original','restored'}
    for export in ('original','restored'):
        chain = bundle['interface_chains'][export]
        req, native, body = remaining.native_binding(chain['request'], chain['native'])
        assert req['role'] == export+':remaining-interface'
        assert req['manifest'] == manifest
        assert req['configuration']['manifest_sha256'] == SCOPE['cache_manifest_sha256']
        value = remaining.pinned_read(body, 8*old.M)
        assert value == report['summaries'][0 if export == 'original' else 1]
        assert value['verified'] and value['remaining_execution_admitted'] is False
        assert value['new_worlds'] == value['target_queries'] == 0
        assert [b['seed'] for b in value['materialized']] == list(remaining.CACHED)
        assert [b['seed'] for b in req['batch_grants']] == list(remaining.CACHED)
        paths = chain_paths(chain); result = {}
        for index, (materialized, slot, batch) in enumerate(zip(value['materialized'], req['batch_grants'], expected_batches, strict=True)):
            seed = remaining.CACHED[index]; g = slot['grant']; receipt = materialized['receipt']
            assert materialized['seed'] == slot['seed'] == batch['seed'] == seed
            assert slot['role'] == req['role']+':cached:'+str(seed)
            assert slot['seal'] == transport.digest(g) == receipt['grant_sha256']
            for key, expected in (('role',slot['role']),('source_sha',req['source_sha']),('config_sha',req['config_sha'])):
                assert receipt[key] == g[key] == expected
            assert g['limit'] == 8*old.M
            path = Path(g['root'])/g['phase']/g['name']; info = transport.plain(path)
            assert (info.st_dev,info.st_ino) == (g['device'],g['inode'])
            actual = remaining.spec(path)
            assert actual == materialized['spec'] and actual['sha256'] == receipt['sha256'] == HASHES[index]
            assert actual['extent'] == receipt['extent']
            assert boundary.read_spec(actual,8*old.M) == batch
            result[seed] = actual; paths.append(path)
        outputs.append(result); interface_paths += paths
    assert all((outputs[0][s]['extent'],outputs[0][s]['sha256']) == (outputs[1][s]['extent'],outputs[1][s]['sha256']) for s in remaining.CACHED)
    old_req = remaining.pinned_read(manifest['cells'][0]['original_generate']['request'],65536)
    qual_req = remaining.pinned_read(manifest['qualified']['original']['request'],65536)
    interface_req = remaining.pinned_read(bundle['interface_chains']['original']['request'],65536)
    membership = {}
    for archive_spec, root, paths in ((manifest['old_archive'],old_req['grant']['root'],original_paths),
                                      (manifest['qualified_archive'],qual_req['grant']['root'],qualified_paths),
                                      (bundle['interface_archive'],interface_req['grant']['root'],interface_paths)):
        membership.update(archive_members(archive_spec,root,paths)); all_paths += paths
    all_paths += [Path(manifest[k]['path']) for k in ('old_report','qualified_report')]
    all_paths += [Path(bundle['interface_report']['path'])]
    # The exact archive anchors remain immutable external evidence. All consumed
    # records/requests/native/source files are copied into the new archive.
    return dict(cached=outputs[0], membership=membership,
                files={str(p):remaining.spec(p) for p in sorted(set(all_paths),key=str)},
                source_scope=SCOPE, new_worlds=0,target_queries=0,execution_admission=False)


def relocate(cached, grants, pins):
    """Lossless parent materialization, not another metric or organism run."""
    from experiments import digital_cognitive76_child as boundary
    from experiments import evidence_write_grant68 as transport
    assert set(cached) == set(grants) == set(remaining.CACHED)
    result = {}; provenance = []
    for index, seed in enumerate(remaining.CACHED):
        original = cached[seed]; assert original['sha256'] == HASHES[index]
        value = boundary.read_spec(original,8*old.M)
        grant, signature = grants[seed]
        role = f'cached:{seed}:metrics'
        receipt = transport.record(grant,signature,old.digest(pins),old.digest(old.CONFIG),role,value)
        body = remaining.spec(Path(grant['root'])/grant['phase']/grant['name'])
        assert (body['extent'],body['sha256']) == (original['extent'],original['sha256'])
        provenance.append(dict(seed=seed,original=original,materialized=body,grant=grant,seal=signature,receipt=receipt))
        result[seed] = body
    return result, provenance
