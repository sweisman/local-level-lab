"""Finite source-bound whole-fit timing comparison."""

from types import SimpleNamespace

import pytest


def test_timed_recipe_keeps_six_long_cases_and_finite_allowances():
    from lll.ilvis0_hybrid_timed_fit_study import recipe, tasks

    r = recipe()
    assert r['duration_s'] == 1200.
    assert r['queries'] == 1199
    assert r['workers'] * r['threads'] == 4
    assert r['maximum_wall_s'] == 21600.
    assert len(tasks(r)) == 6
    assert all(row['limits']['native_calls'] == 402 for row in tasks(r))


def test_timed_adapter_loads_from_a_frozen_file_without_package_context():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / 'lll/ilvis0_hybrid_timed_fit_study.py'
    spec = importlib.util.spec_from_file_location('frozen_timed_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.recipe()['duration_s'] == 1200.


def test_timed_preparation_requires_qualified_sources_before_writing(tmp_path):
    from lll.ilvis0_hybrid_timed_fit_study import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None)
    assert list(tmp_path.iterdir()) == []


def test_timed_worker_rejects_changed_recipe_before_construction(tmp_path):
    import json
    from lll.ilvis0_hybrid_fit_study import recipe as short_recipe
    from lll.ilvis0_hybrid_timed_fit_study import SCOPE, evaluate, tasks

    path = tmp_path / 'recipe.json'
    path.write_text(json.dumps(short_recipe()))
    context = SimpleNamespace(
        manifest={'scope': SCOPE}, input_path=lambda key=None: path,
        root=tmp_path, directory=tmp_path, shard=0)
    with pytest.raises(ValueError, match='unchanged source-qualified'):
        evaluate(tasks()[0], context)
    assert set(tmp_path.iterdir()) == {path}


def test_timed_report_rejects_unclosed_study(tmp_path):
    from lll.ilvis0_hybrid_timed_fit_study import inspect

    with pytest.raises((FileNotFoundError, ValueError)):
        inspect(tmp_path, 'data/not-started')


def test_operational_speed_gate_uses_fit_cpu_not_total_cpu():
    from lll.ilvis0_hybrid_timed_fit_study import speed_summary

    rows = [dict(wide=dict(fit_cpu_ns=130, complete_cpu_ns=140,
                           fit_wall_ns=150, complete_wall_ns=160),
                 hybrid=dict(fit_cpu_ns=100, complete_cpu_ns=200,
                             fit_wall_ns=110, complete_wall_ns=220))
            for _ in range(6)]
    report = speed_summary(rows)
    assert report['median_fit_cpu_ratio'] == 1.3
    assert report['minimum_fit_cpu_ratio'] == 1.3
    assert report['worthwhile_substitution'] is True
    rows[0]['wide']['fit_cpu_ns'] = 90
    assert speed_summary(rows)['worthwhile_substitution'] is False
