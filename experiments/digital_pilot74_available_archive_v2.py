"""Finite available-evidence ZIP_STORED/restore custody, unqualified source.

No native/World/loader/replay imports. Archiving available partials is distinct
from complete experiment evidence. No role execution or implicit acceptance.
"""
import os,stat,struct,hashlib,zlib,zipfile
from pathlib import Path
from experiments import digital_pilot74_publication_reader_v2 as physical
MIB=1024**2

def scan(path,cap):
    """Read one plain registered leaf with full physical identity and extent."""
    p=Path(path);assert p.is_absolute();chain=[(a,physical.identity_tuple(physical.plain(a,True))[:2]) for a in p.parents]
    before=physical.plain(p);assert type(cap) is int and 0<=before.st_size<=cap
    fd=os.open(p,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0));digest=hashlib.sha256();crc=0;count=0
    try:
        opened=os.fstat(fd);assert physical.identity_tuple(opened)==physical.identity_tuple(before) and stat.S_ISREG(opened.st_mode) and opened.st_nlink==1
        while True:
            block=os.read(fd,65536)
            if not block:break
            count+=len(block);assert count<=before.st_size;digest.update(block);crc=zlib.crc32(block,crc)
        after=physical.plain(p);last=os.fstat(fd)
        assert physical.identity_tuple(after)==physical.identity_tuple(last)==physical.identity_tuple(before) and count==before.st_size
        for a,identity in chain:assert physical.identity_tuple(physical.plain(a,True))[:2]==identity
    finally:os.close(fd)
    return dict(path=str(p),extent=count,sha256=digest.hexdigest(),crc32=crc,device=before.st_dev,inode=before.st_ino)

class Forward:
    def __init__(self,slot):
        self.slot=slot;self.offset=0;self.sha=hashlib.sha256();self.fd=None
        p=Path(slot['path']);self.path=p;self.parents=[(a,physical.identity_tuple(physical.plain(a,True))[:2]) for a in p.parents]
        info=physical.plain(p);assert info.st_size==0 and (info.st_dev,info.st_ino)==(slot['device'],slot['inode'])
        self.fd=os.open(p,os.O_RDWR|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
        try:self.check()
        except BaseException:
            os.close(self.fd);self.fd=None;raise
    def check(self):
        i=os.fstat(self.fd);p=physical.plain(self.path)
        assert stat.S_ISREG(i.st_mode) and i.st_nlink==1 and physical.identity_tuple(i)==physical.identity_tuple(p)==(self.slot['device'],self.slot['inode'],self.offset)
        for parent,identity in self.parents:assert physical.identity_tuple(physical.plain(parent,True))[:2]==identity
    def __enter__(self):return self
    def __exit__(self,kind,first,trace):
        try:self.close()
        except BaseException as later:
            if first is None:raise
            first.add_note("Archive/restore close failure: "+repr(later))
        return False
    def write(self,raw):
        assert type(raw) is bytes and self.offset+len(raw)<=self.slot['limit'];self.check()
        n=os.write(self.fd,raw);self.offset+=n;self.sha.update(raw[:n])
        if n!=len(raw):raise OSError('Short archive/restore write retained, no retry')
        self.check()
    def close(self):
        if self.fd is not None:
            try:os.fsync(self.fd);self.check()
            finally:os.close(self.fd);self.fd=None

def archive_and_restore(slots,plan,*,evidence_complete,allow_observed_identity_changes=False):
    """Last raw/failure operation; later source evidence mutation invalidates it.

    On failure preserve all available files at registered leaf paths. Identity
    changes can be disclosed for custody only, never accepted as valid execution.
    No complete archive claim if this function raises or a hard stop interrupts.
    """
    assert type(evidence_complete) is bool and type(allow_observed_identity_changes) is bool
    assert not (evidence_complete and allow_observed_identity_changes)
    rows={}
    for phase in ('raw','failure'):
        for row in plan[phase]:
            name=phase+'/'+row['name'];assert name.isascii() and len(name)<=240 and name not in rows
            slot=slots[name];assert slot['limit']==row['limit'];actual=scan(slot['path'],slot['limit'])
            changed=(actual['device'],actual['inode'])!=(slot['device'],slot['inode'])
            assert not changed or allow_observed_identity_changes
            rows[name]=dict(actual,limit=row['limit'],identity_changed=changed)
    assert 0<len(rows)<=1024
    source_bytes=sum(v['extent'] for v in rows.values());header_bound=len(rows)*556+22
    assert source_bytes+header_bound<=slots['archive/complete.zip']['limit']<=1280*MIB
    out=Forward(slots['archive/complete.zip']);central=[]
    with out:
        for name,row in sorted(rows.items()):
            label=name.encode('ascii');offset=out.offset;size=row['extent'];crc=row['crc32']
            assert size<2**32 and offset<2**32
            out.write(struct.pack('<IHHHHHIIIHH',0x04034b50,20,0,0,0,33,crc,size,size,len(label),0)+label)
            p=Path(row['path']);chain=[(a,physical.identity_tuple(physical.plain(a,True))[:2]) for a in p.parents]
            before=physical.plain(p);assert physical.identity_tuple(before)==(row['device'],row['inode'],size)
            fd=os.open(p,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0));sha=hashlib.sha256();check_crc=0;count=0
            try:
                opened=os.fstat(fd);assert physical.identity_tuple(opened)==physical.identity_tuple(before) and opened.st_nlink==1
                while True:
                    block=os.read(fd,65536)
                    if not block:break
                    count+=len(block);assert count<=size;sha.update(block);check_crc=zlib.crc32(block,check_crc);out.write(block)
                assert physical.identity_tuple(os.fstat(fd))==physical.identity_tuple(physical.plain(p))==physical.identity_tuple(before)
            finally:os.close(fd)
            for a,identity in chain:assert physical.identity_tuple(physical.plain(a,True))[:2]==identity
            assert count==size and sha.hexdigest()==row['sha256'] and check_crc==crc
            central.append(struct.pack('<IHHHHHHIIIHHHHHII',0x02014b50,20,20,0,0,0,33,crc,size,size,len(label),0,0,0,0,0,offset)+label)
        start=out.offset
        for header in central:out.write(header)
        length=out.offset-start
        out.write(struct.pack('<IHHHHIIH',0x06054b50,0,0,len(rows),len(rows),length,start,0))
        assert out.offset<=source_bytes+header_bound
    archive=scan(slots['archive/complete.zip']['path'],1280*MIB)
    archive_path=Path(archive['path']);chain=[(a,physical.identity_tuple(physical.plain(a,True))[:2]) for a in archive_path.parents];before=physical.plain(archive_path)
    with archive_path.open('rb') as stream:
        opened=os.fstat(stream.fileno());assert physical.identity_tuple(opened)==physical.identity_tuple(before) and opened.st_nlink==1
        with zipfile.ZipFile(stream,'r',allowZip64=False) as bundle:
            infos=bundle.infolist();assert bundle.comment==b'' and len(infos)==len(rows) and {i.filename for i in infos}==set(rows)
            for info in infos:
                row=rows[info.filename]
                assert not info.is_dir() and info.compress_type==zipfile.ZIP_STORED and info.flag_bits==0 and info.extra==b'' and info.comment==b''
                assert info.file_size==info.compress_size==row['extent'] and info.CRC==row['crc32']
                target=slots['restore/'+info.filename];assert target['limit']==row['limit'];writer=Forward(target)
                with writer:
                    with bundle.open(info,'r') as source:
                        while True:
                            block=source.read(65536)
                            if not block:break
                            writer.write(block)
                    assert writer.offset==row['extent'] and writer.sha.hexdigest()==row['sha256']
                restored=scan(target['path'],target['limit'])
                assert (restored['extent'],restored['sha256'])==(row['extent'],row['sha256'])
        assert physical.identity_tuple(os.fstat(stream.fileno()))==physical.identity_tuple(physical.plain(archive_path))==physical.identity_tuple(before)
    for a,identity in chain:assert physical.identity_tuple(physical.plain(a,True))[:2]==identity
    # Original raw leaves must still equal the exact restored archive, including
    # empty slots, failed partials and available native output. No post-archive edits.
    for name,row in rows.items():
        current=scan(row['path'],row['limit']);assert current=={k:row[k] for k in current}
    return dict(schema='PILOT74-AVAILABLE-EVIDENCE-RESTORE-v2',archive=archive,files=len(rows),available_files_exactly_restored=True,evidence_complete=evidence_complete,identity_changes=[n for n,v in rows.items() if v['identity_changed']],worlds=0,vm_steps=0,publication_accepted=False,live_attachment=False)
