# SPDX-License-Identifier: AGPL-3.0-or-later
import gzip
import hashlib
import json

import numpy as np
import pytest

from lll import ilvis0_gps_sensitivity as sensitivity
from ilvis0_gnss_worker import verify_cached


def test_assumption_grid_is_fixed_and_not_calibration():
    grid = sensitivity.assumptions()
    assert len(grid) == 13 and len({a.name for a in grid}) == 13
    assert all(a.report()['calibrated'] is False for a in grid)
    with pytest.raises(ValueError):
        sensitivity.Assumption('bad', (-1., 1., 1.), 10., (0.,)*3, (0.,)*3)


def test_covariance_matches_dense_oracle_with_cross_axis_terms():
    t = np.array([0., 1., 3., 6.])
    block = np.array([[2., .3, .2], [.3, 1., .1], [.2, .1, 3.]])
    blocks = np.repeat(block[None], len(t), axis=0)
    a = sensitivity.Assumption('test', (1., 2., 3.), 10., (3., 2., 1.), (2., 4., 6.))
    u = t/t[-1]; k = sensitivity.correlation(t, a.correlation_s)
    dense = np.kron(np.eye(len(t)), block)
    dense += np.kron(k, np.diag(np.square(a.noise_neu_m)))
    dense += np.kron(np.ones_like(k), np.diag(np.square(a.offset_neu_m)))
    dense += np.kron(np.outer(u, u), np.diag(np.square(a.drift_neu_m)))
    w = np.array([.2, -.1, .3, .6])
    transform = np.kron(w[None], np.eye(3))
    expected = transform@dense@transform.T
    actual = sensitivity.weighted_covariance(w, blocks, k, u, a)
    assert np.allclose(actual, expected, atol=1e-12)
    assert actual[0, 1] == pytest.approx(.3*np.sum(w*w))


def test_correlated_means_do_not_use_independent_epoch_precision():
    t = np.arange(101.)
    b = np.repeat(np.eye(3)[None], len(t), axis=0); w = np.ones(len(t))/len(t)
    independent = sensitivity.Assumption('iid', (1.,)*3, 0., (0.,)*3, (0.,)*3)
    correlated = sensitivity.Assumption('ou', (1.,)*3, 300., (0.,)*3, (0.,)*3)
    offset = sensitivity.Assumption('offset', (0.,)*3, 0., (3.,)*3, (0.,)*3)
    compute = lambda a: sensitivity.weighted_covariance(w, b,
        sensitivity.correlation(t, a.correlation_s), t/t[-1], a)
    assert np.diag(compute(independent))[0] == pytest.approx(2/len(t))
    assert np.diag(compute(correlated))[0] > .8
    assert np.diag(compute(offset))[0] == pytest.approx(9+1/len(t))


def test_dense_coordinate_covariance_is_positive_definite_and_retains_time_terms():
    t = np.array([0., 1., 2.]); b = np.repeat(np.eye(3)[None], 3, axis=0)
    a = sensitivity.Assumption('test', (1., 1., 3.), 60., (3., 3., 10.), (1., 1., 3.))
    c = sensitivity.coordinate_covariance(t, np.full(3, .8), np.full(3, 1000.), b, a)
    assert c.shape == (9, 9) and np.allclose(c, c.T)
    assert np.min(np.linalg.eigvalsh(c)) > 0 and c[0, 3] > 0
    assert c[2, 2] == pytest.approx(1+9+100)
    with pytest.raises(ValueError, match='nonpolar'):
        sensitivity.coordinate_covariance(t, np.full(3, np.pi/2), np.full(3, 1000.), b, a)


def test_actual_timestamp_derivatives_recover_polynomial_and_cancel_common_offset():
    t = np.array([-3., -1.8, -.8, 0., .9, 2.1, 3.])
    (indices, velocity, acceleration), reason = sensitivity.quadratic_weights(t, 0., 6.)
    assert reason is None and len(indices) == len(t)
    p = 19+4*t+1.5*t*t
    assert velocity@p == pytest.approx(4., abs=1e-12)
    assert acceleration@p == pytest.approx(3., abs=1e-12)
    assert np.sum(velocity) == pytest.approx(0., abs=1e-12)
    assert np.sum(acceleration) == pytest.approx(0., abs=1e-12)
    a = sensitivity.Assumption('offset', (0.,)*3, 0., (100.,)*3, (5.,)*3)
    b = np.repeat(np.eye(3)[None], len(t), axis=0)
    c = sensitivity.weighted_covariance(acceleration, b, np.eye(len(t)), (t+3)/6, a)
    assert c[0, 0] == pytest.approx(np.sum(acceleration**2), abs=1e-12)


def test_missing_epoch_and_edge_do_not_become_interpolated_windows():
    t = np.array([-3., -2., 0., 1., 2., 3.])
    assert sensitivity.quadratic_weights(t, 0., 6.) == (None, 'receiver_gap')
    assert sensitivity.quadratic_weights(np.arange(10.), 0., 6.) == (None, 'incomplete_window')
    with pytest.raises(ValueError, match='strictly increasing'):
        sensitivity.quadratic_weights([0., 1., 1.], 1., 2.)
    with pytest.raises(ValueError, match='actual epoch'):
        sensitivity.quadratic_weights(np.arange(10.), .5, 2.)


def test_short_lateral_motion_is_retained_in_short_window_and_attenuated_in_long_one():
    # A 200 m/s trajectory has a one-second ~0.1deg lateral velocity excursion.
    # Integrate it as a ramp/plateau; no IMU, Earth simulation or scientific gate.
    t = np.arange(-30., 31.)
    displacement = 200*np.sin(np.deg2rad(.1))*np.clip(t, 0., 1.)
    short, _ = sensitivity.quadratic_weights(t, 0., 2.)
    long, _ = sensitivity.quadratic_weights(t, 0., 60.)
    short_a = short[2]@displacement[short[0]]
    long_a = long[2]@displacement[long[0]]
    assert short_a > .34 and abs(long_a) < short_a/100


def test_position_loader_rejects_hash_epoch_mismatch_failure_and_duplicates(tmp_path):
    path = tmp_path/'positions.gz'
    rows = [dict(method=m, status='converged', gps_week=2000, gps_week_seconds=float(i))
        for i in range(3) for m in sensitivity.METHODS]
    def save():
        with gzip.open(path, 'wt') as stream:
            for r in rows:
                stream.write(json.dumps(r)+'\n')
        return hashlib.sha256(path.read_bytes()).hexdigest()
    digest = save()
    result, t = sensitivity.load_series(path, digest, 3)
    assert len(result['l1_broadcast']) == 3 and np.array_equal(t, [0., 1., 2.])
    with pytest.raises(ValueError, match='hash'):
        sensitivity.load_series(path, 'bad', 3)
    rows[-1]['gps_week_seconds'] = 2.1
    with pytest.raises(ValueError, match='epoch mismatch'):
        sensitivity.load_series(path, save(), 3)
    rows[-1]['status'] = 'abstain'
    with pytest.raises(ValueError, match='failed epoch'):
        sensitivity.load_series(path, save(), 3)
    rows[-1].update(status='converged', gps_week_seconds=1.)
    with pytest.raises(ValueError, match='strictly increasing'):
        sensitivity.load_series(path, save(), 3)


def test_formal_blocks_reject_nonpositive_and_nonsymmetric_covariance():
    with pytest.raises(ValueError, match='positive definite'):
        sensitivity.formal_blocks([np.diag([1., 1., 0.])])
    b = np.eye(3); b[0, 1] = .1
    with pytest.raises(ValueError, match='symmetric'):
        sensitivity.formal_blocks([b])


def test_cached_sensitivity_report_rejects_corruption(tmp_path):
    task = dict(task_id='task', source_sha256='source')
    report = task | dict(artifacts_sha256={})
    target = tmp_path/'task.json.gz'
    with gzip.open(target, 'wt') as stream:
        json.dump(report, stream)
    receipt = dict(manifest_sha256='manifest', report_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    (tmp_path/'task.receipt.json').write_text(json.dumps(receipt))
    assert verify_cached(tmp_path, task, 'manifest') == report
    with pytest.raises(ValueError, match='corrupt'):
        verify_cached(tmp_path, task, 'changed')
    target.write_bytes(b'bad')
    with pytest.raises(ValueError, match='corrupt'):
        verify_cached(tmp_path, task, 'manifest')
