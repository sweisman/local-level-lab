# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_information as info
from lll import ilvis0_excitation_controls as controls, ilvis0_gps_sensitivity as sensitivity


def test_diagonal_reference_information_has_independent_closed_form():
    names = ('position_x', 'gyro_bias_y', 'time_offset')
    jac = np.diag([0., 2., .1])
    row, resolution = info.information(jac, names, dict.fromkeys(names, 1.))
    np.testing.assert_allclose(np.diag(resolution), [0., 4/5, .01/1.01])
    assert row['modes_above_unit_information'] == 1
    assert row['parameters']['position_x']['reference_sigma_to_bound'] == 1.
    assert row['parameters']['gyro_bias_y']['reference_sigma_to_bound'] == pytest.approx(1/np.sqrt(5))


def test_partial_rank_and_confounding_preserve_null_reference_uncertainty():
    names = ('position_x', 'time_offset', 'gyro_gain_y')
    row, resolution = info.information([[1., 1., 0.]], names, dict.fromkeys(names, 1.))
    np.testing.assert_allclose(resolution, [[1/3, 1/3, 0], [1/3, 1/3, 0], [0, 0, 0]], atol=1e-15)
    assert row['parameters']['gyro_gain_y']['reference_sigma_to_bound'] == 1.
    assert row['parameters']['position_x']['reference_sigma_to_bound'] == pytest.approx(np.sqrt(2/3))


def test_more_assumed_noise_cannot_improve_reference_information():
    jac = np.array([[3., 1.], [1., 2.], [2., -1.]])
    names = ('position_x', 'time_offset'); limits = dict.fromkeys(names, 1.)
    _, a = info.information(jac, names, limits)
    _, b = info.information(jac/100, names, limits)
    assert np.min(np.linalg.eigvalsh(a-b)) >= -1e-15


def test_near_rank_cutoff_is_smooth_and_unhelpful():
    names = ('position_x', 'gyro_gain_y'); limits = dict.fromkeys(names, 1.)
    r = info.compare([np.diag([10., 1e-8]), np.diag([10., 2e-8])], names, limits)
    assert r['resolution_stable_under_tested_steps']
    assert r['parameters']['gyro_gain_y']['minimum_reference_sigma_to_bound'] > .999999
    assert r['steps'][0]['modes_above_unit_information'] == 1
    assert not r['data_only_marginal_sigmas_reported']


def test_material_step_changes_and_information_boundary_are_not_hidden():
    names = ('position_x', 'time_offset'); limits = dict.fromkeys(names, 1.)
    r = info.compare([np.diag([2., .1]), np.diag([2., 1.1])], names, limits)
    assert not r['resolution_stable_under_tested_steps']
    assert r['steps'][0]['modes_above_unit_information_with_proxy_subtracted'] == 0
    assert r['steps'][0]['modes_above_unit_information_with_proxy_added'] == 2
    assert not r['derivative_noise_proxy_is_bound']


def test_central_derivative_counts_and_exact_steady_gain_null():
    assumption = next(a for a in sensitivity.assumptions() if a.name == 'formal_only')
    p, point, _ = controls.fixture(2., 'steady_orientation', assumption, limits={'gyro_gain_y': .01})
    matrices, calls = info.central_jacobians(p, point)
    assert calls == 8
    for j in matrices:
        np.testing.assert_array_equal(j, np.zeros_like(j))
    with pytest.raises(ValueError, match='central steps'):
        info.central_jacobians(p, np.ones(1))


def test_central_derivative_against_independent_constant_force_displacement():
    # Gyro-free constant orientation fixture has d north / d accel_bias = -t²/2;
    # calibration subtracts the injected bias. Whiten this independent derivative.
    assumption = next(a for a in sensitivity.assumptions() if a.name == 'formal_only')
    p, point, metric = controls.fixture(2., 'steady_orientation', assumption, limits={'accel_bias_x': .05})
    matrices, _ = info.central_jacobians(p, point)
    delta = np.zeros_like(p.gps)
    delta[:, 0] = -.5*p.gps_times**2*.05*metric[0]
    expected = p.whiten(delta)
    for j in matrices:
        np.testing.assert_allclose(j[:, 0], expected, rtol=2e-5, atol=2e-4)


def test_control_preserves_independent_trajectory_and_every_fixed_step():
    assumption = next(a for a in sensitivity.assumptions() if a.name == 'h1_v3_tau60')
    r = info.run_control(2., 'brief_pitch', assumption)
    assert r['analytic_control_passed'] and r['prediction_evaluations'] == 65
    assert [s['normalized_central_step'] for s in r['information']['steps']] == list(info.STEPS)
    assert r['information']['scientific_decision'] == 'abstain'


@pytest.mark.parametrize('jac,limits', [([[float('nan')]], {'time_offset': 1.}),
                                     ([[1.]], {'time_offset': 0.})])
def test_invalid_information_fails(jac, limits):
    with pytest.raises(ValueError, match='finite Jacobian'):
        info.information(jac, ('time_offset',), limits)


def test_large_information_does_not_round_reference_sigma_to_zero():
    row, _ = info.information([[1e10]], ('position_x',), {'position_x': 1.})
    assert row['parameters']['position_x']['reference_sigma_to_bound'] == pytest.approx(1e-10)


def test_interrupted_start_limits_and_corruption_are_rejected(tmp_path):
    from ilvis0_information_worker import charge
    tasks = {'one': {}, 'two': {}}
    charge(tmp_path, tasks, 'one', 'digest')
    charge(tmp_path, tasks, 'one', 'digest')
    with pytest.raises(ValueError, match='allowance exhausted'):
        charge(tmp_path, tasks, 'one', 'digest')
    with pytest.raises(ValueError, match='corrupt'):
        charge(tmp_path, tasks, 'two', 'changed')
