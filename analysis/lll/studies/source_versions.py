# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resolve a declared source version without substituting a newer checkout file."""
from functools import lru_cache
import json
from pathlib import Path
import re

from .artifacts import digest,safe_path
from .readers import evidence


@lru_cache(maxsize=8)
def _versions(root):
    _,catalog=evidence(root);index={}
    for alias,record in catalog['paths'].items():
        if alias.startswith('docs/') and '/source-freeze/' in alias:
            name=alias.split('/source-freeze/',1)[1]
            index.setdefault((name,record['sha256']),alias)
    return index


def read_source(root,name,expected_sha256):
    """Read only an exact same-name source alias with its declared SHA-256.

    Ordinary scientific artifacts never receive this source-version fallback.
    Hash checks on expanded frozen files and archive packs remain in force.
    """
    root=Path(root).resolve();current=safe_path(root,name)
    if (not name.startswith(('analysis/','docs/')) or current.suffix not in ('.py','.c','.cc','.cpp','.cxx','.hpp','.h')
            or not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_sha256)):
        raise ValueError('declared project source path and exact version hash required')
    if current.is_file():
        raw=current.read_bytes()
        if digest(raw)==expected_sha256:return raw
    store,catalog=evidence(str(root));alias=_versions(str(root)).get((name,expected_sha256))
    if alias is not None:
        raw=store._read(alias,catalog)
    else:
        registry=root/'repro/source-versions.json'
        versions=json.loads(registry.read_bytes()) if registry.is_file() else {}
        alias=versions.get(name,{}).get(expected_sha256)
        if (not isinstance(alias,str) or not alias.startswith('docs/')
                or not alias.endswith('/source-freeze/'+name)):
            raise ValueError('no verified frozen version of source: '+name)
        raw=safe_path(root,alias).read_bytes()
    if digest(raw)!=expected_sha256:raise ValueError('frozen source version hash mismatch: '+name)
    return raw
