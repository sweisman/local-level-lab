"""Cheap contract checks for the generated paired-fit study."""
import json
from types import SimpleNamespace

import pytest

from lll.ilvis0_hybrid_fit_study import evaluate, inspect, pair, prepare, recipe, tasks


def test_study_freezes_six_cases_and_two_finite_fit_allowances():
    r = recipe()
    cases = tasks(r)
    assert len(cases) == 6
    assert {row['payload']['model'] for row in cases} == {
        'sphere_rotating', 'sphere_still', 'flat_still'}
    assert {row['payload']['profile'] for row in cases} == {False, True}
    assert r['duration_s'] == 120.
    assert r['maximum_evaluations'] == 200
    assert r['workers'] * r['threads'] == 4
    assert all(row['limits']['native_calls'] == 402 for row in cases)


def test_pair_uses_two_factories_and_preserves_matched_input_and_truth():
    r = recipe()
    case = tasks(r)[0]['payload']
    saved = {}
    factories = []
    def calculate(spec, settings, *, kernel_factory, reserve,
                  reserve_construction, save, check_continue):
        assert spec == case and settings == r
        _, _, meta = kernel_factory(3500.)
        factories.append(meta['variant'])
        save('input-binding.json', {'full_array_sha256': {'theta': 'a' * 64}})
        save('scoring-observations.json', {'times': [1., 2.]})
        save('scores.json', {'errors_neu_m': [[0., 0., 0.], [0.1, 0., 0.]]})
        reserve(native_calls=1, packet_visits=10)
        reserve_construction(constructed_intervals=1)
        check_continue()
        return dict(spec, passed=True, converged=True,
                    all_columns_retained=True, training_cost=0.2)
    result = pair(case, r, calculate=calculate,
                  factories={name: (lambda anchor, label=name: (None, None, {'variant': label}))
                             for name in ('wide', 'hybrid')},
                  reserve=lambda **work: None,
                  reserve_construction=lambda **work: None,
                  save=lambda name, value: saved.update({name: value}),
                  check_continue=lambda: None)
    assert factories == ['wide', 'hybrid']
    assert result['comparison']['passed']
    assert saved['wide-input-binding.json'] == saved['hybrid-input-binding.json']
    assert saved['comparison.json'] == result['comparison']


def test_worker_rejects_changed_recipe_before_creating_artifacts(tmp_path):
    row = tasks()[0]
    wrong = tmp_path / 'wrong.json'
    wrong.write_text(json.dumps(dict(recipe(), duration_s=3.)))
    context = SimpleNamespace(
        manifest={'scope': 'changed'},
        input_path=lambda key=None: wrong,
        root=tmp_path,
        directory=tmp_path,
        shard=0)
    with pytest.raises(ValueError, match='unchanged source-qualified'):
        evaluate(row, context)
    assert set(tmp_path.iterdir()) == {wrong}


def test_report_rejects_unclosed_study(tmp_path):
    with pytest.raises((FileNotFoundError, ValueError)):
        inspect(tmp_path, 'data/never-started')


def test_preparation_requires_source_bound_tests_before_writing(tmp_path):
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None)
    assert list(tmp_path.iterdir()) == []


def test_short_real_paired_fits_share_inputs_and_forecast(tmp_path):
    """Exercise the unchanged fitting path without spending study allowance."""
    import hashlib
    from pathlib import Path

    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_hybrid_tangent import load as hybrid_load
    from lll.ilvis0_wide_tangent import load as wide_load
    from lll.ilvis0_wide_training import SOURCES, bind

    source = Path(__file__).resolve().parents[1] / 'lll'
    hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
              for name in SOURCES}
    _, calculate, _ = bind(expected_sources=hashes)
    r = dict(recipe(), duration_s=20., queries=19, maximum_evaluations=8)
    cpp = hashlib.sha256((source / 'ilvis0_tangent.cpp').read_bytes()).hexdigest()
    loader = hashlib.sha256((source / 'ilvis0_wide_tangent.py').read_bytes()).hexdigest()

    def factory(variant):
        def build(anchor):
            value, vm = load_kernel(tmp_path, gravity_anchor_height_m=anchor)
            if variant == 'wide':
                tangent, tm = wide_load(tmp_path, gravity_anchor_height_m=anchor,
                                        expected_source_sha256=cpp)
            else:
                tangent, tm = hybrid_load(tmp_path, gravity_anchor_height_m=anchor,
                                          expected_source_sha256=cpp,
                                          expected_loader_sha256=loader)
            return value, tangent, dict(value=vm, tangent=tm, variant=variant)
        return build

    saved = {}
    result = pair(tasks(r)[0]['payload'], r, calculate=calculate,
                  factories={name: factory(name) for name in ('wide', 'hybrid')},
                  reserve=lambda **work: None,
                  reserve_construction=lambda **work: None,
                  save=lambda name, value: saved.update({name: value}),
                  check_continue=lambda: None)
    assert result['comparison']['forecast_epochs'] == 19
    assert result['comparison']['maximum_prediction_difference_m'] < 1e-5
    assert result['reference']['evaluations'] <= 8
    assert result['candidate']['evaluations'] <= 8
    assert saved['wide-input-binding.json'] == saved['hybrid-input-binding.json']
