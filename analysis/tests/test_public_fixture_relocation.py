# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import pytest
from public_fixtures import public_read_path


@pytest.mark.parametrize('nested',[False,True])
def test_already_relocated_paths_are_not_rebased_twice(nested):
    recorded=Path('/fixture/repository')
    root=recorded/'data/worktree' if nested else Path('/fixture/other-checkout')
    remap=public_read_path(root,recorded_root=recorded)
    expected=root/'docs/ilvis0-example/manifest.json'
    assert remap(root/'data/ilvis0-example/manifest.json')==expected
    assert remap(recorded/'data/ilvis0-example/manifest.json')==expected


def test_current_test_scratch_is_never_mistaken_for_a_frozen_study():
    recorded=Path('/fixture/repository');root=recorded/'data/worktree'
    scratch=recorded/'data/ilvis0-source-point-development/scratch/pytest-1'
    remap=public_read_path(root,recorded_root=recorded,temporary_root=scratch)
    path=scratch/'test_repeat/2.gz'
    assert remap(path)==path
    assert remap(recorded/'data/ilvis0-example/manifest.json')==root/'docs/ilvis0-example/manifest.json'
