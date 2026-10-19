"""Unqualified source-bound parent worker; separate registration required."""
import hashlib,json,os,sys,traceback
from pathlib import Path

def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def digest(raw):return hashlib.sha256(raw).hexdigest()

def bind(root,pins):
    """Bind package, __main__ and every already loaded experiments module."""
    expected=root/'experiments/digital_pilot74_parent_worker_v2.py'
    assert Path(__file__).resolve()==expected and Path(sys.modules['__main__'].__file__).resolve()==expected
    for name,module in list(sys.modules.items()):
        if name=='__main__' or name=='experiments' or name.startswith('experiments.'):
            path=Path(module.__file__).resolve();relative=path.relative_to(root).as_posix()
            assert relative in pins and digest(path.read_bytes())==pins[relative]

def main():
    # First failure includes argument/admission failures before controller init.
    stage='arguments';owner=None
    try:
        assert len(sys.argv)==4 and not sys.flags.optimize
        from experiments import digital_pilot74_publication_reader_v2 as physical
        spec=dict(path=sys.argv[1],extent=int(sys.argv[2]),sha256=sys.argv[3])
        raw=physical.external(spec,65536);r=physical.parse(raw,65536)
        root=Path(r['source_root']);stage='source-binding'
        assert root.is_absolute() and r['source_sha256']==digest(encode(r['source_files']))
        for relative,pin in r['source_files'].items():
            assert type(relative) is str and (relative.startswith('experiments/') and relative.endswith('.py') or relative in {'experiments/native/pilot74_guardian_v1.c','experiments/native/pilot74_guardian_v1.exe'}) and '..' not in relative and '\\' not in relative and ':' not in relative
            assert physical.digest(physical.external(dict(path=str(root/relative),extent=physical.plain(root/relative).st_size,sha256=pin),1024**2))==pin
        bind(root,r['source_files'])
        from experiments import digital_pilot74_journal as journal
        creation=journal.birth(os.getpid());assert type(creation) is int and 0<creation<2**64
        owner=dict(pid=os.getpid(),creation_filetime_decimal=str(creation))
        from experiments import digital_pilot74_guardian_v1 as guardian
        session=guardian.connect(r)
        from experiments import digital_pilot74_finite_controller_v2 as controller
        bind(root,r['source_files']);stage='registered-controller'
        result=controller.execute_registered(spec,spec['sha256'])
        bind(root,r['source_files']);stage='closed-controller'
        assert result['available_files_exactly_restored'] is True and result['evidence_complete'] is True
        row=dict(schema='PILOT74-PARENT-WORKER-RESULT-v2',registration_sha256=spec['sha256'],source_sha256=r['source_sha256'],owner=owner,archive=result,publication_accepted=False,live_attachment=False)
        session.finish(result)
        output=encode(row);assert len(output)<=65536
        sys.stdout.buffer.write(output+b'\n');sys.stdout.buffer.flush()
    except BaseException as first:
        if 'session' in locals():
            try:session.finish()
            except BaseException as later:first.add_note('Guardian failure finish unavailable: '+repr(later))
        # No inference from the presence of partial archive/header files.
        row=dict(schema='PILOT74-PARENT-WORKER-FAILURE-v2',stage=stage,owner=owner,first_exception=repr(first),traceback=''.join(traceback.format_exception(first)),inner_complete_archive_claimed=False)
        raw=encode(row)
        if len(raw)>65536:
            # Explicit failure, never silently shorten an exception to pass.
            sys.stderr.write('PILOT74 failure diagnostic exceeds registered 64KiB; outer raw capture is incomplete authority\n')
            raise
        sys.stderr.buffer.write(raw+b'\n');sys.stderr.buffer.flush()
        raise

if __name__=='__main__':main()
