# SPDX-License-Identifier: AGPL-3.0-or-later
"""Physical fixtures independent of the replay generator and gyro fitter."""
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

import acceleration_motion as m


def test_varying_acceleration_recovers_gravity_for_fixed_mount():
    t = np.arange(100.)
    acceleration = np.column_stack([.3*np.sin(t/20), .1*np.cos(t/10), .05*np.sin(t/10)])
    C = Rotation.from_euler('ZYX', [25., 3., -8.], degrees=True).as_matrix().T
    forward = C@np.array([np.cos(np.radians(25)), np.sin(np.radians(25)), 0.])
    specific = (acceleration-[0, 0, m.G0])@C.T
    up, recovered, _ = m.recover_up(specific, acceleration, forward, np.full(len(t), np.radians(25)))
    assert up == pytest.approx(np.tile(-C[:, 2], (len(t), 1)), abs=1e-9)
    assert recovered == pytest.approx(np.broadcast_to(C, recovered.shape), abs=1e-9)
    assert np.max(np.linalg.norm(m.unit(specific)-up, axis=1)) > .02


def test_known_roll_survives_acceleration_correction():
    t = np.arange(400.)
    roll_rate = 1e-4
    roll = roll_rate*t
    C = Rotation.from_euler('X', roll[:, None]).as_matrix().transpose(0, 2, 1)
    acceleration = np.column_stack([.2*np.sin(t/25), np.zeros(len(t)), np.zeros(len(t))])
    force = np.einsum('nij,nj->ni', C, acceleration-[0., 0., m.G0])
    prepared = dict(t=t, acceleration=acceleration, force=force, heading=np.zeros(len(t)),
                    valid=np.ones(len(t), bool), window_seconds=30.)
    corrected = m.correct(prepared, np.array([1., 0., 0.]), .01)
    valid = corrected['valid']
    assert corrected['motion'][valid, 0] == pytest.approx(np.full(valid.sum(), roll_rate), rel=1e-6)
    assert np.max(np.abs(corrected['motion'][valid, 1:])) < 1e-9


def test_gap_and_invalid_force_never_have_differentiated_support():
    t = np.r_[np.arange(100.), np.arange(120., 220.)]
    force = np.tile([0., 0., -m.G0], (len(t), 1))
    valid = np.ones(len(t), bool); valid[30] = False
    prepared = m.prepare(t, np.full(len(t), 200.), np.zeros(len(t)), np.full(len(t), 10000.), force, valid, 15.)
    corrected = m.correct(prepared, [1., 0., 0.], .01)
    motion, supported = m.bin_average(t, corrected['motion'], corrected['valid'],
        dict(t=np.array([30., 70., 110., 170.]), dt=np.full(4, 20.)))
    assert supported.tolist() == [False, True, False, True]
    assert np.max(np.abs(motion[supported])) < 1e-9


def test_sparse_gps_and_bad_physics_are_rejected():
    t = np.arange(10.)*30
    with pytest.raises(ValueError, match='frequent GPS'):
        m.regular_runs(t, np.ones(len(t), bool))
    with pytest.raises(ValueError, match='envelope'):
        m.recover_up([[0., 0., -m.G0]], [[2., 0., 0.]], [1., 0., 0.], [0.])
    with pytest.raises(ValueError, match='gravity magnitude'):
        m.recover_up([[0., 0., -2*m.G0]], [[0., 0., 0.]], [1., 0., 0.], [0.])


def test_filter_uncertainty_matches_independent_linear_operator():
    t = np.arange(100.)
    sigma_a, sigma_f = m.independent_uncertainty(t, np.full(100, 200.), np.zeros(100),
        np.full(100, .3), np.full(100, .5), np.full(100, 8.), np.full((100, 3), .01), np.ones(100, bool), 15.)
    # Build the actual filter/gradient mapping column-by-column, independent of variance code.
    indices = np.arange(30, 71)
    operator = []
    for impulse in indices:
        values = np.zeros((100, 1)); values[impulse] = 1
        filtered, valid = m.matched_filter(t, values, np.ones(100, bool), 15.)
        derivative, _ = m.local_derivative(t, filtered, valid)
        operator.append(derivative[50, 0])
    assert sigma_a[50, 0] == pytest.approx(.3*np.linalg.norm(operator), rel=1e-12)
    assert np.isfinite(sigma_f[50]).all()
    assert np.isnan(sigma_a[:10]).all()


def test_prototype_has_no_decision_path():
    assert m.provenance()['production_enabled'] is False
    assert m.provenance()['decisions_enabled'] is False


def test_uncertainty_state_outside_envelope_excludes_local_support():
    t = np.arange(200.)
    acceleration = np.zeros((len(t), 3)); acceleration[50, 0] = 2.
    prepared = dict(t=t, acceleration=acceleration, force=np.tile([0., 0., -m.G0], (len(t), 1)),
                    heading=np.zeros(len(t)), valid=np.ones(len(t), bool), window_seconds=30.)
    result = m.correct(prepared, [1., 0., 0.], .01)
    _, valid = m.bin_average(t, result['motion'], result['valid'],
        dict(t=np.array([50., 150.]), dt=np.full(2, 20.)))
    assert valid.tolist() == [False, True]


def test_combined_yaw_pitch_roll_matches_independent_euler_rates():
    t = np.arange(400.)
    yaw_rate = .0003
    heading = yaw_rate*t
    pitch, bank = .015*np.sin(t/80), .02*np.cos(t/100)
    C = Rotation.from_euler('ZYX', np.column_stack([heading, pitch, bank])).as_matrix().transpose(0, 2, 1)
    acceleration = np.column_stack([.2*np.sin(t/25), .1*np.cos(t/20), .03*np.sin(t/30)])
    force = np.einsum('nij,nj->ni', C, acceleration-[0., 0., m.G0])
    prepared = dict(t=t, acceleration=acceleration, force=force, heading=heading,
                    valid=np.ones(len(t), bool), window_seconds=30.)
    result = m.correct(prepared, [1., 0., 0.], .01)
    pitch_rate, bank_rate = .015/80*np.cos(t/80), -.02/100*np.sin(t/100)
    expected = np.column_stack([bank_rate-yaw_rate*np.sin(pitch),
        pitch_rate*np.cos(bank)+yaw_rate*np.sin(bank)*np.cos(pitch),
        -pitch_rate*np.sin(bank)+yaw_rate*np.cos(bank)*np.cos(pitch)])
    assert np.max(np.abs(result['motion'][result['valid']]-expected[result['valid']])) < 1e-7
