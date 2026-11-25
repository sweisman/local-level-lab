# SPDX-License-Identifier: AGPL-3.0-or-later
import csv
import json
import math
from pathlib import Path

import numpy as np
import pytest

from lll import ilvis0_shape as shape, ilvis0_stretch_checks as checks
from lll.ilvis0_exploratory import load_kernel

ROOT = Path(__file__).resolve().parents[2]
# Shortest selected stretch; its first-pass fits stopped normally.
REPLAY = '705de394963c8be15c580512'


def test_wider_allowances_change_only_the_gyro_offset():
    base = shape.instrument_limits(1.)
    assert checks.limits(1.) == base
    wide = checks.limits(30.)
    assert {name for name in base if wide[name] != base[name]} == {
        'gyro_bias_x', 'gyro_bias_y', 'gyro_bias_z'}
    assert wide['gyro_bias_x'] == pytest.approx(math.radians(30)/3600)
    with pytest.raises(ValueError):
        checks.limits(20.)


def test_declared_fit_grids_are_exact():
    disc, wide = checks.disc_field_fits(), checks.allowance_fits()
    assert [checks.label(fit) for fit in disc] == [
        'flat_geographic_field-unsubtracted-1dph', 'flat_geographic_field-profiled_removal-1dph']
    assert len(wide) == 9 and len({checks.label(fit) for fit in wide}) == 9
    assert {fit['offset_dph'] for fit in wide} == {3., 10., 30.}
    assert {fit['case'] for fit in wide} == {'unsubtracted'}
    assert {fit['model'] for fit in wide} == {'sphere_rotating', 'flat_still', 'flat_geographic_field'}
    task = checks.tasks([dict(segment_id='a', native_packets=10)], disc)[0]
    assert task['identity'] == 'a' and task['fits'] == disc
    assert task['limits'] == dict(native_calls=402, packet_visits=4020, bound_calls=0, bound_steps=0)


def test_one_representative_is_the_longest_stretch_on_each_date():
    rows = [dict(segment_id='b', date='2015-10-12', duration_s=300.),
            dict(segment_id='a', date='2015-10-12', duration_s=300.),
            dict(segment_id='c', date='2015-10-12', duration_s=250.),
            dict(segment_id='d', date='2009-10-20', duration_s=240.)]
    assert [row['segment_id'] for row in checks.representatives(rows)] == ['d', 'a']


def test_every_native_sweep_is_reserved_before_it_runs(monkeypatch):
    order = []
    problem = object.__new__(checks.CountedProblem)
    problem.dt = np.zeros(7)
    problem.reserve = lambda **work: order.append(('reserve', work))
    monkeypatch.setattr(checks.MatchedTrainingProblem, 'prediction_tangent',
                        lambda self, point, model: order.append(('native', model)) or 'out')
    assert problem.prediction_tangent(None, 'flat_still') == 'out'
    assert order == [('reserve', dict(native_calls=1, packet_visits=7)), ('native', 'flat_still')]

    def refuse(**work):
        raise ValueError('task allowance exhausted; no operation performed')
    problem.reserve = refuse
    order.clear()
    with pytest.raises(ValueError):
        problem.prediction_tangent(None, 'flat_still')
    assert order == []


def test_disc_with_field_uses_the_disc_metric_and_field_kernel():
    problem = object.__new__(checks.CountedProblem)
    problem.matched_model = checks.DISC_WITH_FIELD
    assert problem.kernel_model(checks.DISC_WITH_FIELD) == 3
    assert problem.metric_model(checks.DISC_WITH_FIELD) == 'flat_still'
    with pytest.raises(ValueError):
        problem.kernel_model('flat_still')
    tangent = (ROOT/'analysis/lll/ilvis0_tangent.cpp').read_text()
    value = (ROOT/'analysis/lll/ilvis0_native.c').read_text()
    assert 'const bool disc=model==2 || model==3, field=model==0 || model==3;' in tangent
    assert 'const int disc=model==2 || model==3, field=model==0 || model==3;' in value


def test_replay_reproduces_published_costs(tmp_path):
    """One derivative sweep at each saved solution must return the published cost."""
    row = next(row for row in checks.stretches(ROOT) if row['segment_id'] == REPLAY)
    if not (ROOT/row['source_path']).is_file():
        pytest.skip('the original recording is required')
    task = checks.tasks([row], checks.disc_field_fits())[0]

    class Context:
        root = ROOT/'data'/'replay'

        def input_path(self, key):
            return ROOT/dict(selection=checks.SELECTION, contexts=checks.CONTEXTS)[key]

    values, times, gps, _ = checks.load_stretch(task, Context())
    kernel, _ = load_kernel(tmp_path)
    tangent, _ = shape.load_tangent(tmp_path)
    covariance = checks.receiver_covariance(times, gps)
    csv.field_size_limit(10**9)
    with (ROOT/'docs/ilvis0-current-findings-20261015/fit-analytics.csv').open(newline='') as stream:
        saved = [r for r in csv.DictReader(stream) if r['segment_id'] == REPLAY and r['parameters']]
    with (ROOT/checks.ANALYTICS).open(newline='') as stream:
        table = next(r for r in csv.DictReader(stream) if r['segment_id'] == REPLAY)
    for case, model in (('unsubtracted', 'flat_still'), ('profiled_removal', 'sphere_rotating')):
        published = table[f'bias1_{case}__{model}__cost']
        record = next(r for r in saved if r['case_id'] == 'bias1_'+case and r['model'] == model
                      and r['cost'] == published)
        parameters = json.loads(record['parameters'])
        charged = []
        problem, _ = checks.build_problem(values, times, gps, covariance,
            dict(model=model, case=case, offset_dph=1.), kernel=kernel, tangent=tangent,
            reserve=lambda **work: charged.append(work))
        point = np.array([2*parameters[name]-1 if name == 'earth_removal'
                          else parameters[name]/problem.bounds.limits[name]
                          for name in problem.bounds.active])
        residual, _, _ = problem.residual_tangent(np.clip(point, -1., 1.), model)
        assert float(residual@residual) == pytest.approx(float(published), rel=1e-6)
        assert charged == [dict(native_calls=1, packet_visits=row['native_packets'])]
