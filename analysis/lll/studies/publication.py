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


def archive_preparation(root,definition_path):
    """Archive only declared local preparation copies after their study closes.

    Only declared copies inside the preparation's dedicated directory are accepted.
    Every compacted byte remains recoverable through a verified archive alias.
    """
    from ..ilvis0_control_shards import IDENTITY
    root=Path(root).resolve();definition=safe_path(root,definition_path);base=definition.parent
    if not base.is_relative_to(root/'data') or base==root/'data':
        raise ValueError('a dedicated data preparation directory is required')
    store=ArchiveStore(root);catalog=store.catalog()
    try:
        value=json.loads(store._read(definition.relative_to(root).as_posix(),catalog))
        if not isinstance(value.get('id'),str) or not IDENTITY.fullmatch(value['id']):
            raise ValueError('safe declared study identity required')
        names={definition.relative_to(root).as_posix()}
        for name in value['inputs'].values():
            path=safe_path(root,name)
            if not path.is_relative_to(base):raise ValueError('external inputs cannot be compacted as preparation copies')
            names.add(path.relative_to(root).as_posix())
        prefix='data/'+value['id']
        try:completion=json.loads(store._read(prefix+'/completion.json',catalog))
        except FileNotFoundError as exc:raise ValueError('closed study required before preparation compaction') from exc
        manifest_bytes=store._read(prefix+'/manifest.json',catalog)
        if completion['state'] not in ('complete','terminal') or digest(manifest_bytes)!=completion['manifest_sha256']:
            raise ValueError('closed manifest hash mismatch')
        manifest=json.loads(manifest_bytes)
        if set(manifest['inputs'])!=set(value['inputs']):raise ValueError('declared input identities differ')
        for key,name in value['inputs'].items():
            frozen=manifest['inputs'][key]
            if frozen['source']!=name or digest(store._read(name,catalog))!=frozen['sha256']:
                raise ValueError('preparation input differs from its closed freeze')
        packed=store.pack(sorted(names));removed=store.compact(names=sorted(names))
    finally:store.close()
    from . import readers
    readers.evidence.cache_clear();readers.archive_directories.cache_clear()
    return dict(packed,compacted_files=removed,numerical_work=0)
