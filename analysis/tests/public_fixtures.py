# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only relocation of sealed campaign fixtures for clean-checkout tests.

Frozen worker/test sources stay unchanged. Their own SHA-256 checks still run
against the original bytes. This adapter neither rewrites metadata nor supplies
recordings, credentials, optimizer outputs or replacement scientific values.
"""
import os
from pathlib import Path
from contextlib import contextmanager

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


def public_read_path(root,*,recorded_root=Path('/site/repo/local-level-lab'),temporary_root=None,source_freeze=None):
    root=Path(root);recorded_root=Path(recorded_root)
    def remap(value):
        if not isinstance(value,(str,os.PathLike)):return value
        path=Path(value)
        if temporary_root is not None and path.is_relative_to(temporary_root):return value
        if not path.is_relative_to(root) and path.is_relative_to(recorded_root):
            path=root/path.relative_to(recorded_root)
        if not path.is_relative_to(root):return value
        relative=path.relative_to(root)
        if source_freeze is not None and relative.parts[:2]==('analysis','lll'):
            return Path(source_freeze)/relative
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


@contextmanager
def archived_read_path(root,cache):
    """Materialize only requested public archive aliases into a test cache."""
    from lll.studies.artifacts import ArchiveStore
    root,cache=(Path(p).resolve() for p in (root,cache));store=None;catalog=None
    def remap(value):
        nonlocal store,catalog
        if not isinstance(value,(str,os.PathLike)):return value
        path=Path(value)
        if not path.is_relative_to(root/'docs') or path.is_file():return value
        if store is None:store=ArchiveStore(root);catalog=store.catalog()
        name=path.relative_to(root).as_posix()
        if name not in catalog['paths']:return value
        target=cache/name
        if not target.is_file():
            raw=store._read(name,catalog);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        return target
    try:yield remap
    finally:
        if store is not None:store.close()


@contextmanager
def qualified_worker(root,public,module_name,destination,*,read_path=lambda p:p,prerequisites=()):
    """Execute a legacy lifecycle test with its actual frozen library graph.

    This is test isolation, not hash substitution: both executed modules and
    files checked by the worker come from the same verified source snapshot.
    The checkout and its imported module objects are restored unchanged.
    """
    import hashlib
    import importlib
    import json
    import sys
    root,public,destination=(Path(p).resolve() for p in (root,public,destination))
    if not public.is_relative_to(root/'docs'):raise ValueError('public project snapshot required')
    pending=[(public,None)]+[(Path(p),None) for p in prerequisites];seen={};verified={}
    while pending:
        directory,expected_manifest=pending.pop()
        if not directory.resolve().is_relative_to(root/'docs'):raise ValueError('public prerequisite required')
        raw=Path(read_path(directory/'manifest.json')).read_bytes();sha=hashlib.sha256(raw).hexdigest()
        if expected_manifest is not None and sha!=expected_manifest:raise ValueError('prerequisite manifest mismatch')
        if directory in seen:continue
        receipt=json.loads(Path(read_path(directory/'evidence-receipt.json')).read_bytes())['artifacts']
        if sha!=receipt['manifest.json']:raise ValueError('frozen manifest hash mismatch')
        seen[directory]=sha
        for name,expected in json.loads(raw)['sources'].items():
            relative=Path(name)
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('safe frozen source path required')
            data=Path(read_path(directory/'source-freeze'/relative)).read_bytes()
            if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('frozen source hash mismatch: '+name)
            if name in verified and verified[name]!=data:raise ValueError('conflicting qualified source versions: '+name)
            verified[name]=data
            if name.startswith('docs/') and name.endswith('/manifest.json'):
                pending.append((root/relative.parent,expected))
    entry='analysis/tests/'+module_name+'.py'
    if entry not in verified:raise ValueError('worker must belong to the verified source snapshot')
    for name,data in verified.items():
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    def selected(name):
        return name=='lll' or name.startswith(('lll.','ilvis0_')) or name==module_name
    saved={name:value for name,value in sys.modules.items() if selected(name)};paths=list(sys.path)
    try:
        for name in saved:sys.modules.pop(name,None)
        sys.path[:0]=[str(destination/'analysis/tests'),str(destination/'analysis')]
        importlib.invalidate_caches()
        yield importlib.import_module(module_name)
    finally:
        for name in list(sys.modules):
            if selected(name):sys.modules.pop(name,None)
        sys.modules.update(saved);sys.path[:]=paths;importlib.invalidate_caches()


def qualified_read_path(root,destination):
    """Relocate prerequisite reads only; library reads stay in the frozen tree."""
    root,destination=(Path(p).resolve() for p in (root,destination))
    generated=generated_read_path(root)
    def remap(value):
        if not isinstance(value,(str,os.PathLike)):return value
        path=Path(value)
        if path.is_relative_to(destination):
            relative=path.relative_to(destination)
            if relative.parts and relative.parts[0]=='docs' and not path.is_file():return root/relative
            if relative.parts and relative.parts[0]=='data':
                candidate=root/relative;mapped=generated(candidate)
                return mapped if mapped!=candidate else value
        return generated(value)
    return remap


def reference_fixture(path):
    """Reference accessors define helpers; they do not execute a study or CLI."""
    import ast
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):continue
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
        return False
    return True
