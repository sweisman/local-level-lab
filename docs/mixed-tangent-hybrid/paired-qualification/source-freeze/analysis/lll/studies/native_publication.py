# SPDX-License-Identifier: AGPL-3.0-or-later
"""Include explicitly selected native cache artifacts in a closed publication.

No cache discovery, compilation, numerical imports, propagation or fitting.
Call after generic publication and before verified archive compaction.
"""
import json
from pathlib import Path
import re

from .artifacts import atomic,digest,encoded,safe_path

_ASSET=re.compile(r'shards/[0-9]{3}/kernels/[A-Za-z0-9_.-]+\.(?:cpp|so|json|sqlite)')


def include_native_caches(root,data,public,*,entries,maximum_bytes):
    from ..ilvis0_control_shards import verify_completion
    root=Path(root).resolve();data=Path(data).resolve();public=Path(public).resolve()
    if (not data.is_relative_to(root/'data') or data==root/'data'
            or not public.is_relative_to(root/'docs') or public==root/'docs'
            or type(maximum_bytes) is not int or maximum_bytes<1
            or not isinstance(entries,list) or not 1<=len(entries)<=64):
        raise ValueError('closed project data/publication, explicit native assets and finite byte allowance required')
    verify_completion(data)
    receipt_path=public/'evidence-receipt.json';receipt=json.loads(receipt_path.read_bytes())
    if not isinstance(receipt.get('artifacts'),dict):raise ValueError('existing publication receipt required')
    pending=[];seen=set();size=0
    for entry in entries:
        if (not isinstance(entry,dict) or set(entry)!={'path','sha256'}
                or not isinstance(entry['path'],str) or not _ASSET.fullmatch(entry['path'])
                or entry['path'] in seen or not isinstance(entry['sha256'],str)
                or not re.fullmatch(r'[a-f0-9]{64}',entry['sha256'])):
            raise ValueError('unique safe native cache path and exact SHA-256 required')
        name=entry['path'];sha=entry['sha256'];seen.add(name)
        source=safe_path(data,name);target=safe_path(public,name)
        size+=source.stat().st_size
        if size>maximum_bytes:raise ValueError('native publication byte allowance exceeded')
        raw=source.read_bytes()
        if digest(raw)!=sha:raise ValueError('declared native asset checksum differs')
        if (name in receipt['artifacts'] and receipt['artifacts'][name]!=sha
                or target.exists() and (not target.is_file() or target.read_bytes()!=raw)):
            raise ValueError('native publication would overwrite different bytes')
        pending.append((name,target,raw,sha))
    # Check all paths, hashes and existing destinations before publishing any.
    for name,target,raw,sha in pending:
        if not target.exists():atomic(target,raw)
        receipt['artifacts'][name]=sha
    atomic(receipt_path,encoded(receipt))
    return dict(files=len(pending),bytes=size,numerical_work=0)
