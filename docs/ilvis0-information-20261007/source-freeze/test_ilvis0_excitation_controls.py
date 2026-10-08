# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll import ilvis0_excitation_controls as controls, ilvis0_gps_sensitivity as sensitivity


def assumption(name='formal_only'):
    return next(a for a in sensitivity.assumptions() if a.name == name)


def test_independent_position_integral_and_rotation():
    assert controls.north_at(.25) == pytest.approx(200*.25+.5*.5*.25**2)
    t = 1.25
    independent = 200*t
    for start, end in ((0., .5), (.5, 1.), (1., 1.25)):
        a = controls.acceleration_at((start+end)/2)
        independent += a*(t*(end-start)-(end**2-start**2)/2)
    assert controls.north_at(t) == pytest.approx(independent)
    r = controls.pitch_rotation(.2)
    assert np.allclose(r.T@r, np.eye(3)) and np.linalg.det(r) == pytest.approx(1.)


def test_brief_rotation_resolves_native_event_and_returns_without_erasing_force():
    p, point, metric = controls.fixture(20., 'brief_pitch', assumption(), limits={})
    assert np.sum(abs(p.theta[:, 1])) == pytest.approx(2*math.radians(.1))
    assert np.sum(p.theta[:, 1]) == pytest.approx(0., abs=1e-14)
    assert np.sum(np.isclose(p.dt, .005)) == 200
    assert np.any(abs(p.dv[:, 0]-np.array([controls.acceleration_at(t) for t in
        np.cumsum(p.dt)-p.dt/2])*p.dt) > 1e-5)


def test_twenty_second_truth_matches_independent_trajectory():
    truth = dict(gyro_bias_y=2e-6, gyro_gain_y=.002, accel_bias_x=.01, accel_gain_x=.003, time_offset=.035)
    p, point, metric = controls.fixture(20., 'brief_pitch', assumption(), truth=truth)
    error = (p.predict(point, 'flat_still')-p.gps)/metric
    assert np.max(abs(error)) < 2e-6


def test_covariance_changes_preserve_native_measurements_and_full_correlations():
    a, _, _ = controls.fixture(2., 'brief_pitch', assumption())
    b, _, _ = controls.fixture(2., 'brief_pitch', assumption('h1_v3_tau60'))
    for name in ('theta', 'dv', 'dt', 'gps', 'gps_times'):
        np.testing.assert_array_equal(getattr(a, name), getattr(b, name))
    c = b.cholesky@b.cholesky.T
    assert c[0, 3] > 0 and c[0, 1] != 0


def test_partial_precision_does_not_assign_pseudoinverse_sigma_to_null_parameter():
    names = ('accel_bias_x', 'time_offset', 'gyro_gain_y')
    jac = np.array([[2., 0., 0.], [0., 4., 0.]])
    r = controls.jacobian_precision(jac, jac, names, dict.fromkeys(names, 1.))
    assert r['rank'] == 2
    assert r['parameters']['accel_bias_x']['local_sigma'] == pytest.approx(.5)
    assert r['parameters']['time_offset']['local_sigma'] == pytest.approx(.25)
    assert r['parameters']['gyro_gain_y']['local_sigma'] is None
    with pytest.raises(ValueError, match='matching'):
        controls.jacobian_precision(jac, [[float('nan')]], names, dict.fromkeys(names, 1.))


def test_gyro_gain_requires_known_rotation_excitation():
    limits = {'gyro_gain_y': .01}
    steady, point, _ = controls.fixture(2., 'steady_orientation', assumption(), limits=limits)
    r = controls.tangent(steady, point)
    assert r['rank'] == 0 and r['parameters']['gyro_gain_y']['local_sigma'] is None
    pitch, point, _ = controls.fixture(2., 'brief_pitch', assumption(), limits=limits)
    r = controls.tangent(pitch, point)
    assert r['rank'] == 1 and r['parameters']['gyro_gain_y']['local_sigma'] is not None


def test_longer_timing_recovery_stays_bounded_and_scientifically_abstains():
    r = controls.run_recovery(20., 'time_offset', assumption('h1_v3_tau60'))
    assert r['recovery_passed'] and r['fit']['evaluations'] <= 160
    assert r['fit']['scientific_decision'] == 'abstain' and r['empirical_earth_fit_attempts'] == 0


def test_invalid_duration_and_truth_bounds_fail_before_prediction():
    with pytest.raises(ValueError, match='fixed duration'):
        controls.fixture(30., 'brief_pitch', assumption())
    with pytest.raises(ValueError, match='active parameter'):
        controls.fixture(20., 'brief_pitch', assumption(), truth={'gyro_bias_x': 0.})
    with pytest.raises(ValueError, match='outside bounds'):
        controls.fixture(20., 'brief_pitch', assumption(), truth={'gyro_bias_y': .1})
