# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import math

import numpy as np
import pytest

from lll import ilvis0_estimator as estimator
from lll import ilvis0_forward as forward
from lll.ilvis0_estimator_controls import fixture, control_results


def test_analytic_bias_recovery():
    r = estimator.fit_control(fixture(), 'flat_still', maximum_evaluations=100)
    assert r['converged'] and r['nuisance_fully_observable']
    assert r['parameters']['accel_bias_x'] == pytest.approx(.04, abs=2e-7)
    assert r['evaluations'] <= 100
    assert r['scientific_decision'] == 'abstain'


def test_analytic_orientation_gain_timing_and_gauge():
    r = control_results()
    assert r['effective_orientation']['parameters']['attitude_y'] == pytest.approx(.002, abs=2e-7)
    # Midpoint mechanization has O(dt^2) position error for nonconstant acceleration.
    assert r['gain']['parameters']['accel_gain_x'] == pytest.approx(.003, abs=2e-5)
    assert r['timing']['parameters']['time_offset'] == pytest.approx(.035, abs=2e-5)
    assert all(r[k]['converged'] for k in ('bias', 'effective_orientation', 'gain', 'timing'))
    assert not r['orientation_acceleration_ambiguity']['nuisance_fully_observable']


def test_velocity_and_bias_joint_recovery():
    p = fixture(estimator.Bounds({'velocity_x': .2, 'accel_bias_x': .1}))
    p.initial['velocity_ned_mps'][0] = .4
    r = estimator.fit_control(p, 'flat_still', maximum_evaluations=100)
    assert r['nuisance_rank'] == 2
    assert r['parameters']['velocity_x'] == pytest.approx(.1, abs=2e-7)
    assert r['parameters']['accel_bias_x'] == pytest.approx(.04, abs=2e-7)


def test_gps_covariance_is_common_coordinate_space():
    p = fixture()
    n = p.gps.size
    diagonal = np.diag(p.cholesky)**2
    cov = np.diag(diagonal)
    cov[0, 3] = cov[3, 0] = .4*math.sqrt(diagonal[0]*diagonal[3])
    q = fixture(covariance=cov)
    delta = np.zeros_like(q.gps)
    delta[0, 0] = math.sqrt(diagonal[0])
    white = q.whiten(delta)
    assert white@white == pytest.approx(1/(1-.4**2))
    with pytest.raises(ValueError, match='positive definite'):
        fixture(covariance=np.zeros((n, n)))
    cov[0, 3] = 0
    with pytest.raises(ValueError, match='symmetric'):
        fixture(covariance=cov)


def test_timing_support_and_no_measurement_interpolation():
    with pytest.raises(ValueError, match='whole timing bound'):
        fixture(estimator.Bounds({'time_offset': .3}))
    with pytest.raises(ValueError, match='duplicate/reversed'):
        fixture(times=[.5, .5])
    p = fixture(estimator.Bounds({}), bias=0., times=[.253, .997, 1.743])
    before = p.gps.copy()
    predicted = p.predict([], 'flat_still')
    assert np.max(abs(predicted-p.gps)) < 2e-14
    np.testing.assert_array_equal(p.gps, before)
    assert not p.theta.flags.writeable and not p.gps.flags.writeable


def test_bounds_and_processing_rejection():
    for limits in ({'unknown': 1}, {'gyro_gain_x': 1}, {'time_offset': float('nan')}, {'attitude_x': -1}):
        with pytest.raises(ValueError):
            estimator.Bounds(limits)
    p = fixture()
    with pytest.raises(ValueError, match='outside bounds'):
        p.predict([1.01], 'flat_still')
    with pytest.raises(ValueError, match='disc metric scale'):
        forward.coordinate_rates('flat_still', .8, 20., [0., 0., 0.])


def test_every_numerical_derivative_counts_toward_budget():
    r = estimator.fit_control(fixture(), 'flat_still', maximum_evaluations=4)
    assert r['evaluations'] <= 4
    assert not r['converged']
    assert r['nuisance_rank'] == 1
    assert 'exhausted' in r['message']


def test_bounded_pair_profile_does_not_use_unbounded_absorption():
    r = estimator.bounded_pair_profile([10., 0.], [[1.], [0.]])
    assert r['remaining_energy'] == pytest.approx(81.)
    assert r['unbounded_remaining_energy'] == pytest.approx(0.)
    assert r['active_bounds'] == [0]
    r = estimator.bounded_pair_profile([1., 2.], np.empty((2, 0)))
    assert r['retained_fraction'] == 1
    assert estimator.bounded_pair_profile([0.], [[0.]])['retained_fraction'] is None


def test_pairwise_partial_information_without_global_rank():
    p = {'rotating': [0., 0.], 'still': [10., 0.], 'disc': [10., 1.]}
    j = {key: [[0.], [1.]] for key in p}
    r = estimator.pairwise_design(p, j)
    assert r['rotating__still']['worst_remaining_energy'] == pytest.approx(100.)
    assert r['disc__still']['worst_remaining_energy'] < 1e-10
    assert all(x['decision'] == 'abstain' for x in r.values())


def test_empirical_gate_precedes_start_charge(tmp_path):
    path = tmp_path/'starts.jsonl'
    ledger = estimator.StartLedger(path, 'a'*64)
    with pytest.raises(ValueError, match='processing_independence'):
        estimator.fit_observed(fixture(), 'flat_still', evidence={}, ledger=ledger,
                               task='file1', maximum_evaluations=100)
    assert not path.exists()
    with pytest.raises(ValueError):
        estimator.fit_observed(fixture(), 'flat_still', evidence={name: True for name in estimator.REQUIRED_EVIDENCE},
                               ledger=ledger, task='file1', maximum_evaluations=100)
    assert not path.exists()


def test_start_ledger_counts_interruptions_and_rejects_changes(tmp_path):
    path = tmp_path/'starts.jsonl'
    ledger = estimator.StartLedger(path, 'a'*64)
    for i in range(24):
        ledger.charge('file1', 100)  # No completion needed: interrupted starts count.
    assert len(path.read_text().splitlines()) == 24
    with pytest.raises(ValueError, match='exhausted'):
        ledger.charge('file1', 100)
    with pytest.raises(ValueError, match='incompatible'):
        estimator.StartLedger(path, 'b'*64).charge('file1', 100)


def test_start_ledger_file_count_and_corruption(tmp_path):
    path = tmp_path/'starts.jsonl'
    ledger = estimator.StartLedger(path, 'a'*64)
    for i in range(6):
        ledger.charge(str(i), 100)
    with pytest.raises(ValueError, match='exhausted'):
        ledger.charge('file7', 100)
    with path.open('a') as out:
        out.write('{"broken":true}\n')
    with pytest.raises(ValueError, match='corrupt'):
        ledger.charge('0', 100)


def test_native_interval_and_processing_guards():
    p = fixture()
    kwargs = dict(clock_hypothesis='header_elapsed', processing_hypothesis='unsubtracted_increment_hypothesis',
                  maximum_interval_s=.015, gravity_mps2=9.81, disc_radius_m=p.radius)
    def construct(dt, **override):
        return estimator.MotionProblem(p.theta, p.dv, dt, p.gps_times, p.gps,
            p.cholesky@p.cholesky.T, p.initial, p.bounds, **(kwargs|override))
    for value in (0., -.01, .02, float('nan')):
        dt = p.dt.copy()
        dt[20] = value
        with pytest.raises(ValueError):
            construct(dt)
    with pytest.raises(ValueError, match='unsubtracted'):
        construct(p.dt, processing_hypothesis='unknown')
    with pytest.raises(ValueError, match='clock'):
        construct(p.dt, clock_hypothesis='invented')


def test_covariance_longitude_wrap_and_zero_parameter_control():
    p = fixture(estimator.Bounds({}), bias=0.)
    d = np.zeros_like(p.gps)
    d[:, 1] = 2*math.pi
    assert np.max(abs(p.whiten(d))) == 0
    r = estimator.fit_control(p, 'flat_still', maximum_evaluations=10)
    assert r['converged'] and r['evaluations'] == 1 and r['nuisance_rank'] == 0


def test_pair_profile_rejects_nonfinite_or_mismatched_inputs():
    for contrast, jac in (([float('nan')], [[1.]]), ([1., 2.], [[1.]])):
        with pytest.raises(ValueError, match='same whitened coordinates'):
            estimator.bounded_pair_profile(contrast, jac)
