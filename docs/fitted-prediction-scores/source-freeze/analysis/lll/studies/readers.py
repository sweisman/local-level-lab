# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verified read-only archive views shared by status, reports and the website."""
from functools import lru_cache
from pathlib import Path
from .artifacts import ArchiveStore,safe_path


@lru_cache(maxsize=8)
def evidence(root):
    store=ArchiveStore(Path(root));return store,store.catalog()


def available(root,name):
    path=safe_path(root,name)
    if path.is_file():return True
    _,catalog=evidence(str(Path(root).resolve()));return name in catalog['paths']


def read(root,name):
    store,catalog=evidence(str(Path(root).resolve()));return store._read(name,catalog)


def origin(root,name):
    _,catalog=evidence(str(Path(root).resolve()))
    if name in catalog['paths']:
        # Local runtime copies were never published at their data/ paths in Git.
        if name.startswith('data/'):return None
        return catalog['paths'][name].get('origin_commit',catalog.get('origin_commit','main'))
    return archive_directories(str(Path(root).resolve())).get(name.rstrip('/'),'main')


@lru_cache(maxsize=8)
def archive_directories(root):
    _,catalog=evidence(root);parents={}
    for name,record in catalog['paths'].items():
        revision=None if name.startswith('data/') else record.get('origin_commit',catalog.get('origin_commit','main'))
        for path in Path(name).parents:
            parent=str(path)
            if parent!='.' and parents.get(parent) is None:parents[parent]=revision
    return parents


def bundle(root,name):
    _,catalog=evidence(str(Path(root).resolve()))
    record=catalog['paths'].get(name)
    return None if record is None else ('repro/'+catalog['objects'][record['sha256']],record['sha256'])
