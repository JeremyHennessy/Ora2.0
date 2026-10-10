"""Trusted single-writer prewrite storage accounting; not an OS disk quota."""
import io
import json
import os
from pathlib import Path
import stat


class QuotaError(ValueError):pass


def plain(path):
    info=path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
        raise QuotaError('Link/reparse point refused')
    if not stat.S_ISDIR(info.st_mode) and (not stat.S_ISREG(info.st_mode) or info.st_nlink!=1):
        raise QuotaError('Nonplain or multiply linked file refused')


class Budget:
    def __init__(self,root,limits,total):
        if not limits or any(type(v) is not int or v<=0 for v in limits.values()) or type(total) is not int or total<=0:
            raise QuotaError('Finite positive integer limits')
        if any(not k or not k.isascii() or not k.replace('-','').isalnum() for k in limits):raise QuotaError('Plain phase names')
        self.root=Path(root).absolute()
        for p in (self.root.parent,*self.root.parent.parents):plain(p)
        if self.root.exists():raise QuotaError('Fresh root required')
        self.root.mkdir();self.limits=dict(limits);self.total=total;self.used={k:0 for k in limits};self.files={}
        for phase in limits:(self.root/phase).mkdir()

    def _path(self,phase,name):
        if phase not in self.limits or not isinstance(name,str) or not name or '\\' in name or ':' in name:raise QuotaError('Registered relative path')
        parts=name.split('/')
        if any(p in ('','.','..') for p in parts) or name.startswith('/'):raise QuotaError('Path escape refused')
        path=self.root/phase/name
        for parent in (self.root,self.root/phase,*list(path.parents)[:len(parts)-1]):plain(parent)
        return path

    def _charge(self,key,extent):
        phase=key.split('/',1)[0];old=self.files.get(key,0);growth=max(0,extent-old)
        if self.used[phase]+growth>self.limits[phase] or sum(self.used.values())+growth>self.total:raise QuotaError('Phase or combined growth refused before write')
        self.used[phase]+=growth;self.files[key]=old+growth

    def create(self,phase,name,reserve=0):
        if type(reserve) is not int or reserve<0:raise QuotaError('Nonnegative reservation')
        parts=name.split('/') if isinstance(name,str) else []
        # Validate lexical form before making any directories.
        if phase not in self.limits or not parts or any(p in ('','.','..') for p in parts) or '\\' in name or ':' in name:raise QuotaError('Registered relative path')
        key=phase+'/'+name
        if key in self.files:raise QuotaError('No overwrite/reopen')
        # Refuse the entire reservation before filesystem mutation.
        if self.used[phase]+reserve>self.limits[phase] or sum(self.used.values())+reserve>self.total:raise QuotaError('Phase or combined reservation refused before create')
        parent=self.root/phase
        for item in parts[:-1]:
            plain(parent);parent=parent/item
            if not parent.exists():parent.mkdir()
            plain(parent)
        path=self._path(phase,name)
        if path.exists():raise QuotaError('No overwrite')
        self._charge(key,reserve)
        # Failed creation retains its charge; caller must preserve the failure.
        stream=path.open('xb')
        return GuardedStream(self,key,path,stream)

    def snapshot(self):return dict(schema='evidence-budget-v1',limits=self.limits,total_limit=self.total,reserved=self.used,total_reserved=sum(self.used.values()),files=self.files)

    def write_snapshot(self,phase,name='budget.json'):
        """Save the current ledger, including its own precharged final extent.

        Call after all other writes. Later writes require a new snapshot path.
        A capacity refusal retains the empty file and any successful charges;
        it never writes an undercharged or partially calculated JSON receipt.
        """
        with self.create(phase,name) as stream:
            while True:
                data=json.dumps(self.snapshot(),sort_keys=True,separators=(',',':')).encode('utf-8')
                if len(data)<=self.files[stream.key]:
                    stream.write(data)
                    return stream.path
                # Only nondecreasing integer digit widths change the next JSON.
                # Growth is finite: the registered phase/combined caps bound it.
                self._charge(stream.key,len(data))


class GuardedStream:
    def __init__(self,budget,key,path,stream):self.budget,self.key,self.path,self.stream=budget,key,path,stream
    def write(self,data):
        if not isinstance(data,(bytes,bytearray,memoryview)):raise TypeError('Binary evidence only')
        plain(self.path);self.budget._charge(self.key,self.stream.tell()+len(data))
        n=self.stream.write(data)
        if n!=len(data):raise OSError('Partial write retained with full reservation')
        return n
    def seek(self,offset,whence=io.SEEK_SET):return self.stream.seek(offset,whence)
    def tell(self):return self.stream.tell()
    def flush(self):return self.stream.flush()
    def close(self):return self.stream.close()
    def writable(self):return True
    def seekable(self):return True
    @property
    def closed(self):return self.stream.closed
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
