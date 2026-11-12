# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checks for the separately frozen observed selective-tangent comparison."""
import importlib.util
from pathlib import Path

import pytest


def test_hybrid_observed_recipe_preserves_wide_scientific_matrix():
    from lll.airquantumgrav_observed_hybrid import recipe, tasks
    from lll.airquantumgrav_observed_wide import recipe as wide_recipe

    wide = wide_recipe(maximum_wall_s=28800)
    hybrid = recipe(maximum_wall_s=28800)
    assert {k: v for k, v in hybrid.items() if k != 'version'} == {
        k: v for k, v in wide.items() if k != 'version'}
    assert hybrid['version'] != wide['version']
    layout = dict(native_packets=360028, training_prefix_packets=239867,
                  training_epochs=800, receiver_epochs=1200)
    cases = tasks(layout)
    assert len(cases) == 24
    assert sum(t['limits']['native_calls'] for t in cases) == 9648
    assert sum(t['limits']['packet_visits'] for t in cases) == 1862916172800
    assert recipe(maximum_wall_s=57600)['maximum_wall_s'] == 57600
    with pytest.raises(ValueError):
        recipe(maximum_wall_s=57601)


def test_hybrid_observed_requires_qualification_before_inputs(tmp_path):
    from lll.airquantumgrav_observed_hybrid import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None, maximum_wall_s=28800)
    assert not (tmp_path / 'data').exists()


def test_hybrid_observed_adapter_loads_directly_and_freezes_sources():
    path = Path('analysis/lll/airquantumgrav_observed_hybrid.py')
    spec = importlib.util.spec_from_file_location('_hybrid_observed_worker', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = set(module.qualification_sources(Path.cwd()))
    assert 'analysis/lll/ilvis0_hybrid_tangent.py' in names
    assert 'analysis/lll/airquantumgrav_observed_hybrid.py' in names
    assert 'docs/esa-observed-hybrid/PLAN.md' in names


def test_hybrid_observed_only_expected_parent_hashes_pass():
    from lll.airquantumgrav_observed_hybrid import verify_parent

    expected = ('f4d8609c51a918493d1b9b0a83c719201b49426fe2d98938451bfbfa7f4ee956',
                '2df075a347a694e908608306bd05ed384602fd53b9c2bc3739d4af74521689f8')
    verify_parent('long', *expected, six_passed=True)
    with pytest.raises(ValueError, match='parent'):
        verify_parent('long', '0' * 64, expected[1], six_passed=True)
    with pytest.raises(ValueError, match='parent'):
        verify_parent('long', *expected, six_passed=False)
