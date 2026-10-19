"""Unqualified physical source export/ZIP restore, no native/World entrypoint."""
import hashlib,os,struct,zipfile
from pathlib import Path
from experiments import digital_pilot74_parent_ledger_v2 as ledger
from experiments import digital_pilot74_publication_reader_v2 as physical
from experiments import digital_pilot74_available_archive_v2 as custody
from experiments.digital_pilot74_guardian_v1 import artifact_name
MIB=1024**2

def rows(root,pins):
    root=Path(root);assert root.is_absolute() and type(pins) is dict and pins
    result=[]
    for name,digest in sorted(pins.items()):
        assert type(name) is str and name.isascii() and artifact_name(name) and '..' not in name and '\\' not in name and ':' not in name
        physical.checksum(digest);item=custody.scan(root/name,MIB)
        assert item['extent']>0 and item['sha256']==digest
        result.append(dict(name=name,extent=item['extent'],sha256=digest))
    assert len(result)<=256 and sum(x['extent'] for x in result)+65536<=1536*1024
    return result

def export(root,slots,pins,source_rows,revision,config_sha):
    """Original physical bytes, stored ZIP, restored physical bytes; no import."""
    assert source_rows==rows(root,pins);physical.checksum(config_sha)
    assert type(revision) is str and len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
    source_sha=ledger.digest(ledger.encode(pins));manifest=dict(schema='PILOT74-PHYSICAL-SOURCE-EXPORT-v2',revision=revision,source_sha256=source_sha,configuration_sha256=config_sha,files=source_rows)
    manifest_raw=ledger.encode(manifest);assert len(manifest_raw)<=65536
    roots={k:Path(slots['raw/metadata/source/'+k+'.json']['path']).parent/k for k in ('original','restored')}
    original={}
    for row in source_rows:
        raw=physical.external(dict(path=str(Path(root)/row['name']),extent=row['extent'],sha256=row['sha256']),MIB)
        spec=ledger.write_empty(slots['raw/metadata/source/original/'+row['name']],raw)
        original[row['name']]=custody.scan(spec['path'],row['extent'])
    output=custody.Forward(slots['raw/metadata/source/source.zip']);central=[]
    with output:
        for row in source_rows:
            name=row['name'];meta=original[name];raw=physical.external(dict(path=meta['path'],extent=row['extent'],sha256=row['sha256']),MIB)
            label=name.encode('ascii');offset=output.offset;size=len(raw);crc=meta['crc32']
            output.write(struct.pack('<IHHHHHIIIHH',0x04034b50,20,0,0,0,33,crc,size,size,len(label),0)+label);output.write(raw)
            central.append(struct.pack('<IHHHHHHIIIHHHHHII',0x02014b50,20,20,0,0,0,33,crc,size,size,len(label),0,0,0,0,0,offset)+label)
        start=output.offset
        for header in central:output.write(header)
        output.write(struct.pack('<IHHHHIIH',0x06054b50,0,0,len(source_rows),len(source_rows),output.offset-start,start,0))
    archive=custody.scan(slots['raw/metadata/source/source.zip']['path'],1536*1024)
    archive_path=Path(archive['path']);chain=[(a,physical.identity_tuple(physical.plain(a,True))[:2]) for a in archive_path.parents];before=physical.plain(archive_path)
    with Path(archive['path']).open('rb') as stream:
        assert physical.identity_tuple(os.fstat(stream.fileno()))==physical.identity_tuple(before)
        with zipfile.ZipFile(stream,'r',allowZip64=False) as bundle:
            expected={x['name']:x for x in source_rows};infos=bundle.infolist()
            assert bundle.comment==b'' and len(infos)==len(expected) and {x.filename for x in infos}==set(expected)
            for info in infos:
                row=expected[info.filename];assert info.compress_type==zipfile.ZIP_STORED and info.flag_bits==0 and info.extra==info.comment==b'' and info.file_size==info.compress_size==row['extent']
                raw=bundle.read(info);assert len(raw)==row['extent'] and hashlib.sha256(raw).hexdigest()==row['sha256']
                ledger.write_empty(slots['raw/metadata/source/restored/'+row['name']],raw)
        assert physical.identity_tuple(os.fstat(stream.fileno()))==physical.identity_tuple(physical.plain(Path(archive['path'])))==physical.identity_tuple(before)
    for a,identity in chain:assert physical.identity_tuple(physical.plain(a,True))[:2]==identity
    receipts={}
    for name,export_root in roots.items():
        assert rows(export_root,pins)==source_rows
        receipts[name]=ledger.write_empty(slots['raw/metadata/source/'+name+'.json'],manifest_raw)
    return dict(roots={k:str(v) for k,v in roots.items()},manifests=receipts,archive=archive,source_sha256=source_sha,source_rows=source_rows,execution_admitted=False)
