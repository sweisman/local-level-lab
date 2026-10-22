# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from lll.studies.artifacts import ArchiveStore


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
    assert (a/'repro/catalog.json').read_bytes()==(b/'repro/catalog.json').read_bytes()
    ca=json.loads((a/'repro/catalog.json').read_text());ca['paths'][next(iter(fa))]['size']=1000
    (a/'repro/catalog.json').write_text(json.dumps(ca))
    with pytest.raises(ValueError):sa.verify()


def test_partial_restore_then_compact_preserves_unlisted_files(tmp_path):
    files=example(tmp_path);store=ArchiveStore(tmp_path);store.pack(files);store.compact()
    name=next(iter(files));store.restore(tmp_path,names=[name]);other=tmp_path/'docs/personal.txt';other.write_text('leave')
    assert store.compact(names=[name])==1 and other.read_text()=='leave'
