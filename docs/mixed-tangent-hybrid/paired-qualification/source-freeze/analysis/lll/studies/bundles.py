# SPDX-License-Identifier: AGPL-3.0-or-later
"""Register an explicit nested evidence bundle without copying its ZIP payloads."""
import copy
from pathlib import Path

from .artifacts import ArchiveStore,digest,safe_path


def register(root,prefix):
    root=Path(root).resolve();directory=safe_path(root,prefix)
    target=ArchiveStore(root);source=ArchiveStore(directory)
    try:
        if (not source.directory.is_relative_to(target.directory)
                or source.directory==target.directory):
            raise ValueError('explicit bundle inside the project archive tree required')
        if not source.catalog_path.is_file() and not (source.directory/'catalog.json').is_file():
            raise ValueError('existing verified bundle catalog required')
        incoming=source.catalog();source.verify()
        original=target.catalog();merged=copy.deepcopy(original)
        added_aliases=0;added_objects=0;added_packs=0
        # Validate conflicts and expanded bytes before changing the main index.
        for name,record in incoming['paths'].items():
            path=safe_path(root,name);old=merged['paths'].get(name)
            if old and (old['sha256']!=record['sha256'] or old['size']!=record['size']):
                raise ValueError('bundle alias conflict: '+name)
            if path.is_file():
                raw=path.read_bytes()
                if digest(raw)!=record['sha256'] or len(raw)!=record['size']:
                    raise ValueError('expanded bundle alias conflict: '+name)
            if old is None:
                merged['paths'][name]=dict(record,origin_commit=None);added_aliases+=1
        relative=source.directory.relative_to(target.directory)
        for sha,pack in incoming['objects'].items():
            if sha in merged['objects']:continue
            name=(relative/pack).as_posix();safe_path(target.directory,name)
            pack_sha=incoming['packs'][pack]
            if name in merged['packs'] and merged['packs'][name]!=pack_sha:
                raise ValueError('bundle pack conflict: '+name)
            if name not in merged['packs']:added_packs+=1
            merged['packs'][name]=pack_sha;merged['objects'][sha]=name;added_objects+=1
        if added_aliases or added_objects or added_packs:
            target.save_catalog(merged)
            try:target.verify(names=list(incoming['paths']))
            except Exception:
                target.save_catalog(original)
                raise
            from .readers import evidence,archive_directories
            from .source_versions import _versions
            evidence.cache_clear();archive_directories.cache_clear();_versions.cache_clear()
        return dict(added_aliases=added_aliases,added_objects=added_objects,added_packs=added_packs,
            payload_bytes_copied=0,numerical_work=0)
    finally:source.close();target.close()
