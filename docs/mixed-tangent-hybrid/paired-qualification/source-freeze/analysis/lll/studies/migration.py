# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inventory only tracked study payloads; compact only verified byte duplicates."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess
from .artifacts import ArchiveStore, atomic, digest, encoded, safe_path

PAYLOADS=frozenset(('source-freeze','frozen-inputs','artifacts','shards','charges','realization-charges',
    'results','inputs','bound-reservations','bounds','native-qualification','saved-inputs','native',
    'starts','qualification','software-controls','run','kernel','evidence','proofs'))
PUBLIC_SUFFIXES=frozenset(('.md','.png','.svg','.csv','.html','.pdf'))


def tracked_payloads(root):
    raw=subprocess.check_output(['git','ls-files','-z','--','docs'],cwd=root).decode()
    selected=[]
    for name in raw.split('\0'):
        if not name:continue
        p=Path(name)
        if len(p.parts)<4 or p.parts[2] not in PAYLOADS:continue
        # Keep public pages/downloads; frozen source trees are restored as a unit.
        if p.suffix in PUBLIC_SUFFIXES and p.parts[2] not in ('source-freeze','frozen-inputs'):continue
        selected.append(name)
    return sorted(selected)


def migrate(root,*,restore_destination,names=None):
    root=Path(root).resolve();store=ArchiveStore(root);catalog=store.catalog();declared=names is not None
    candidates=tracked_payloads(root) if names is None else sorted(set(names))
    names=[n for n in candidates if n not in catalog['paths']]
    if not names:return dict(archived_files=0,new_objects=0)
    restore_destination=Path(restore_destination)
    if restore_destination.exists():raise ValueError('restoration audit requires a fresh destination')
    before=sum((root/n).stat().st_size for n in names)
    code=sum(Path(n).suffix in ('.py','.c','.cpp','.h','.hpp') for n in names)
    packed=store.pack(names)
    # A complete real restoration, independently hashed before any compaction.
    restored=store.restore(restore_destination,names=names)
    catalog=store.catalog()
    for name in names:
        if digest(safe_path(restore_destination,name).read_bytes())!=catalog['paths'][name]['sha256']:
            raise ValueError('restoration differs from original: '+name)
    for name in names:safe_path(restore_destination,name).unlink()
    removed=store.compact(names=names)
    report=dict(version='lll-repro-migration-v1',archived_files=len(names),archived_code_copies=code,
        original_bytes=before,unique_objects=packed['new_objects'],packs=packed['packs'],restored_files=restored,
        verified_removed_expanded_files=removed,scientific_results_changed=False,numerical_work=0,
        archived_bytes=sum(p.stat().st_size for p in (root/'repro/packs').glob('*.zip')))
    catalog=store.catalog()
    origin=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    catalog.setdefault('origin_commit',origin)
    if declared:
        for name in names:catalog['paths'][name]['origin_commit']=None
    store.save_catalog(catalog)
    history=root/'repro/migrations';previous=root/'repro/migration.json'
    if previous.exists() and not history.exists():atomic(history/'0001.json',previous.read_bytes())
    number=1+len(list(history.glob('*.json')))
    atomic(history/f'{number:04d}.json',encoded(report))
    atomic(previous,encoded(report));return report


def add_local_aliases(root,source_root):
    """Index only declared members with a matching closed public manifest."""
    from .aliases import index_local_duplicates
    return index_local_duplicates(root,source_root)
