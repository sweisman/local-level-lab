# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import importlib.util
from pathlib import Path

from lll.airquantumgrav_same_point_study import prepare, tasks, validate_points


def test_same_point_tasks_are_exact_failed_pairs_with_finite_limits():
    rows = tasks()
    assert len(rows) == 3
    assert {row['identity'] for row in rows} == {
        'flat_still-0-reported-short-v1-1',
        'flat_still-0-reported-persistent-v1-0',
        'flat_still-1-reported-short-v1-0'}
    assert all(row['limits']['native_calls'] == 4 for row in rows)
    assert all(row['limits']['packet_visits'] == 767574400 for row in rows)
    assert all(row['limits']['bound_calls'] == 0 for row in rows)


def test_same_point_input_rejects_changed_column_order():
    row = tasks()[0]
    points = {name: dict(active_parameters=['a', 'b'],
                         normalized_parameters=[0., 0.])
              for name in ('wide', 'hybrid')}
    assert validate_points(row, points, ['a', 'b']) is None
    points['hybrid']['active_parameters'] = ['b', 'a']
    with pytest.raises(ValueError, match='active'):
        validate_points(row, points, ['a', 'b'])


def test_same_point_preparation_requires_bound_qualification(tmp_path):
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None)


def test_same_point_adapter_loads_directly_from_frozen_file():
    path = Path('analysis/lll/airquantumgrav_same_point_study.py')
    spec = importlib.util.spec_from_file_location('frozen_same_point_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(AttributeError, match='input_path'):
        module.evaluate({}, None)
