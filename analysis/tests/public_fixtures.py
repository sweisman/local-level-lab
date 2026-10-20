# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only relocation of sealed campaign fixtures for clean-checkout tests.

Frozen worker/test sources stay unchanged. Their own SHA-256 checks still run
against the original bytes. This adapter neither rewrites metadata nor supplies
recordings, credentials, optimizer outputs or replacement scientific values.
"""
import os
from pathlib import Path

GENERATED_RUNTIME_COPIES = {
    'ilvis0-affine-support-qualification-20261019': 'ilvis0-affine-support-qualification',
    'ilvis0-correlated-clock-controls-20261019': 'ilvis0-correlated-clock-controls',
    'ilvis0-native-training-contraction-20261019': 'ilvis0-native-training-contraction',
}


def generated_read_path(root):
    """Relocate only the named generated prerequisites, even on a local checkout."""
    root = Path(root)
    def remap(value):
        if not isinstance(value, (str, os.PathLike)):
            return value
        path = Path(value)
        if not path.is_relative_to(root / 'data'):
            return value
        parts = path.relative_to(root / 'data').parts
        if not parts or parts[0] not in GENERATED_RUNTIME_COPIES:
            return value
        return root / 'docs' / GENERATED_RUNTIME_COPIES[parts[0]] / Path(*parts[1:])
    return remap


def public_read_path(root,*,recorded_root=Path('/site/repo/local-level-lab')):
    root=Path(root);recorded_root=Path(recorded_root)
    def remap(value):
        if not isinstance(value,(str,os.PathLike)):return value
        path=Path(value)
        if path.is_relative_to(recorded_root):path=root/path.relative_to(recorded_root)
        if not path.is_relative_to(root):return value
        relative=path.relative_to(root)
        if str(relative)=='data/ilvis0-boundary-diagnostic-20261016/manifest.json':
            return root/'docs/ilvis0-last-zero-boundary-20261018/source-freeze'/relative
        if len(relative.parts)>1 and relative.parts[0]=='data' and relative.parts[1].startswith('ilvis0-'):
            return root/'docs'/Path(*relative.parts[1:])
        return path
    return remap


def read_adapter(original,remap):
    def opened(file,mode='r',*args,**kwargs):
        if 'r' in mode and not any(c in mode for c in ('+','w','a','x')):file=remap(file)
        return original(file,mode,*args,**kwargs)
    return opened


def source_aliases(root,values):
    """Expose local names after original source hashing, retaining frozen keys."""
    result=dict(values);remap=public_read_path(root)
    for path,digest in values.items():result[str(remap(path))]=digest
    return result
