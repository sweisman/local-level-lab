# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound the project path before reconstructing a sealed turning problem."""

import pytest

from lll.generated_turning_problem import project_root


def test_generated_turning_builder_accepts_only_declared_study_directory(tmp_path):
    path = tmp_path/'data'/'generated-turning-known-optimum-v1'
    path.mkdir(parents=True)
    assert project_root(path, 'generated-turning-known-optimum-v1') == tmp_path
    with pytest.raises(ValueError, match='declared study directory'):
        project_root(path, 'another-study')
