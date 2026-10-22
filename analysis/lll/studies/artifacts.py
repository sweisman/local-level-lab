# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lossless content-addressed ZIP packs; original evidence bytes never change."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import zipfile

VERSION='lll-evidence-packs-v1'
PACK_BYTES=64*1024*1024


def digest(data):return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def atomic(path,data,*,durable=True):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.pending')
    with temporary.open('xb') as stream:
        stream.write(data);stream.flush()
        if durable:os.fsync(stream.fileno())
    os.replace(temporary,path)
    if durable:
        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)


def safe_path(root,name):
    if not isinstance(name,str) or not name or '\\' in name:
        raise ValueError('nonempty POSIX relative path required')
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or str(p)!=name or name=='.':
        raise ValueError('unsafe relative path')
    root=Path(root).resolve();out=root/name
    if not out.resolve().is_relative_to(root):raise ValueError('path escapes declared root')
    current=root
    for part in p.parts:
        current=current/part
        if current.is_symlink():raise ValueError('symlink in evidence path')
    return out


class ArchiveStore:
    def __init__(self,root):
        self.root=Path(root).resolve();self.directory=self.root/'repro'
        self.catalog_path=self.directory/'catalog.json';self._opened={}

    def catalog(self):
        if not self.catalog_path.exists():
            if self.catalog_path.with_suffix('.sha256').exists() or (self.directory/'packs').exists():
                raise ValueError('missing archive catalog')
            return dict(version=VERSION,paths={},objects={},packs={})
        raw=self.catalog_path.read_bytes()
        try:expected=self.catalog_path.with_suffix('.sha256').read_text().strip()
        except OSError as error:raise ValueError('missing catalog checksum') from error
        if digest(raw)!=expected:raise ValueError('catalog checksum mismatch')
        result=json.loads(raw)
        if result.get('version')!=VERSION:raise ValueError('unsupported archive catalog')
        return result

    def _archive(self,name,catalog,*,fresh=False):
        path=safe_path(self.directory,name)
        if fresh or name not in self._opened:
            try:
                if digest(path.read_bytes())!=catalog['packs'][name]:raise ValueError('pack checksum mismatch')
                archive=zipfile.ZipFile(path)
                members=archive.namelist()
                if len(members)!=len(set(members)):raise ValueError('duplicate pack member')
            except (OSError,zipfile.BadZipFile,KeyError) as error:
                raise ValueError('missing or invalid evidence pack: '+name) from error
            if name in self._opened:self._opened[name].close()
            self._opened[name]=archive
        return self._opened[name]

    def _object(self,sha,catalog):
        try:data=self._archive(catalog['objects'][sha],catalog).read(sha)
        except (KeyError,OSError,zipfile.BadZipFile) as error:raise ValueError('missing or corrupt object') from error
        if digest(data)!=sha:raise ValueError('evidence object checksum mismatch')
        return data

    def read(self,name):
        return self._read(name,self.catalog())

    def _read(self,name,catalog):
        path=safe_path(self.root,name);record=catalog['paths'].get(name)
        if path.is_file():
            data=path.read_bytes()
            if record and (digest(data)!=record['sha256'] or len(data)!=record['size']):
                raise ValueError('expanded evidence changed: '+name)
            return data
        if record is None:raise FileNotFoundError(name)
        data=self._object(record['sha256'],catalog)
        if len(data)!=record['size']:raise ValueError('object size mismatch')
        return data

    def pack(self,names):
        names=sorted(set(names));catalog=self.catalog();new={};records={}
        for name in names:
            path=safe_path(self.root,name)
            if name.startswith('repro/'):raise ValueError('cannot archive the archive store')
            data=self._read(name,catalog);sha=digest(data)
            mode=stat.S_IMODE(path.stat().st_mode) if path.is_file() else catalog['paths'][name]['mode']
            records[name]=dict(sha256=sha,size=len(data),mode=mode)
            if sha not in catalog['objects']:new.setdefault(sha,(name,len(data)))
        batches=[];batch=[];size=0
        for sha,(name,length) in sorted(new.items()):
            if batch and size+length>PACK_BYTES:batches.append(batch);batch=[];size=0
            batch.append((sha,name));size+=length
        if batch:batches.append(batch)
        for batch in batches:
            import io
            buffer=io.BytesIO()
            with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
                for sha,source in batch:
                    data=self._read(source,catalog)
                    if digest(data)!=sha:raise ValueError('source changed during archival')
                    member=zipfile.ZipInfo(sha,date_time=(1980,1,1,0,0,0));member.compress_type=zipfile.ZIP_DEFLATED
                    member.external_attr=0o100444<<16;archive.writestr(member,data)
            raw=buffer.getvalue();pack_sha=digest(raw);name='packs/'+pack_sha+'.zip'
            target=safe_path(self.directory,name)
            if target.exists():
                if digest(target.read_bytes())!=pack_sha:raise ValueError('existing pack changed')
            else:atomic(target,raw)
            catalog['packs'][name]=pack_sha
            for sha,_ in batch:catalog['objects'][sha]=name
        catalog['paths'].update(records)
        raw=encoded(catalog);atomic(self.catalog_path,raw);atomic(self.catalog_path.with_suffix('.sha256'),(digest(raw)+'\n').encode())
        self.verify()
        return dict(paths=len(records),new_objects=len(new),packs=len(batches))

    def verify(self):
        catalog=self.catalog()
        for name in catalog['packs']:self._archive(name,catalog,fresh=True)
        sizes={}
        for sha in catalog['objects']:sizes[sha]=len(self._object(sha,catalog))
        for name,record in catalog['paths'].items():
            safe_path(self.root,name)
            if sizes.get(record['sha256'])!=record['size']:raise ValueError('indexed object size mismatch')
        return dict(paths=len(catalog['paths']),objects=len(sizes),packs=len(catalog['packs']))

    def restore(self,destination,*,names=None):
        catalog=self.catalog();names=sorted(catalog['paths'] if names is None else set(names));pending=[]
        for name in names:
            record=catalog['paths'][name];path=safe_path(destination,name)
            if path.exists():
                if not path.is_file() or digest(path.read_bytes())!=record['sha256']:
                    raise ValueError('restore would overwrite changed file: '+name)
            else:pending.append((name,path,record))
        for name,path,record in pending:
            data=self._object(record['sha256'],catalog)
            if len(data)!=record['size']:raise ValueError('restore size mismatch')
            atomic(path,data,durable=False);path.chmod(record['mode'])
        return len(pending)

    def compact(self,*,names=None):
        self.verify();catalog=self.catalog();names=sorted(catalog['paths'] if names is None else set(names));pending=[]
        # Verify every expanded byte before removing any file. Unlisted paths are invisible.
        for name in names:
            path=safe_path(self.root,name);record=catalog['paths'][name]
            if path.exists():
                if not path.is_file() or digest(path.read_bytes())!=record['sha256']:
                    raise ValueError('expanded evidence changed: '+name)
                pending.append(path)
        for path in pending:path.unlink()
        return len(pending)

    def close(self):
        for archive in self._opened.values():archive.close()
        self._opened.clear()
