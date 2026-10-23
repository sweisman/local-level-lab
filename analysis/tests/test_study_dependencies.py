# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_dependency_closure_follows_only_explicit_project_imports_and_headers(tmp_path):
    from lll.studies.dependencies import source_closure
    base=tmp_path/'analysis/lll';base.mkdir(parents=True)
    files={'__init__.py':'','candidate.py':'from . import helper\nimport numpy\n',
        'helper.py':'from lll.nested import leaf\n','nested/__init__.py':'',
        'nested/leaf.py':'from .. import helper\n','kernel.cpp':'#include "kernel.hpp"\n',
        'kernel.hpp':'// header\n','unrelated.py':'raise RuntimeError("invisible")'}
    for name,body in files.items():
        p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
    result=source_closure(tmp_path,['analysis/lll/candidate.py','analysis/lll/kernel.cpp'])
    assert result==sorted('analysis/lll/'+name for name in files if name!='unrelated.py')


def test_dependency_closure_rejects_missing_and_escaping_declared_sources(tmp_path):
    from lll.studies.dependencies import source_closure
    with pytest.raises(ValueError):source_closure(tmp_path,['../outside.py'])
    with pytest.raises(ValueError):source_closure(tmp_path,['analysis/lll/missing.py'])
def test_cpp_sources_named_by_python_loaders_are_part_of_closure(tmp_path):
    from lll.studies.dependencies import source_closure
    base=tmp_path/'analysis/lll';base.mkdir(parents=True)
    (base/'loader.py').write_text("from pathlib import Path\na=Path(__file__).with_suffix('.cpp')\nb=Path(__file__).with_name('helper.cpp')\n")
    (base/'loader.cpp').write_text('#include "detail.hpp"\n')
    (base/'helper.cpp').write_text('int helper;\n');(base/'detail.hpp').write_text('int detail;\n')
    assert source_closure(tmp_path,['analysis/lll/loader.py'])==[
        'analysis/lll/detail.hpp','analysis/lll/helper.cpp','analysis/lll/loader.cpp','analysis/lll/loader.py']

