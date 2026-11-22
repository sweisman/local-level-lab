# SPDX-License-Identifier: AGPL-3.0-or-later
"""Keep the opt-in matched candidate bound through the wider arithmetic path."""

import numpy as np
import pytest


def test_wide_adapter_preserves_matched_disc_model_and_receiver_prefix(tmp_path):
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_forecast import native_forecast
    from lll.ilvis0_matched_training import DISC_WITH_FIELD, matched_limits, matched_training_problem
    from lll.ilvis0_matched_truth import matched_truth
    from lll.ilvis0_precision_value import calculate, load as load_scalar
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_wide_tangent import load, problem

    dt = np.full(240, .005)
    times = np.array([.2075, .3225, .4925, .7825, 1.0075])
    settings = dict(latitude_deg=-55., route='turning', removal=.5)
    samples = matched_truth(DISC_WITH_FIELD, (np.arange(len(dt)) + .5) * .005, **settings)
    gps = matched_truth(DISC_WITH_FIELD, times[:3], **settings)['coordinates']
    theta = samples['angular_rate_rads'] * dt[:, None]
    dv = samples['specific_force_mps2'] * dt[:, None]
    kernel, _ = load_kernel(tmp_path)
    tangent, _ = load_tangent(tmp_path)
    prefix = 130
    base = matched_training_problem(
        times[:3], gps, theta=theta[:prefix], dv=dv[:prefix], dt=dt[:prefix],
        covariance=np.tile([1e-6, 1e-6, 1.], 3) ** 2 * np.eye(9),
        model=DISC_WITH_FIELD, limits=matched_limits(3.), profile=True,
        clock='header_elapsed', maximum_interval_s=.0075, kernel=kernel,
        tangent_kernel=tangent)
    wide_kernel, metadata = load(tmp_path)
    wide = problem(base, kernel=wide_kernel)
    start = np.zeros(len(wide.bounds.active))
    residual, jac, edges = wide.residual_tangent(start, DISC_WITH_FIELD)
    old, old_jac, old_edges = base.residual_tangent(start, DISC_WITH_FIELD)
    assert metadata['internal_mantissa_bits'] > 53
    np.testing.assert_allclose(residual, old, rtol=0., atol=3e-8)
    np.testing.assert_allclose(jac, old_jac, rtol=5e-9, atol=3e-8)
    assert edges == old_edges
    scalar_kernel, _ = load_scalar(tmp_path, precision='long_double')
    scalar = calculate(base, start, DISC_WITH_FIELD, kernel=scalar_kernel, longitude='stable')
    np.testing.assert_array_equal(scalar['residual'], residual)
    np.testing.assert_array_equal(scalar['coordinates'], wide.predict(start, DISC_WITH_FIELD))
    assert scalar['boundaries'] == edges
    with pytest.raises(ValueError, match='differs from matched training model'):
        calculate(base, start, 'flat_still', kernel=scalar_kernel, longitude='stable')
    charges = []
    forecast = native_forecast(
        wide, start, DISC_WITH_FIELD, theta=theta, dv=dv, dt=dt, times=times,
        maximum_interval_s=.0075, retain_training_difference=True,
        reserve=lambda **charge: charges.append(charge))
    assert charges == [dict(native_calls=1, packet_visits=len(dt) * len(times))]
    np.testing.assert_array_equal(forecast['coordinates'][:3], wide.predict(start, DISC_WITH_FIELD))
    with pytest.raises(ValueError, match='differs from matched training model'):
        wide.residual_tangent(start, 'flat_still')


def test_fixed_saved_probe_reconstruction_rejects_changed_step():
    from lll.ilvis0_matched_precision import correction_point

    fit = dict(converged=False, normalized_parameters=[0.], active_parameters=['offset'],
               residual_sum_squares=1.,
               local_linearization=dict(normalized_parameters=[0.], active_parameters=['offset'],
                                        residual=[1.], jacobian=[[2.]]),
               stability_probe=dict(reason='fresh_position_probe_not_stable',
                                    normalized_parameter_step=.5, predicted_cost_change=1.))
    endpoint, probe = correction_point(fit)
    np.testing.assert_array_equal(endpoint, [0.])
    np.testing.assert_array_equal(probe, [-.5])
    fit['stability_probe']['normalized_parameter_step'] = .6
    with pytest.raises(ValueError, match='differs from the saved'):
        correction_point(fit)


def test_matched_precision_limits_are_exact():
    from lll.ilvis0_matched_precision import task

    sample = task('sphere_rotating-flat_still-cap1-removal0')
    assert sample['limits'] == dict(native_calls=4, packet_visits=151816, bound_calls=0, bound_steps=0)
    with pytest.raises(ValueError, match='alternative'):
        task('sphere_rotating-sphere_rotating-cap1-removal0')
