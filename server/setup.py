# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read the canonical source version; sdists retain it in generated PKG-INFO."""
import ast
from email.parser import Parser
from pathlib import Path

from setuptools import setup

root = Path(__file__).resolve().parent
source = root.parent / "analysis" / "lll" / "__init__.py"
if source.exists():
    tree = ast.parse(source.read_text())
    version = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "__version__" for t in n.targets))
else:
    version = Parser().parsestr((root / "PKG-INFO").read_text())["Version"]
    if not version:
        raise RuntimeError("source distribution has no version")
setup(version=version)
