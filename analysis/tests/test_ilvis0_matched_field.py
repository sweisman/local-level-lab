# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the matched field against independently generated coordinate histories."""

import math

import numpy as np
import pytest

from lll.airquantumgrav_truth import truth


@pytest.mark.parametrize('geometry,model', [
    ('globe', 'sphere_still'), ('disc', 'flat_still'),
])
@pytest.mark.parametrize('removed_fraction', [0., .35])
def test_field_changes_force_and_logged_rotation_without_changing_transport(
        geometry, model, removed_fraction):
    from lll.ilvis0_matched_field import evaluate

    times = np.array([17., 61., 108.])
    track = truth(model, times, latitude_deg=-60., pattern='fast', removal=0.)
    inclination_k, longitude_k, height_k = (2. * math.pi / p for p in (300., 180., 240.))
    second_derivatives = np.column_stack((
        -8. / 6378137. * inclination_k * np.sin(inclination_k * times),
        -75. / (6378137. * .5) * .1 * longitude_k * np.sin(longitude_k * times),
        -10. * height_k ** 2 * np.sin(height_k * times),
    ))
    nearby_times = times[:, None] + np.array([-.01, .01])
    nearby = truth(model, nearby_times.ravel(), latitude_deg=-60.,
                   pattern='fast', removal=0.)
    local_axes = nearby['body_axes_world'] @ np.swapaxes(
        nearby['attitude_body_to_local'], 1, 2)
    before, after = local_axes[::2], local_axes[1::2]
    rate_matrix = ((before + after) / 2.).swapaxes(1, 2) @ ((after - before) / .02)
    expected_transport = .5 * np.column_stack((
        rate_matrix[:, 2, 1] - rate_matrix[:, 1, 2],
        rate_matrix[:, 0, 2] - rate_matrix[:, 2, 0],
        rate_matrix[:, 1, 0] - rate_matrix[:, 0, 1],
    ))

    for index, (position, rate) in enumerate(zip(
            track['coordinates'], track['coordinate_rates'], strict=True)):
        kwargs = dict(geometry=geometry, removed_fraction=removed_fraction,
                      gravity_mps2=9.81, disc_radius_m=6371000.)
        derivatives = (position, rate, second_derivatives[index])
        zero = evaluate(*derivatives, field='zero', **kwargs)
        matched = evaluate(*derivatives, field='geographic', **kwargs)
        body = track['attitude_body_to_local'][index]
        base_force = body @ track['specific_force_mps2'][index]
        latitude = position[0]
        field = 7.292115e-5 * np.array([math.cos(latitude), 0., -math.sin(latitude)])
        coriolis = 2. * np.cross(field, track['velocity_local_mps'][index])
        np.testing.assert_allclose(zero['specific_force_ned_mps2'], base_force,
                                   rtol=0., atol=1e-11)
        np.testing.assert_allclose(matched['specific_force_ned_mps2'],
                                   base_force + coriolis, rtol=0., atol=1e-11)
        np.testing.assert_array_equal(matched['transport_ned_rads'],
                                      zero['transport_ned_rads'])
        np.testing.assert_allclose(zero['transport_ned_rads'], expected_transport[index],
                                   rtol=0., atol=2e-13)
        np.testing.assert_allclose(matched['logged_frame_ned_rads'],
                                   zero['transport_ned_rads'] + (1.-removed_fraction)*field,
                                   rtol=0., atol=1e-15)
        np.testing.assert_allclose(zero['logged_frame_ned_rads'],
                                   zero['transport_ned_rads'] - removed_fraction*field,
                                   rtol=0., atol=1e-15)


def test_constant_body_axis_signal_can_be_absorbed_only_inside_offset_box():
    from lll.ilvis0_matched_field import profile_constant_gyro_offset

    radians_per_second = math.pi / (180. * 3600.)
    observed = np.tile([7., 0., -9.], (4, 1)) * radians_per_second
    expected = np.zeros_like(observed)
    tight = profile_constant_gyro_offset(observed, expected, limit_dph=1.)
    wide = profile_constant_gyro_offset(observed, expected, limit_dph=20.)
    np.testing.assert_allclose(tight['offset_dph'], [1., 0., -1.])
    assert wide['weighted_mean_square_rads2'] == 0.
    assert tight['weighted_mean_square_rads2'] > 0.
    observed[2:, 0] *= -1.
    changing = profile_constant_gyro_offset(observed, expected, limit_dph=20.)
    np.testing.assert_allclose(changing['offset_dph'], [0., 0., -9.], atol=1e-14)
    assert changing['weighted_mean_square_rads2'] == pytest.approx(
        (7. * radians_per_second) ** 2, rel=1e-14, abs=0.)


def test_weighted_offset_shares_one_calibration_across_the_full_history():
    from lll.ilvis0_matched_field import profile_constant_gyro_offset

    conversion = math.pi / (180. * 3600.)
    signal = np.array([[2., 0., 0.], [6., 0., 0.]]) * conversion
    result = profile_constant_gyro_offset(signal, np.zeros_like(signal),
                                          limit_dph=10., weights=[3., 1.])
    np.testing.assert_allclose(result['offset_dph'], [3., 0., 0.])
    assert result['weighted_mean_square_rads2'] == pytest.approx(
        3. * conversion ** 2, rel=1e-14, abs=0.)


def test_gyro_free_attitude_witness_retains_the_same_error_for_different_twists():
    from lll.ilvis0_matched_field import gyro_free_attitude_witness
    from lll.ilvis0_scalar_nonlinear import Problem

    body = np.array([[0., 2., 0.], [0., 0., 3.], [0., -4., 0.]])
    required = np.array([[0., 0., -1.], [0., 0., -4.], [0., 0., -4.]])
    limits = [.2, .2, .2, .1, .1, .1, .1]
    calibration = np.array([0., .5, 0., 0., 0., 0., 0.])
    problem = Problem(body, required, limits)
    aligned = gyro_free_attitude_witness(problem, calibration, [0., 0., 0.])
    twisted = gyro_free_attitude_witness(problem, calibration, [.3, -1., .8])
    assert not np.allclose(aligned['body_to_ned'], twisted['body_to_ned'])
    for witness in (aligned, twisted):
        np.testing.assert_allclose(np.linalg.det(witness['body_to_ned']), 1., atol=1e-14)
        np.testing.assert_allclose(np.linalg.norm(witness['force_error_ned_mps2'], axis=1),
                                   np.abs(problem.residual(calibration)), atol=1e-14)
        assert witness['attitude_identified'] is False


def test_force_uncertainty_is_invariant_under_equivalent_receiver_coordinates():
    from lll.ilvis0_force_magnitude_covariance import propagate

    # The receiver error is shared between two fixes. Rescale and mix its
    # latitude/longitude coordinates with an invertible linear chart.
    jet = np.array([-.9, .3, 2500., -2e-5, 1e-5, 0., 2e-7, 3e-7, 0.])
    scales = np.array([1e-7, 1e-7, .4])
    correlation = np.array([[1., .2, .1], [.2, 1., -.3], [.1, -.3, 1.]])
    covariance = np.kron([[1., .5], [.5, 1.]], correlation * np.outer(scales, scales))
    weights = np.vstack([
        .5 * np.hstack([np.eye(3), np.eye(3)]),
        np.hstack([-np.eye(3), np.eye(3)]),
        np.zeros((3, 6)),
    ])[None, :, :]
    chart = np.kron(np.eye(2), [[2., .5, 0.], [-.3, 1.5, 0.], [0., 0., 1.7]])
    constants = dict(model='sphere_rotating', background_rate_rads=7.292115e-5,
                     gravity_mps2=9.81, disc_radius_m=6371000.)
    direct = propagate(jet[None, :], weights, covariance, **constants)
    transformed = propagate(jet[None, :], weights @ np.linalg.inv(chart),
                            chart @ covariance @ chart.T, **constants)
    np.testing.assert_allclose(transformed['conditional_covariance_mps4'],
                               direct['conditional_covariance_mps4'], rtol=1e-12, atol=0.)


@pytest.mark.parametrize('geometry,field,legacy', [
    ('globe', 'zero', 'sphere_still'),
    ('globe', 'geographic', 'sphere_rotating'),
    ('disc', 'zero', 'flat_still'),
])
@pytest.mark.parametrize('removal', [0., .35])
def test_matched_forward_step_matches_existing_candidates(geometry, field, legacy, removal):
    from lll.ilvis0_exploratory import reference_step
    from lll.ilvis0_matched_field import propagate_step

    state = dict(latitude_rad=-1., longitude_rad=.4, height_m=2500.,
                 attitude_body_to_ned=np.eye(3), velocity_ned_mps=np.array([25., 190., -1.]))
    theta = np.array([.004, .002, -.009])
    dv = np.array([.003, -.005, -.051])
    expected = reference_step(state, theta, dv, .005, legacy,
                              np.array([0., 0., 9.81]), 6371000., removal)
    found = propagate_step(state, theta, dv, .005, geometry=geometry, field=field,
                           removed_fraction=removal, gravity_mps2=9.81, disc_radius_m=6371000.)
    for key in expected:
        np.testing.assert_allclose(found[key], expected[key], rtol=0., atol=3e-14)


@pytest.mark.parametrize('removal', [0., .35, 1.])
def test_disc_with_field_reconstructs_stationary_state_at_known_latitude(removal):
    from lll.ilvis0_matched_field import propagate_step

    latitude = math.radians(-60.)
    state = dict(latitude_rad=latitude, longitude_rad=.4, height_m=2500.,
                 attitude_body_to_ned=np.eye(3), velocity_ned_mps=np.zeros(3))
    dt = .005
    known_field = 7.292115e-5 * np.array([.5, 0., math.sqrt(3.) / 2.])
    found = propagate_step(state, (1.-removal)*known_field*dt,
                           np.array([0., 0., -9.81*dt]), dt, geometry='disc',
                           field='geographic', removed_fraction=removal,
                           gravity_mps2=9.81, disc_radius_m=6371000.)
    for key in state:
        np.testing.assert_allclose(found[key], state[key], rtol=0., atol=1e-14)


@pytest.mark.parametrize('geometry,field,model', [
    ('disc', 'zero', 'flat_still'),
    ('globe', 'geographic', 'sphere_rotating'),
])
def test_matched_queries_reconstruct_a_generated_path_at_fractional_packets(
        geometry, field, model):
    from lll.ilvis0_matched_field import propagate_queries

    dt = np.full(200, .005)
    queries = np.array([0., .001, .3275, .837, .999])
    generator = dict(latitude_deg=55., pattern='fast', removal=.35)
    samples = truth(model, np.cumsum(dt)-dt/2., **generator)
    expected = truth(model, queries, **generator)
    initial = dict(zip(('latitude_rad', 'longitude_rad', 'height_m'),
                       expected['coordinates'][0], strict=True))
    initial.update(velocity_ned_mps=expected['velocity_local_mps'][0],
                   attitude_body_to_ned=expected['attitude_body_to_local'][0])
    predicted = propagate_queries(
        initial, samples['angular_rate_rads']*dt[:, None],
        samples['specific_force_mps2']*dt[:, None], dt, queries,
        geometry=geometry, field=field, removed_fraction=.35,
        gravity_mps2=9.81, disc_radius_m=6371000.)
    differences = (predicted - expected['coordinates']) * [6371000., 6371000., 1.]
    np.testing.assert_allclose(differences, 0., rtol=0., atol=.0003)
    np.testing.assert_array_equal(predicted[0], expected['coordinates'][0])
