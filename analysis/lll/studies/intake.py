# SPDX-License-Identifier: AGPL-3.0-or-later
"""Preserve only explicitly registered source and published evidence paths."""
import json
import ast
from pathlib import Path
import re
import subprocess
from .artifacts import ArchiveStore,atomic,digest,encoded,safe_path


def preserve_linked_pages(source_root,target_root,names):
    """Preserve exact public page paths reported missing by the site builder."""
    source_root=Path(source_root).resolve();target_root=Path(target_root).resolve()
    receipt=target_root/'repro/intake-receipt.json'
    report=json.loads(receipt.read_text()) if receipt.is_file() else dict(version='lll-registered-intake-v1',copied={})
    added=0
    for name in sorted(set(names)):
        if not name.startswith('docs/') or Path(name).suffix!='.md':
            raise ValueError('only explicitly linked public Markdown pages allowed')
        source=safe_path(source_root,name);target=safe_path(target_root,name)
        if not source.is_file():continue
        raw=source.read_bytes()
        if target.exists():
            if target.read_bytes()!=raw:raise ValueError('existing page differs: '+name)
            continue
        atomic(target,raw);report['copied'][name]=digest(raw);added+=1
    atomic(receipt,encoded(report));return added


def preserve_completed(source_root,target_root):
    source_root=Path(source_root).resolve();target_root=Path(target_root).resolve()
    registry=json.loads((source_root/'analysis/study-status.json').read_text())
    prior=target_root/'repro/intake-receipt.json'
    old=json.loads(prior.read_text()) if prior.exists() else {}
    copied=dict(old.get('copied',{}));unchanged=0;conflicts=[];known_sources=set();publications=set()
    catalog=ArchiveStore(target_root).catalog()
    def copy(name,expected=None):
        nonlocal unchanged
        source=safe_path(source_root,name);target=safe_path(target_root,name)
        if not source.is_file():raise ValueError('declared source missing: '+name)
        raw=source.read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('published artifact changed: '+name)
        if name in catalog['paths'] and catalog['paths'][name]['sha256']==sha:
            unchanged+=1;return
        if target.exists():
            if digest(target.read_bytes())!=sha:conflicts.append(name)
            else:unchanged+=1
        else:atomic(target,raw);target.chmod(source.stat().st_mode&0o777);copied[name]=sha
    for item in registry['studies']:
        name=item['path']
        if not name.startswith('data/'):continue
        directory=safe_path(source_root,name)
        manifest=directory/'manifest.json'
        if not manifest.is_file():continue
        value=json.loads(manifest.read_text())
        sources=value.get('sources',{})
        if isinstance(sources,dict):known_sources.update(n for n in sources if n.startswith(('analysis/lll/','analysis/tests/','docs/')))
        stem=Path(name).name
        for candidate in {stem,re.sub(r'-\d{8}$','',stem)}:
            public=source_root/'docs'/candidate;receipt=public/'evidence-receipt.json'
            if not receipt.is_file() or not (directory/'completion.json').is_file():continue
            entries=json.loads(receipt.read_text()).get('artifacts',{})
            # Validate the entire publication before copying any member.
            for artifact,sha in entries.items():
                path=safe_path(public,artifact)
                if not path.is_file() or digest(path.read_bytes())!=sha:
                    raise ValueError('incomplete declared publication: '+str(path))
            for artifact,sha in entries.items():copy(str((public/artifact).relative_to(source_root)),sha)
            copy(str(receipt.relative_to(source_root)));publications.add(str(public.relative_to(source_root)))
            for dependency in sources:
                if dependency.startswith(str(public.relative_to(source_root))+'/') and (source_root/dependency).is_file():copy(dependency)
    tracked=subprocess.check_output(['git','ls-files','-z','--','analysis/tests'],cwd=source_root).decode().split('\0')
    for name in set(tracked)|known_sources.copy():
        if not name.startswith('analysis/tests/') or not name.endswith('.py'):continue
        path=safe_path(source_root,name)
        if not path.is_file():continue
        try:tree=ast.parse(path.read_text())
        except SyntaxError:continue
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.startswith('docs/'):
                try:dependency=safe_path(source_root,node.value)
                except ValueError:continue
                if dependency.is_file():known_sources.add(node.value)
    for name in sorted(known_sources):
        if (source_root/name).is_file():copy(name)
    report=dict(version='lll-registered-intake-v1',copied=copied,unchanged=unchanged,
        preserved_existing_differences=sorted(set(conflicts)),publications=sorted(publications),
        unknown_paths_inspected=False,numerical_work=0)
    atomic(target_root/'repro/intake-receipt.json',encoded(report));return dict(copied=len(copied),
        sources=sum(n.startswith('analysis/') for n in copied),publications=len(publications),
        preserved_existing_differences=len(set(conflicts)))
