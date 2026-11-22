# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise the diagnostic candidate through native fitting and forecast."""

import numpy as np
import pytest

from lll.airquantumgrav_truth import truth


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent

    directory = tmp_path_factory.mktemp('matched-native')
    return load_kernel(directory)[0], load_tangent(directory)[0]


@pytest.mark.parametrize('model,geometry,field,base', [
    ('sphere_still', 'globe', 'zero', 'sphere_still'),
    ('sphere_rotating', 'globe', 'geographic', 'sphere_rotating'),
    ('flat_still', 'disc', 'zero', 'flat_still'),
    ('flat_geographic_field', 'disc', 'geographic', 'flat_still'),
])
@pytest.mark.parametrize('profile', [False, True])
def test_matched_fit_and_forecast_use_same_counted_physics(kernels, model, geometry, field,
                                                         base, profile):
    from lll.ilvis0_forecast import native_forecast
    from lll.ilvis0_matched_field import propagate_queries
    from lll.ilvis0_matched_training import matched_training_problem, matched_limits
    from lll.ilvis0_training_forecast import fit_training

    dt = np.full(240, .005)
    times = np.array([.2075, .3225, .4925, .7825, 1.0075])
    removal = .5 if profile else 0.
    midpoints = np.cumsum(dt) - .5 * dt
    samples = truth(base, midpoints, latitude_deg=-55., pattern='fast', removal=removal)
    if model == 'flat_geographic_field':
        latitude = samples['coordinates'][:, 0]
        background = 7.292115e-5 * np.column_stack(
            (np.cos(latitude), np.zeros_like(latitude), -np.sin(latitude)))
        local_to_body = samples['attitude_body_to_local'].swapaxes(1, 2)
        # The independent disc trajectory supplies the motion. Add the
        # prescribed field and physical Coriolis to its generated body channels.
        samples['angular_rate_rads'] += np.einsum('nij,nj->ni', local_to_body, background)
        force = 2. * np.cross(background, samples['velocity_local_mps'])
        samples['specific_force_mps2'] += np.einsum('nij,nj->ni', local_to_body, force)
    gps = truth(base, times, latitude_deg=-55., pattern='fast', removal=removal)['coordinates']
    theta = samples['angular_rate_rads'] * dt[:, None]
    dv = samples['specific_force_mps2'] * dt[:, None]
    kernel, tangent = kernels
    cut = 3
    prefix = np.searchsorted(np.cumsum(dt), times[cut - 1] + .15) + 1
    problem = matched_training_problem(
        times[:cut], gps[:cut], theta=theta[:prefix], dv=dv[:prefix], dt=dt[:prefix],
        covariance=np.tile([1e-6, 1e-6, 1.], cut) ** 2 * np.eye(3 * cut),
        model=model, limits=matched_limits(1.), profile=profile, clock='header_elapsed',
        maximum_interval_s=.0075, kernel=kernel, tangent_kernel=tangent)
    start = np.zeros(len(problem.bounds.active))
    expected = propagate_queries(
        problem.initial, theta, dv, dt, times, geometry=geometry, field=field,
        removed_fraction=removal, gravity_mps2=problem.gravity, disc_radius_m=problem.radius)
    prediction, jacobian, _ = problem.prediction_tangent(start, model)
    np.testing.assert_allclose(prediction, expected[:cut], rtol=0, atol=1e-10)
    np.testing.assert_allclose(problem.predict(start, model), prediction, rtol=0, atol=1e-10)
    assert np.isfinite(jacobian).all()
    if model == 'flat_geographic_field':
        # Differentiate the separate scalar kernel, with all nuisance
        # directions present, away from a recorded packet boundary.
        direction = np.linspace(-.7, .9, len(start))
        step = 1e-4
        centered = (problem.predict(start + step * direction, model) -
                    problem.predict(start - step * direction, model)) / (2. * step)
        coordinate_scale = np.array([6371000., 6371000., 1.])
        np.testing.assert_allclose(centered * coordinate_scale,
                                   (jacobian @ direction).reshape(-1, 3) * coordinate_scale,
                                   rtol=3e-7, atol=2e-4)
    calls = []
    fit = fit_training(problem, model, start=start, maximum_evaluations=12,
                       reserve=lambda **charge: calls.append(charge))
    assert len(calls) == fit['evaluations'] > 0
    assert all(entry == dict(native_calls=1, packet_visits=prefix * cut) for entry in calls)
    point = np.array(fit['normalized_parameters'])
    forecast = native_forecast(problem, point, model, theta=theta, dv=dv, dt=dt,
                               times=times, maximum_interval_s=.0075,
                               reserve=lambda **charge: calls.append(charge))
    assert calls[-1] == dict(native_calls=1, packet_visits=len(dt)*len(times))
    assert forecast['prediction_receiver_positions_used'] is False
    assert forecast['prediction_epochs'] == 2
    np.testing.assert_array_equal(forecast['coordinates'][:cut],
                                  problem.prediction_tangent(point, model)[0])
    if model == 'flat_geographic_field':
        with pytest.raises(ValueError, match='differs from matched training model'):
            native_forecast(problem, point, 'flat_still', theta=theta, dv=dv, dt=dt,
                            times=times, maximum_interval_s=.0075,
                            reserve=lambda **charge: pytest.fail('mismatched candidate was charged'))
