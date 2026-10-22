# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import gzip
import json
import zipfile
from pathlib import Path

import pytest

from lll.studies.artifacts import ArchiveStore, atomic, digest, encoded


def example(root):
    files={'docs/example/source-freeze/analysis/core.py': b'print(42)\n',
           'docs/example/charges/00000001.json': b'{"charged":1}\n',
           'docs/other/source-freeze/analysis/core.py': b'print(42)\n'}
    for name,data in files.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return files


def test_lossless_deduplicated_restore_and_verified_compaction(tmp_path):
    files=example(tmp_path);store=ArchiveStore(tmp_path)
    report=store.pack(files)
    assert report['paths']==3 and report['new_objects']==2
    assert store.verify()['paths']==3
    destination=tmp_path/'restored';store.restore(destination)
    assert {n:(destination/n).read_bytes() for n in files}==files
    assert store.compact()==3
    assert all(not (tmp_path/n).exists() for n in files)
    assert {n:store.read(n) for n in files}==files
    assert store.pack(files)['new_objects']==0


def test_changed_expanded_file_is_never_removed_or_hidden(tmp_path):
    files=example(tmp_path);store=ArchiveStore(tmp_path);store.pack(files)
    path=next(iter(files));(tmp_path/path).write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):store.compact()
    with pytest.raises(ValueError,match='changed'):store.read(path)
    assert all((tmp_path/n).exists() for n in files)


def test_corruption_and_missing_pack_fail_closed(tmp_path):
    files=example(tmp_path);store=ArchiveStore(tmp_path);store.pack(files)
    pack=next((tmp_path/'repro/packs').glob('*.zip'));data=pack.read_bytes()
    pack.write_bytes(data[:-16])
    with pytest.raises(ValueError):store.verify()
    pack.unlink()
    with pytest.raises(ValueError):store.verify()


@pytest.mark.parametrize('name',['../outside','/absolute','docs/../outside','docs/a\\b',''])
def test_unsafe_paths_rejected(tmp_path,name):
    store=ArchiveStore(tmp_path)
    with pytest.raises(ValueError):store.pack([name])


def test_restore_rejects_symlink_escape_and_never_overwrites(tmp_path):
    files=example(tmp_path);store=ArchiveStore(tmp_path);store.pack(files)
    dest=tmp_path/'dest';dest.mkdir();(dest/'docs').symlink_to(tmp_path/'docs',target_is_directory=True)
    with pytest.raises(ValueError):store.restore(dest)
    dest2=tmp_path/'dest2';p=dest2/next(iter(files));p.parent.mkdir(parents=True);p.write_bytes(b'other')
    with pytest.raises(ValueError):store.restore(dest2)
    assert p.read_bytes()==b'other'


def test_deterministic_packs_and_index_tamper_rejected(tmp_path):
    a=tmp_path/'a';b=tmp_path/'b';fa=example(a);fb=example(b)
    sa=ArchiveStore(a);sb=ArchiveStore(b);sa.pack(fa);sb.pack(reversed(fb))
    assert sa.catalog_path.read_bytes()==sb.catalog_path.read_bytes()
    ca=sa.catalog();ca['paths'][next(iter(fa))]['size']=1000
    sa.catalog_path.write_bytes(gzip.compress(encoded(ca),mtime=0))
    with pytest.raises(ValueError):sa.verify()


def test_partial_restore_then_compact_preserves_unlisted_files(tmp_path):
    files=example(tmp_path);store=ArchiveStore(tmp_path);store.pack(files);store.compact()
    name=next(iter(files));store.restore(tmp_path,names=[name]);other=tmp_path/'docs/personal.txt';other.write_text('leave')
    assert store.compact(names=[name])==1 and other.read_text()=='leave'


def test_new_catalog_is_compressed_and_checksummed(tmp_path):
    files=example(tmp_path);store=ArchiveStore(tmp_path);store.pack(files)
    assert store.catalog_path.name=='catalog.json.gz'
    raw=store.catalog_path.read_bytes()
    assert gzip.decompress(raw)==encoded(store.catalog())
    assert store.catalog_path.with_suffix('.sha256').read_text().strip()==digest(raw)
    assert not (tmp_path/'repro/catalog.json').exists()


def legacy_store(root):
    files=example(root);store=ArchiveStore(root);store.pack(files)
    catalog=store.catalog();raw=encoded(catalog)
    store.catalog_path.unlink();store.catalog_path.with_suffix('.sha256').unlink()
    atomic(root/'repro/catalog.json',raw)
    atomic(root/'repro/catalog.sha256',(digest(raw)+'\n').encode())
    return store,files,catalog


def test_legacy_catalog_remains_readable_and_upgrades_losslessly(tmp_path):
    store,files,catalog=legacy_store(tmp_path)
    assert store.catalog()==catalog
    assert {n:store.read(n) for n in files}==files
    store.save_catalog(catalog)
    assert store.catalog()==catalog
    assert not (tmp_path/'repro/catalog.json').exists()
    assert not (tmp_path/'repro/catalog.sha256').exists()
    store.compact();dest=tmp_path/'restored';store.restore(dest)
    assert {n:(dest/n).read_bytes() for n in files}==files


def test_corrupt_legacy_catalog_is_not_migrated(tmp_path):
    store,_,_=legacy_store(tmp_path)
    legacy=tmp_path/'repro/catalog.json';legacy.write_bytes(b'{}')
    with pytest.raises(ValueError,match='checksum'):store.catalog()
    assert legacy.exists()


def test_compressed_catalog_rejects_invalid_gzip_even_with_matching_hash(tmp_path):
    store=ArchiveStore(tmp_path);store.pack(example(tmp_path))
    raw=b'not a gzip file';atomic(store.catalog_path,raw)
    atomic(store.catalog_path.with_suffix('.sha256'),(digest(raw)+'\n').encode())
    with pytest.raises(ValueError,match='invalid.*catalog'):store.catalog()


def test_different_legacy_and_compressed_catalogs_fail_closed(tmp_path):
    store=ArchiveStore(tmp_path);store.pack(example(tmp_path))
    raw=encoded(dict(version='lll-evidence-packs-v1',paths={},objects={},packs={}))
    atomic(tmp_path/'repro/catalog.json',raw)
    atomic(tmp_path/'repro/catalog.sha256',(digest(raw)+'\n').encode())
    with pytest.raises(ValueError,match='conflicting.*catalog'):store.catalog()
