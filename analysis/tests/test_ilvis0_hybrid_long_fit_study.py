"""Finite long-record comparison of the two complete fitting paths."""
from types import SimpleNamespace

import pytest


def test_long_recipe_keeps_six_matched_cases_and_finite_allowances():
    from lll.ilvis0_hybrid_long_fit_study import recipe, tasks

    r = recipe()
    cases = tasks(r)
    assert r['duration_s'] == 1200.
    assert r['queries'] == 1199
    assert r['maximum_wall_s'] == 21600.
    assert r['maximum_evaluations'] == 200
    assert r['workers'] * r['threads'] == 4
    assert len(cases) == 6
    assert {row['payload']['model'] for row in cases} == {
        'sphere_rotating', 'sphere_still', 'flat_still'}
    assert {row['payload']['profile'] for row in cases} == {False, True}
    assert all(row['limits'] == dict(native_calls=402,
                                     packet_visits=77_425_058_000,
                                     bound_calls=0, bound_steps=0)
               for row in cases)


def test_long_worker_adapter_loads_from_frozen_file_without_package_context():
    import importlib.util
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / 'lll/ilvis0_hybrid_long_fit_study.py'
    spec = importlib.util.spec_from_file_location('frozen_long_adapter', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.recipe()['duration_s'] == 1200.


def test_long_preparation_requires_source_bound_tests_before_writing(tmp_path):
    from lll.ilvis0_hybrid_long_fit_study import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None)
    assert list(tmp_path.iterdir()) == []


def test_long_worker_rejects_short_recipe_before_construction(tmp_path):
    from lll.ilvis0_hybrid_fit_study import recipe as short_recipe
    from lll.ilvis0_hybrid_long_fit_study import SCOPE, evaluate, tasks

    path = tmp_path / 'recipe.json'
    import json
    path.write_text(json.dumps(short_recipe()))
    context = SimpleNamespace(
        manifest={'scope': SCOPE},
        input_path=lambda key=None: path,
        root=tmp_path,
        directory=tmp_path,
        shard=0)
    with pytest.raises(ValueError, match='unchanged source-qualified'):
        evaluate(tasks()[0], context)
    assert set(tmp_path.iterdir()) == {path}


def test_long_worker_rejects_changed_parent_before_construction(tmp_path):
    import json
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_hybrid_long_fit_study import SCOPE, evaluate, recipe, tasks

    values = {
        'recipe': recipe(),
        'qualification-environment': environment(),
        'qualification-request': {'sources': {}},
        'qualified-parent': {'changed': True},
    }
    paths = {}
    for name, value in values.items():
        path = tmp_path / (name + '.json')
        path.write_text(json.dumps(value))
        paths[name] = path
    context = SimpleNamespace(
        manifest={'scope': SCOPE, 'sources': {}},
        input_path=lambda key: paths[key],
        root=tmp_path,
        directory=tmp_path,
        shard=0)
    with pytest.raises(ValueError, match='qualified parent differs'):
        evaluate(tasks()[0], context)
    assert set(tmp_path.iterdir()) == set(paths.values())


def test_long_report_rejects_unclosed_study(tmp_path):
    from lll.ilvis0_hybrid_long_fit_study import inspect

    with pytest.raises((FileNotFoundError, ValueError)):
        inspect(tmp_path, 'data/not-started')
