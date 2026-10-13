"""UNQUALIFIED candidate host recorder. No World or scientific execution.

Parent precharges a complete fresh file in its authoritative Budget before
launching one child. The child gets one source/config/role/file grant; no VM
operation can invoke this recorder. This is not adversarial OS confinement.
"""
import hashlib,json,os,stat
from pathlib import Path

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)

def digest(value):return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()

def plain(path,directory=False):
    info=path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
        raise ValueError('Link or reparse grant refused')
    if directory:
        if not stat.S_ISDIR(info.st_mode):raise ValueError('Plain directory required')
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:
        raise ValueError('Unshared regular grant file required')
    return info

def seal(budget,phase,name,limit,source_sha,config_sha,role):
    """Parent only. Authoritative Budget must retain reservation on failure."""
    if type(limit) is not int or not 0<limit<=64*1024**2:
        raise ValueError('Finite registered grant extent required')
    for identity in (source_sha,config_sha):
        if type(identity) is not str or len(identity)!=64 or any(c not in '0123456789abcdef' for c in identity):
            raise ValueError('Pinned SHA256 identity required')
    if type(role) is not str or not role or not role.isascii():raise ValueError('Explicit role required')
    with budget.create(phase,name,reserve=limit) as stream:path=stream.path
    info=plain(path)
    if info.st_size!=0:raise ValueError('Empty parent-precharged grant required')
    grant=dict(version='sharedlineage68-file-grant-candidate-v1',root=str(budget.root),
               phase=phase,name=name,limit=limit,source_sha=source_sha,config_sha=config_sha,
               role=role,device=info.st_dev,inode=info.st_ino)
    return grant,digest(grant)

def record(grant,expected_seal,source_sha,config_sha,role,value):
    """Child only; forward writes into exactly one already charged empty file."""
    fields={'version','root','phase','name','limit','source_sha','config_sha','role','device','inode'}
    if type(grant) is not dict or set(grant)!=fields or digest(grant)!=expected_seal:
        raise ValueError('Exact sealed grant required')
    if grant['version']!='sharedlineage68-file-grant-candidate-v1':raise ValueError('Grant version')
    if (grant['source_sha'],grant['config_sha'],grant['role'])!=(source_sha,config_sha,role):
        raise ValueError('Source/configuration/role mismatch')
    limit=grant['limit']
    if type(limit) is not int or not 0<limit<=64*1024**2:raise ValueError('Finite extent')
    phase,name=grant['phase'],grant['name']
    if type(phase) is not str or not phase or not phase.isascii() or not phase.replace('-','').isalnum():
        raise ValueError('Plain phase')
    if type(name) is not str or not name or '\\' in name or ':' in name:
        raise ValueError('Relative path')
    parts=name.split('/')
    if any(p in ('','.','..') for p in parts):raise ValueError('Path escape')
    root=Path(grant['root'])
    if not root.is_absolute():raise ValueError('Absolute precharged root')
    path=root/phase/name
    for parent in path.parents:plain(parent,True)
    before=plain(path)
    if before.st_size or (before.st_dev,before.st_ino)!=(grant['device'],grant['inode']):
        raise ValueError('Fresh identical empty file required')
    flags=os.O_RDWR|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)
    fd=os.open(path,flags);extent=0;sha=hashlib.sha256();pending=bytearray()
    def flush():
        nonlocal extent
        if not pending:return
        if extent+len(pending)>limit:raise ValueError('Prewrite extent')
        if os.write(fd,pending)!=len(pending):raise OSError('Partial write retained; no retry')
        sha.update(pending);extent+=len(pending);pending.clear()
    try:
        opened=os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink!=1 or opened.st_size or (opened.st_dev,opened.st_ino)!=(before.st_dev,before.st_ino):
            raise ValueError('Opened file identity mismatch')
        encoder=json.JSONEncoder(sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
        for chunk in encoder.iterencode(value):
            data=chunk.encode('ascii')
            if extent+len(pending)+len(data)>limit:raise ValueError('Extent refused before write; partial evidence retained')
            start=0
            while start<len(data):
                take=min(65536-len(pending),len(data)-start)
                pending.extend(data[start:start+take]);start+=take
                if len(pending)==65536:flush()
        flush()
        os.fsync(fd)
        after=plain(path)
        if after.st_size!=extent or (after.st_dev,after.st_ino)!=(before.st_dev,before.st_ino):
            raise ValueError('Final physical grant identity or extent mismatch')
    finally:os.close(fd)
    return dict(grant_sha256=expected_seal,source_sha=source_sha,config_sha=config_sha,
                role=role,extent=extent,sha256=sha.hexdigest())
