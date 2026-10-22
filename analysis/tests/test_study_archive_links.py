# SPDX-License-Identifier: AGPL-3.0-or-later
"""Archived links must not point to paths absent from historical Git commits."""
import importlib.util
from pathlib import Path

from lll.studies.artifacts import ArchiveStore,atomic,encoded,digest
from lll.studies.readers import origin


def fixture(root):
    files={'docs/new/source-freeze/code.py':b'# preserved\n',
           'data/local/artifacts/result.json':b'{"answer":42}\n'}
    for name,raw in files.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    store=ArchiveStore(root);store.pack(files);store.compact()
    catalog=store.catalog();catalog['origin_commit']='a'*40
    catalog['paths']['docs/new/source-freeze/code.py']['origin_commit']=None
    raw=encoded(catalog);atomic(store.catalog_path,raw)
    atomic(store.catalog_path.with_suffix('.sha256'),(digest(raw)+'\n').encode())
    return store,catalog


def test_local_alias_and_new_snapshot_directory_have_no_historical_git_origin(tmp_path):
    fixture(tmp_path)
    assert origin(tmp_path,'data/local/artifacts/result.json') is None
    assert origin(tmp_path,'docs/new/source-freeze/') is None


def test_new_snapshot_directory_links_to_restore_guide_and_alias_to_pack(tmp_path):
    root=tmp_path/'repo';store,catalog=fixture(root)
    (root/'README.md').write_text('# Home\n\n[Snapshot](docs/new/source-freeze/) [Data](data/local/artifacts/result.json)\n')
    (root/'docs/REPRODUCIBILITY.md').write_text('# Restore\n\n## Inspect, verify and restore\n')
    path=Path(__file__).resolve().parents[2]/'website/build.py'
    spec=importlib.util.spec_from_file_location('archive_site_build',path)
    site=importlib.util.module_from_spec(spec);spec.loader.exec_module(site)
    output=tmp_path/'site';report=site.build(root,output,assets=site.HERE/'assets',navigation=False)
    text=(output/'index.html').read_text()
    record=catalog['paths']['data/local/artifacts/result.json']
    pack=catalog['objects'][record['sha256']]
    assert '/blob/main/repro/'+pack+'#sha256-'+record['sha256'] in text
    assert '/docs/REPRODUCIBILITY.html#inspect-verify-and-restore' in text
    assert report['missing_pages']==[] and report['missing_fragments']==[]
