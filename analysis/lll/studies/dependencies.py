# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resolve explicit project imports and quoted headers without scanning folders."""
import ast
from pathlib import Path
import re
from .artifacts import safe_path


def source_closure(root,seeds):
    root=Path(root).resolve();pending=list(seeds);seen=set()
    def module(parts):
        if not parts or parts[0]!='lll':return
        for size in range(1,len(parts)):
            name='analysis/'+'/'.join(parts[:size])+'/__init__.py'
            if safe_path(root,name).is_file():pending.append(name)
        base='analysis/'+'/'.join(parts)
        for name in (base+'.py',base+'/__init__.py'):
            if safe_path(root,name).is_file():pending.append(name);break
    while pending:
        name=pending.pop();path=safe_path(root,name);name=path.relative_to(root).as_posix()
        if name in seen:continue
        if not path.is_file():raise ValueError('declared source is missing: '+name)
        seen.add(name)
        if path.suffix=='.py':
            package=list(Path(name).parts[1:-1])
            for node in ast.walk(ast.parse(path.read_text(),filename=name)):
                # Loaders often name a sibling translation unit in Python,
                # rather than import it or include it from another C++ file.
                # Follow only those explicit literals; never enumerate a folder.
                target=None
                if isinstance(node,ast.Constant) and isinstance(node.value,str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\.(cpp|hpp|h)',node.value):
                    target=path.with_name(node.value)
                elif (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
                        and node.func.attr=='with_suffix' and len(node.args)==1
                        and isinstance(node.args[0],ast.Constant) and node.args[0].value in ('.cpp','.hpp','.h')):
                    target=path.with_suffix(node.args[0].value)
                if target is not None and target.is_file():pending.append(target.relative_to(root).as_posix())
                if isinstance(node,ast.Import):
                    for alias in node.names:module(alias.name.split('.'))
                elif isinstance(node,ast.ImportFrom):
                    prefix=package[:len(package)-node.level+1] if node.level else []
                    parts=prefix+(node.module.split('.') if node.module else [])
                    module(parts)
                    for alias in node.names:
                        if alias.name!='*':module(parts+[alias.name])
        elif path.suffix in ('.cpp','.hpp','.h'):
            for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"',path.read_text(),re.M):
                target=safe_path(root,(path.parent/include).relative_to(root).as_posix())
                pending.append(target.relative_to(root).as_posix())
    return sorted(seen)
