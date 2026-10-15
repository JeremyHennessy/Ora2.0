"""Read-only exact prior qualification bindings; no experiment imports."""
import hashlib,json
from pathlib import Path
LAB=Path('D:/OraLab')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify():
    from credited_fallback87v2_paid_provenance_v1 import verify as old_source
    old_source()
    namespace=json.loads((LAB/'reports/credited-fallback87v2-origin-namespace-prepared-v1.json').read_bytes())
    assert namespace['passed'] is True and namespace['evidence_archive_exact_readback'] is True
    for path,value in namespace['pins'].items():assert sha(path)==value,('namespace/current source',path)
    root=LAB/'runs/credited-fallback87v2-origin-namespace-prepared-v1-20261015'
    assert sha(root/'archive/evidence.zip')==namespace['evidence_archive_sha256']
    metric=json.loads((LAB/'reports/credited-fallback87v2-origin-prepared-v2.json').read_bytes())
    assert metric['passed'] is True and metric['qualified_closed_originals']==51 and metric['old_native_bindings']==18
    assert sha(LAB/'runs/credited-fallback87v2-origin-prepared-v2-20261015/archive/evidence.zip')==metric['evidence_archive_sha256']
    # The namespace qualification explicitly binds the OLD metric/test source
    # archive to the current metadata-only AST delta. Do not compare those old
    # mutable checkout paths blindly or waive their old immutable proof.
    assert json.loads((LAB/'reports/credited-fallback87v2-origin-publication-v1.json').read_bytes())['publication_verified'] is True
    return dict(verified=True,old51_derivations_reused=True,current_namespace_source_exact=True,
                source_normalization=False,new_worlds=0,new_targets=0)
