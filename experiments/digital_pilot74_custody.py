"""Bounded physical reader only; no producer or validator imports."""
import hashlib,os,stat
from pathlib import Path

def read_recording(path, extent, expected_sha256):
    """Trusted bounded filesystem custody, not adversarial confinement."""
    if type(extent) is not int or not 0 < extent <= 40*1024**2:
        raise ValueError('recording extent')
    path=Path(path)
    if not path.is_absolute():
        raise ValueError('absolute recording')
    def plain(candidate,directory=False):
        info=candidate.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('link/reparse recording')
        if directory:
            if not stat.S_ISDIR(info.st_mode):raise ValueError('plain parent')
        elif not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:
            raise ValueError('unshared regular recording')
        return info
    for parent in path.parents:plain(parent,True)
    before=plain(path)
    if before.st_size!=extent:raise ValueError('physical recording extent')
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    try:
        opened=os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink!=1 or (opened.st_dev,opened.st_ino,opened.st_size)!=(before.st_dev,before.st_ino,extent):
            raise ValueError('opened recording identity')
        chunks=[];remaining=extent
        while remaining:
            block=os.read(fd,min(65536,remaining))
            if not block:raise ValueError('short recording')
            chunks.append(block);remaining-=len(block)
        if os.read(fd,1):raise ValueError('overlong recording')
        after=plain(path);closed=os.fstat(fd)
        if (after.st_dev,after.st_ino,after.st_size)!=(before.st_dev,before.st_ino,extent) or closed.st_nlink!=1 or closed.st_size!=extent:
            raise ValueError('changed recording identity')
        raw=b''.join(chunks)
        if hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('recording hash')
        return raw
    finally:os.close(fd)
