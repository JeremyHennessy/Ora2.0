"""Separate filesystem/capacity interpreter; no writer module imported."""
import hashlib
from pathlib import Path
import stat


def audit(root,receipt,limits,total):
    root=Path(root);files=receipt['files'];used={p:0 for p in limits};seen={};actual=0
    if receipt['schema']!='evidence-budget-v1' or receipt['limits']!=limits or receipt['total_limit']!=total:raise ValueError('Registered capacities')
    for path in [root,*root.rglob('*')]:
        info=path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:raise ValueError('No link/reparse accounting')
        if stat.S_ISDIR(info.st_mode):continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise ValueError('Only unshared regular evidence')
        name=path.relative_to(root).as_posix();phase=name.split('/')[0]
        if phase not in limits or name not in files:raise ValueError('Complete filesystem denominator')
        cap=files[name]
        if type(cap) is not int or cap<info.st_size:raise ValueError('Physical bytes exceed precharged extent')
        used[phase]+=cap;actual+=info.st_size;seen[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    if set(seen)!=set(files) or used!=receipt['reserved'] or sum(used.values())!=receipt['total_reserved']:raise ValueError('Independent complete reservation totals')
    if any(used[p]>limits[p] for p in used) or sum(used.values())>total:raise ValueError('Registered phase/combined cap')
    return dict(files=len(seen),logical_bytes=actual,reserved_bytes=sum(used.values()),reserved_by_phase=used,sha256=seen,limits=limits,total_limit=total)
