"""Read-only mixed old/current qualification binding; no experiment imports."""
import hashlib,json,zipfile
from pathlib import Path
LAB=Path('D:/OraLab');DEV=LAB/'src/Ora2.0-recording82'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify():
    portable=json.loads((LAB/'reports/credited-fallback87-ci-portability-v1.json').read_bytes())
    assert portable['passed'] is True and portable['evidence_exact_readback'] is True
    archive=LAB/'runs/credited-fallback87-ci-portability-v1-20261015/archive/evidence.zip'
    assert sha(archive)==portable['evidence_archive_sha256']
    replacements={
      DEV/'tests/test_digital_credited_fallback87_source.py':LAB/'runs/credited-fallback87-source-prepared-v1-20261015/raw/original/tests/test_digital_credited_fallback87_source.py',
      DEV/'tests/test_digital_credited_fallback87v2_binding.py':LAB/'runs/credited-fallback87-v2-binding-prepared-v2-20261015/raw/original/tests/test_digital_credited_fallback87v2_binding.py'}
    for path,digest in portable['pins'].items():assert sha(path)==digest,(path,'portable pin')
    for path in replacements:
        name=path.relative_to(DEV).as_posix()
        assert sha(path)==portable['sources']['original'][name]
    records=[]
    for name in ('credited-fallback87-source-prepared-v1','credited-fallback87-v2-binding-prepared-v2',
                 'credited-fallback86-active-software-v1'):
        report=json.loads((LAB/'reports'/(name+'.json')).read_bytes())
        assert report.get('passed',report.get('verified')) is True
        for path,digest in report['pins'].items():
            p=Path(path);actual=replacements.get(p,p)
            assert sha(actual)==digest,(path,'old qualification pin')
        if name.startswith('credited-fallback87'):
            archive=LAB/'runs'/(name+'-20261015')/'archive/evidence.zip'
            assert sha(archive)==report['evidence_archive_sha256']
            with zipfile.ZipFile(archive) as z:
                for current,snapshot in replacements.items():
                    if str(current) in report['pins']:
                        assert z.read('raw/original/'+current.relative_to(DEV).as_posix())==snapshot.read_bytes()
        records.append(dict(report=name,pins=len(report['pins'])))
    return dict(verified=True,old_qualifications=records,changed_test_guards=2,
                source_normalization=False,worlds=0,targets=0)

if __name__=='__main__':print(json.dumps(verify(),sort_keys=True))
