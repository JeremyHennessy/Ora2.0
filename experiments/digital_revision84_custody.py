"""Trusted precharged archive/readback streams; no World or target imports."""
import os
from experiments.evidence_budget import GuardedStream,plain

def open_reserved(budget,phase,name):
    key=phase+'/'+name
    assert key in budget.files and budget.files[key]>0
    # All files in this phase were precharged, so any per-file growth would
    # exceed the phase ceiling and is refused by the existing GuardedStream.
    assert budget.used[phase]==budget.limits[phase]
    path=budget._path(phase,name);plain(path);before=path.lstat()
    assert before.st_size==0
    stream=path.open('r+b')
    try:
        opened=os.fstat(stream.fileno())
        assert (opened.st_dev,opened.st_ino,opened.st_size)==(before.st_dev,before.st_ino,0)
        return GuardedStream(budget,key,path,stream)
    except BaseException:
        stream.close();raise

def mirror_limits(raw,failure):
    assert type(raw) is dict and type(failure) is dict
    assert all(type(v) is int and v>0 for v in list(raw.values())+list(failure.values()))
    restore=sum(raw.values())+sum(failure.values())
    archive=restore+4*1024**2
    assert sum(raw.values())<=3584*1024**2 and archive<=4096*1024**2
    assert restore<=4096*1024**2 and sum(failure.values())<=256*1024**2
    return dict(raw=sum(raw.values()),failure=sum(failure.values()),archive=archive,restore=restore)
