# SPDX-License-Identifier: AGPL-3.0-or-later
"""Immutable metadata snapshots; no model evaluation or implicit rebuild."""
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sys

from .ilvis0_evidence_dataset import verify_artifacts


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False,ensure_ascii=False)+'\n').encode()
def load(path):return json.loads(Path(path).read_bytes())


class _SnapshotReader:
    """Read expanded snapshot bytes or their verified evidence-pack copy."""

    def __init__(self,destination):
        self.destination=Path(destination).resolve()
        self.store=None
        self.catalog=None
        self.root=None

    def read(self,name):
        from .studies.artifacts import ArchiveStore

        relative=Path(name)
        path=(self.destination/relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(self.destination):
            raise ValueError('snapshot path escapes destination')
        if path.is_file():return path.read_bytes()
        if self.store is None:
            for root in (self.destination,*self.destination.parents):
                if ((root/'repro/catalog.json.gz').is_file() or
                        (root/'repro/catalog.json').is_file()):
                    self.root=root
                    self.store=ArchiveStore(root)
                    self.catalog=self.store.catalog()
                    break
        if self.store is None:raise FileNotFoundError(path)
        return self.store._read(path.relative_to(self.root).as_posix(),
                                self.catalog)

    def verify(self,prefix,hashes):
        for name,expected in hashes.items():
            if hashlib.sha256(self.read(prefix+'/'+name)).hexdigest()!=expected:
                raise ValueError('artifact hash changed: '+name)

    def close(self):
        if self.store is not None:self.store.close()


def create(root,destination,*,version,inputs,sources,outputs,summary):
    if not isinstance(version,str) or not version:raise ValueError('explicit snapshot version required')
    root=Path(root);destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    with (destination/'snapshot.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (destination/'manifest.json').exists():raise ValueError('immutable snapshot exists; use a different version')
        verify_artifacts(root,inputs);verify_artifacts(root,sources)
        for prefix,names in (('frozen-inputs',inputs),('source-freeze',sources)):
            for name in names:
                target=destination/prefix/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,target)
        outputs=dict(outputs);outputs['dataset-summary.json']=encoded(summary)
        for name,data in outputs.items():
            target=destination/name
            if Path(name).is_absolute() or not target.resolve().is_relative_to(destination.resolve()):raise ValueError('snapshot output escapes root')
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        hashes={name:sha(destination/name) for name in outputs}
        manifest=dict(format_version='immutable-evidence-snapshot-v1',version=version,inputs=inputs,sources=sources,
            artifacts=hashes,summary=summary,metadata_python=sys.version,original_reads=0,model_evaluations=0,optimizer_starts=0)
        (destination/'manifest.json').write_bytes(encoded(manifest))
        (destination/'evidence-receipt.json').write_bytes(encoded(dict(manifest_sha256=sha(destination/'manifest.json'),artifacts=hashes)))
    return check(destination)


def check(destination,*,live_root=None):
    destination=Path(destination)
    if not (destination/'manifest.json').exists():raise ValueError('completed snapshot does not exist')
    manifest=load(destination/'manifest.json');receipt=load(destination/'evidence-receipt.json')
    if sha(destination/'manifest.json')!=receipt['manifest_sha256'] or manifest['artifacts']!=receipt['artifacts']:
        raise ValueError('snapshot manifest/receipt changed')
    reader=_SnapshotReader(destination)
    try:
        reader.verify('.',manifest['artifacts'])
        reader.verify('frozen-inputs',manifest['inputs'])
        reader.verify('source-freeze',manifest['sources'])
        if json.loads(reader.read('dataset-summary.json'))!=manifest['summary']:
            raise ValueError('snapshot summary identity changed')
    finally:reader.close()
    if live_root is not None:verify_artifacts(live_root,manifest['inputs'])
    return manifest


def publish(destination,public):
    destination=Path(destination);public=Path(public);manifest=check(destination)
    names=['manifest.json','evidence-receipt.json',*manifest['artifacts']]
    names+=['frozen-inputs/'+name for name in manifest['inputs']]
    names+=['source-freeze/'+name for name in manifest['sources']]
    reader=_SnapshotReader(destination)
    try:
        for name in names:
            target=public/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(reader.read(name))
    finally:reader.close()
    return check(public)
