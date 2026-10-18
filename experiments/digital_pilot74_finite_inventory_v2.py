"""Concrete source-only leaf inventory; no role execution or admission entrypoint.

Extends the closed v1 inventory by replacing its metadata placeholder. All old
data/publication/request/native reservations and the 26-role graph are retained.
Actual source files and ZIP headers still must pass these caps before endpoints.
"""
from experiments import digital_pilot74_inventory as retained
MIB=1024**2
KIB=1024

def metadata():
    rows=[]
    def slot(name,limit):rows.append(dict(name='metadata/'+name,limit=limit))
    for export in ('original','restored'):slot('source/'+export+'.json',1536*KIB)
    slot('source/source.zip',1536*KIB)
    slot('source/owners.json',512*KIB)
    for export in ('original','restored'):
        for name in ('prepared','generate','audit8192','resume8192','audit9216','resume9216','audit10240','resume10240'):
            slot('grants/'+export+'/'+name+'.json',16*KIB)
    for fault in ('partial','orphan','committed','normal'):
        for kind in ('crash','recover'):
            slot('grants/'+kind+'/'+fault+'.json',16*KIB)
            slot('initial-commit/'+kind+'/'+fault+'.json',16*KIB)
    for name in ('normal-sequence','closed-projection-publication-audit'):
        slot('grants/'+name+'.json',16*KIB)
    slot('initial-commit/normal-sequence.json',16*KIB)
    for seq in (1,2,3):
        slot(f'publication/registration-{seq}.json',32*KIB)
        slot(f'publication/grant-{seq}.json',32*KIB)
        slot(f'publication/receipt-{seq}.json',64*KIB)
    for name,cap in [('registration.json',64),('configuration.json',16),('source-pins.json',128),
                     ('budget-before.json',128),('budget-after.json',128),('summary.json',128),
                     ('qualification-receipts.json',256),('ancestry.json',128),('compatibility.json',32)]:
        slot(name,cap*KIB)
    assert len({r['name'] for r in rows})==len(rows)
    assert sum(r['limit'] for r in rows)<=8*MIB
    return rows

def plan():
    value=retained.plan()
    assert value['files'][-1]==dict(name='metadata-reserve',limit=8*MIB)
    value=dict(version='PILOT74-FINITE-LEAF-INVENTORY-v2',roles=value['roles'],files=value['files'][:-1]+metadata())
    value['files'] += [dict(name='stdout/'+r['name']+'.bin',limit=MIB) for r in value['roles']]
    limits={r['name']:r['limit'] for r in value['files']}
    assert len(limits)==len(value['files']) and sum(limits.values())<=retained.RAW_CAP
    # First failure's already-written data/partial files stay in raw slots. Do
    # not duplicate capsule bodies into this separately precharged phase.
    failure=[dict(name='native-first-failure.json',limit=8*MIB),
             dict(name='native-first-output.bin',limit=24*MIB),
             dict(name='first-exception.json',limit=64*KIB),
             dict(name='partial-inventory.json',limit=512*KIB)]
    # A fixed ZIP_STORED archive avoids compression-expansion assumptions. The
    # parent must bound each actual ASCII path to240 bytes and disallow comments,
    # extras, ZIP64 and directories; every leaf gets local+central headers.
    count=len(limits)+len(failure);assert count<=1024
    zip_headers=count*(30+46+2*240)+22
    bound=sum(limits.values())+sum(r['limit'] for r in failure)+zip_headers
    assert sum(r['limit'] for r in failure)<=128*MIB
    assert bound<=1280*MIB
    return dict(schema=value['version'],roles=value['roles'],raw=value['files'],failure=failure,
                archive_format='ZIP_STORED/no-extra/no-comment/no-ZIP64/ASCII-path<=240',
                archive_and_restore_bound=bound,zip_header_bound=zip_headers,
                source_fit_verified=False,resource_fit_verified=False,execution_admitted=False)

def source_fit(rows):
    """Inspect externally supplied exact inventory, never import source modules."""
    assert type(rows) is list and rows
    names=[];size=0
    for row in rows:
        assert type(row) is dict and set(row)=={'name','extent','sha256'}
        name=row['name'];assert type(name) is str and name.isascii() and len(name)<=240
        assert name.startswith('experiments/') and name.endswith('.py') and '..' not in name and '\\' not in name
        assert type(row['extent']) is int and 0<row['extent']<=MIB
        digest=row['sha256'];assert type(digest) is str and len(digest)==64 and all(c in '0123456789abcdef' for c in digest)
        names.append(name);size+=row['extent']
    assert len(set(names))==len(names)
    # Hex-free JSON source exports must independently check actual encoded size;
    # this bound covers only the stored source ZIP, not their expansion.
    bound=size+len(rows)*(30+46+2*240)+22
    assert bound<=1536*KIB
    return dict(source_zip_stored_bound=bound,actual_json_exports_still_required=True,
                execution_admitted=False)
