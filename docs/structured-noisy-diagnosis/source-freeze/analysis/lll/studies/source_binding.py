# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check a qualified source subset plus Definition's frozen execution files."""
from contextlib import contextmanager
from pathlib import PurePosixPath

from .artifacts import digest,encoded,safe_path

ENGINE_FILES=frozenset(('analysis/tests/ilvis0_control_shards.py','analysis/lll/ilvis0_control_shards.py',
    'analysis/lll/ilvis0_receipt_journal.py','analysis/lll/compute_budget.py','analysis/lll/__init__.py'))


def verify(root,*,declared,manifest):
    if (not isinstance(declared,dict) or not declared or not isinstance(manifest,dict)
            or not declared.keys()<=manifest.keys() or any(manifest[k]!=v for k,v in declared.items())):
        raise ValueError('unchanged qualified source subset required')
    extension={k:v for k,v in manifest.items() if k not in declared}
    for name in extension:
        p=PurePosixPath(name)
        if name not in ENGINE_FILES and not (str(p.parent)=='analysis/lll/studies' and p.suffix=='.py' and p.stem.isidentifier()):
            raise ValueError('only Definition shared execution files may extend qualified sources')
    for name,sha in manifest.items():
        if not isinstance(name,str) or not isinstance(sha,str) or digest(safe_path(root,name).read_bytes())!=sha:
            raise ValueError('frozen source bytes changed: '+str(name))
    return dict(qualified_count=len(declared),manifest_count=len(manifest),engine_extension_count=len(extension),
        engine_extension=extension,qualified_source_list_sha256=digest(encoded(declared)),
        manifest_source_list_sha256=digest(encoded(manifest)),all_frozen_source_bytes_verified=True)


@contextmanager
def enumeration(adapter,names):
    """Supply an already verified manifest list to a closed-result checker only.

    This changes one in-process enumeration callback, never source files or a
    scientific calculation. The original callback is restored even on failure.
    """
    names=tuple(names)
    if not names or len(set(names))!=len(names):raise ValueError('distinct verified manifest sources required')
    original=adapter.qualification_sources
    adapter.qualification_sources=lambda root:list(names)
    try:yield
    finally:adapter.qualification_sources=original
