# SPDX-License-Identifier: AGPL-3.0-or-later
"""Index only exact declared public members of matching completed local studies."""
import json
from pathlib import Path
import re
from .artifacts import ArchiveStore,atomic,digest,encoded,safe_path


def index_local_duplicates(root,source_root):
    from .migration import PAYLOADS
    root=Path(root).resolve();source_root=Path(source_root).resolve();store=ArchiveStore(root)
    catalog=store.catalog();public={}
    for name,record in catalog['paths'].items():
        parts=Path(name).parts
        if len(parts)>3 and parts[0]=='docs' and parts[2] in PAYLOADS:
            public.setdefault('/'.join(parts[:2]),[]).append(('/'.join(parts[2:]),record))
    # Rebuild this derived index; no unpublished or unfamiliar filename is inspected.
    catalog['paths']={n:r for n,r in catalog['paths'].items() if not n.startswith('data/')}
    registry=json.loads((source_root/'analysis/study-status.json').read_text());added=0;matched=0;different=0
    for item in registry['studies']:
        name=item['path']
        if not name.startswith('data/'):continue
        directory=safe_path(source_root,name)
        if not (directory/'completion.json').is_file() or not (directory/'manifest.json').is_file():continue
        manifest_sha=digest((directory/'manifest.json').read_bytes());stem=Path(name).name
        for candidate in sorted({stem,re.sub(r'-\d{8}$','',stem)}):
            prefix='docs/'+candidate;manifest=root/prefix/'manifest.json'
            if not manifest.is_file() or digest(manifest.read_bytes())!=manifest_sha:continue
            matched+=1
            for relative,record in public.get(prefix,[]):
                if Path(relative).suffix=='.lock':continue
                path=safe_path(directory,relative)
                if not path.is_file():continue
                raw=path.read_bytes()
                if digest(raw)!=record['sha256']:
                    different+=1
                    continue
                catalog['paths'][name+'/'+relative]=dict(sha256=record['sha256'],size=len(raw),mode=path.stat().st_mode&0o777)
                added+=1
            break
    store.save_catalog(catalog)
    return dict(local_duplicate_aliases=added,matched_completed_studies=matched,
        different_members_preserved=different,unknown_paths_inspected=False)
