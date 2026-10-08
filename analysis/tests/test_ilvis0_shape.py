# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import numpy as np
import pytest
from lll import ilvis0_shape as shape, ilvis0_exploratory as explore
from lll import ilvis0_estimator as estimator, ilvis0_excitation_controls as controls
from lll import ilvis0_gps_sensitivity as sensitivity


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    path = tmp_path_factory.mktemp('shape-kernels')
    return explore.load_kernel(path)[0], shape.load_tangent(path)[0]


def problem(kernels, *, profile=True, all_parameters=True):
    base, _, _ = controls.fixture(2., 'brief_pitch', sensitivity.assumptions()[0])
    limits = shape.instrument_limits(1.) if all_parameters else dict(position_x=5., velocity_x=.5)
    return shape.TangentProblem(base.theta, base.dv, base.dt, base.gps_times, base.gps,
        base.cholesky@base.cholesky.T, base.initial, estimator.Bounds(limits),
        kernel=kernels[0], tangent_kernel=kernels[1], fit_earth_removal=profile,
        clock_hypothesis='header_elapsed', processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.501, gravity_mps2=9.81, disc_radius_m=6371000.)


@pytest.mark.parametrize('model', explore.MODELS)
@pytest.mark.parametrize('profile', [False, True])
def test_tangent_values_and_all_derivatives(kernels, model, profile):
    p = problem(kernels, profile=profile)
    u = np.full(len(p.bounds.active), .03)
    if profile: u[-1] = -.3
    out, jac, boundaries = p.prediction_tangent(u, model)
    metric = np.array([6371000., 6371000., 1.])
    assert np.max(abs((out-p.predict(u, model))*metric)) < 3e-7
    assert boundaries == 0
    for i in range(len(u)):
        h = 1e-3
        plus = u.copy(); minus = u.copy(); plus[i] += h; minus[i] -= h
        fd = (p.predict(plus, model)-p.predict(minus, model)).reshape(-1)/(2*h)
        scale = np.tile(metric, len(p.gps))
        assert np.allclose(jac[:, i]*scale, fd*scale, atol=8e-5, rtol=3e-5), p.bounds.active[i]


def test_bias_cases_are_constant_offset_hypotheses():
    assert shape.instrument_limits(.1)['gyro_bias_x'] == math.radians(.1)/3600
    assert shape.instrument_limits(1.)['gyro_bias_z'] == math.radians(1.)/3600
    assert shape.instrument_limits(.1)['accel_bias_x'] == explore.LIMITS['accel_bias_x']
    with pytest.raises(ValueError): shape.instrument_limits(20.)


def case(name='a', costs=(3., 5., 10.), converged=True):
    return dict(case_id=name, fits=[dict(model=m, residual_sum_squares=c, converged=converged,
        exact_projected_gradient_relative=1e-6) for m,c in zip(explore.MODELS,costs)])


def test_rotation_requires_consistent_globe_shape_first():
    result = shape.hierarchical_profile([case(), case('b', (4., 6., 12.))])
    assert result['conditional_shape_preference'] == 'globe'
    assert len(result['rotation_diagnostics']) == 2
    assert result['scientific_shape_decision'] == result['scientific_rotation_decision'] == 'abstain'
    for cases, expected in [([case(costs=(10.,12.,3.))], 'flat'),
            ([case(), case('b', (10.,12.,3.))], 'ambiguous'),
            ([case(costs=(3.,5.,3.))], 'ambiguous'),
            ([case(converged=False)], 'unresolved')]:
        result = shape.hierarchical_profile(cases)
        assert result['conditional_shape_preference'] == expected
        assert result['rotation_diagnostics'] is None
    with pytest.raises(ValueError): shape.hierarchical_profile([case(),case()])


def test_solver_recovers_position_velocity_without_finite_difference_starts(kernels):
    p = problem(kernels, profile=False, all_parameters=False)
    truth = np.array([.15, -.2])
    p.gps = p.predict(truth, 'flat_still')
    result = shape.fit_shape_candidate(p, 'flat_still', maximum_evaluations=20)
    assert result['converged']
    assert np.allclose(result['normalized_parameters'], truth, atol=2e-5)
    assert result['evaluations'] <= 18
    assert not result['constant_bias_is_measured_drift']
    assert result['scientific_decision'] == 'abstain'


def test_evaluation_limit_and_independent_gate_are_preserved(kernels, tmp_path):
    p = problem(kernels)
    result = shape.fit_shape_candidate(p, 'flat_still', maximum_evaluations=4)
    assert result['evaluations'] <= 2
    assert not result['converged']
    with pytest.raises(ValueError, match='prerequisites'):
        estimator.fit_observed(p, 'sphere_rotating', evidence={},
            ledger=estimator.StartLedger(tmp_path/'starts.jsonl','a'*64), task='test', maximum_evaluations=200)
    assert not (tmp_path/'starts.jsonl').exists()
