"""Unqualified precharged pipe capture; no launch or automatic operations."""
import hashlib,json,os,stat
from pathlib import Path
MIB=1024**2
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(b):return hashlib.sha256(b).hexdigest()
def plain(path,directory=False):
    i=path.lstat();assert not stat.S_ISLNK(i.st_mode) and not getattr(i,'st_file_attributes',0)&0x400
    assert stat.S_ISDIR(i.st_mode) if directory else stat.S_ISREG(i.st_mode) and i.st_nlink==1
    return i
def ident(i):return i.st_dev,i.st_ino

class Capture:
    VERSION="PILOT74-NATIVE-CAPTURE-GRANT-v2"
    OVERFLOW=24*MIB
    def __init__(self,grant,seal,source,config,role,command):
        self.opened={};self.used={'raw':0,'overflow':0};self.hashes={k:hashlib.sha256() for k in self.used}
        self.grant=grant;self.seal=seal;self.eof=False;self.errors=[];self.received=0
        try:
            assert type(grant) is dict and set(grant)=={'version','root','source_sha256','configuration_sha256','role','command_sha256','operator_lock','raw','overflow'}
            assert grant['version']==self.VERSION and sha(enc(grant))==seal
            assert (grant['source_sha256'],grant['configuration_sha256'],grant['role'])==(source,config,role) and grant['command_sha256']==sha(enc(list(command)))
            for value in (source,config):assert type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value)
            assert type(role) is str and role.isascii() and all(p not in ('','.','..') for p in role.split('/')) and '\\' not in role and ':' not in role
            root=Path(grant['root']);assert root.is_absolute() and root.resolve().is_relative_to(Path('D:/OraLab/runs').resolve())
            assert Path(grant['raw']['path'])==root/'raw'/'stdout'/(role+'.bin')
            assert Path(grant['overflow']['path'])==root/'failure'/'native-first-output.bin'
            self.owner()
            seen=[]
            for key,limit in (('raw',MIB),('overflow',self.OVERFLOW)):
                spec=grant[key];assert type(spec) is dict and set(spec)=={'path','limit','device','inode'}
                assert type(spec['limit']) is int and spec['limit']==limit and type(spec['device']) is int and type(spec['inode']) is int
                path=Path(spec['path']);chain=[(p,ident(plain(p,True))) for p in path.parents]
                before=plain(path);assert before.st_size==0 and ident(before)==(spec['device'],spec['inode'])
                fd=os.open(path,os.O_RDWR|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
                self.opened[key]=(fd,path,chain)
                now=os.fstat(fd);assert stat.S_ISREG(now.st_mode) and now.st_nlink==1 and now.st_size==0 and ident(now)==ident(before)
                seen.append(ident(now))
            assert len(set(seen))==2
        except BaseException as first:
            try:self.close()
            except BaseException as later:first.add_note("Capture close failure: "+repr(later))
            raise

    def owner(self):
        spec=self.grant['operator_lock'];assert type(spec) is dict and set(spec)=={'path','extent','sha256','device','inode'}
        p=Path(spec['path']);assert p==Path('D:/OraLab/state/operator.lock') and type(spec['extent']) is int and 0<spec['extent']<=16384
        for parent in p.parents:plain(parent,True)
        old=plain(p);assert old.st_size==spec['extent'] and ident(old)==(spec['device'],spec['inode'])
        fd=os.open(p,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
        try:
            now=os.fstat(fd);assert stat.S_ISREG(now.st_mode) and now.st_nlink==1 and ident(now)==ident(old) and now.st_size==old.st_size
            raw=os.read(fd,spec['extent']+1);assert len(raw)==spec['extent'] and sha(raw)==spec['sha256']
            assert ident(plain(p))==ident(old) and plain(p).st_size==old.st_size
        finally:os.close(fd)

    def check(self,key):
        fd,path,chain=self.opened[key];spec=self.grant[key]
        actual=os.fstat(fd);latest=plain(path)
        assert stat.S_ISREG(actual.st_mode) and actual.st_nlink==1 and ident(actual)==ident(latest)==(spec['device'],spec['inode']) and actual.st_size==latest.st_size==self.used[key]
        for parent,identity in chain:assert ident(plain(parent,True))==identity

    def append(self,block):
        assert type(block) is bytes and 0<len(block)<=65536
        self.received+=len(block);remaining=block
        for key in ('raw','overflow'):
            if not remaining:break
            available=self.grant[key]['limit']-self.used[key];piece=remaining[:available]
            if not piece:continue
            self.owner();self.check(key);fd=self.opened[key][0]
            n=os.write(fd,piece)
            self.used[key]+=n;self.hashes[key].update(piece[:n])
            if n!=len(piece):raise OSError('Short capture write; partial retained without retry')
            self.check(key);remaining=remaining[len(piece):]
        if remaining:raise OSError('Capture hard ceiling reached; retained prefix is INCOMPLETE')

    def finish(self):
        files={}
        for key,(fd,path,chain) in self.opened.items():
            os.fsync(fd);self.check(key)
            files[key]=dict(path=str(path),extent=self.used[key],sha256=self.hashes[key].hexdigest())
        assert len(files)==2
        retained=sum(self.used.values());complete=self.eof and not self.errors and retained==self.received
        return dict(schema='PILOT74-NATIVE-CAPTURE-v2',grant_sha256=self.seal,raw=files['raw'],overflow=files['overflow'],received_bytes=self.received,retained_bytes=retained,eof=self.eof,capture_complete=complete,stdout_limit_exceeded=self.received>MIB,errors=list(self.errors))

    def close(self):
        errors=[]
        for key,(fd,path,chain) in list(self.opened.items()):
            try:os.fsync(fd)
            except BaseException as error:errors.append(repr(error))
            try:os.close(fd)
            except BaseException as error:errors.append(repr(error))
            del self.opened[key]
        if errors:raise OSError('Capture close failures: '+repr(errors))


class ParentCapture(Capture):
    """Separate control8MiB sink; child capture remains unchanged."""
    VERSION="PILOT74-PARENT-CAPTURE-GRANT-v2"
    OVERFLOW=2*MIB
    def __init__(self,grant,seal,source,config,role,command):
        assert role=="parent"
        super().__init__(grant,seal,source,config,role,command)
