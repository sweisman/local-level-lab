# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compact a verified closed publication so new studies do not grow copied trees."""
import json
from pathlib import Path
from .artifacts import ArchiveStore,atomic,digest,encoded,safe_path
from .migration import PAYLOADS,PUBLIC_SUFFIXES


def archive_publication(root,data,public):
    from ..ilvis0_control_shards import verify_completion
    root=Path(root).resolve();data=Path(data).resolve();public=Path(public).resolve()
    if not data.is_relative_to(root) or not public.is_relative_to(root):raise ValueError('publication must stay in project')
    verify_completion(data)
    receipt=json.loads((public/'evidence-receipt.json').read_text());names=[]
    for relative,expected in receipt['artifacts'].items():
        parts=Path(relative).parts
        if not parts or parts[0] not in PAYLOADS:continue
        if Path(relative).suffix in PUBLIC_SUFFIXES and parts[0] not in ('source-freeze','frozen-inputs'):continue
        path=safe_path(public,relative)
        if digest(path.read_bytes())!=expected:raise ValueError('published bytes changed')
        names.append(str(path.relative_to(root)))
        original=safe_path(data,relative)
        if original.is_file():
            if digest(original.read_bytes())!=expected:raise ValueError('runtime/public artifact mismatch')
            names.append(str(original.relative_to(root)))
    store=ArchiveStore(root);packed=store.pack(names);catalog=store.catalog()
    for name in names:catalog['paths'][name]['origin_commit']=None
    store.save_catalog(catalog)
    removed=store.compact(names=names)
    from . import readers
    readers.evidence.cache_clear();readers.archive_directories.cache_clear()
    return dict(packed,compacted_files=removed,numerical_work=0)
