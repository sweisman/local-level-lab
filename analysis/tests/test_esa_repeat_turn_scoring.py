import numpy as np
import pytest
from scipy.stats import chi2

from lll import esa_repeat_turn_scoring as score
from lll.studies.artifacts import digest


def fixture():
    time = np.arange(1., 13.)
    shape = 3*len(time)
    anchor = np.array([1., -.1, 500.])
    path = np.broadcast_to(anchor, (len(time), 3))
    root = .04*np.eye(shape)
    exposure = np.zeros(len(time))
    exposure[[2, 5]] = [3., 2.]
    return time, anchor, path, root, exposure


def test_score_agrees_with_independent_dense_gaussian_calculation():
    time, anchor, path, root, exposure = fixture()
    actual = path.copy()
    actual[:, 2] += .01*time
    receipt = score.seal(training_sha256='b'*64, law='increment', previous_time=0.,
                         times=time, anchor=anchor, mean=path, native_root=root, exposure=exposure)
    report = score.score_sealed(receipt, expected_sha256=digest(receipt), times=time, actual=actual)
    assert report['physical_rms_neu_m'][2] == pytest.approx(.01*np.sqrt(np.mean(time**2)))
    y = np.zeros_like(actual)
    y[:, 2] = .01*time
    steady = np.kron((.5*time**2)[:, None], np.eye(3))*.001
    lag = np.maximum(time[:, None]-time[None, :], 0.)
    response = 15.*lag-225.*(1.-np.exp(-lag/15.))
    turn = np.kron(response*np.sqrt(exposure), np.eye(3)[:, :2])*.001
    covariance = score.NATIVE_VARIANCE['increment']*(root@root.T)+steady@steady.T+turn@turn.T
    expected = y.ravel()@np.linalg.solve(covariance, y.ravel())
    determinant = np.linalg.slogdet(covariance)[1]
    assert report['scores']['both']['quadratic'] == pytest.approx(expected)
    assert report['scores']['both']['negative_log_score'] == pytest.approx((expected+determinant+y.size*np.log(2*np.pi))/2)


def test_changed_sealed_forecast_or_scoring_clock_is_rejected():
    time, anchor, path, root, exposure = fixture()
    payload = score.seal(training_sha256='b'*64, law='point', previous_time=0.,
                         times=time, anchor=anchor, mean=path, native_root=root, exposure=exposure)
    with pytest.raises(ValueError, match='sealed forecast'):
        score.score_sealed(payload+b' ', expected_sha256=digest(payload), times=time, actual=path)
    with pytest.raises(ValueError, match='clock'):
        score.score_sealed(payload, expected_sha256=digest(payload), times=time+.1, actual=path)


def test_reversed_measured_turn_preserves_the_covariance_rule():
    from lll.maneuver_error_roots import turn_exposure

    time, _, _, root, _ = fixture()
    dt = np.full(28, .5)
    gyro = np.zeros((28, 3))
    gyro[8:14, 2] = np.deg2rad(2.5)*dt[8:14]
    positive = turn_exposure(dt, gyro, time, previous_time=0., threshold_deg_s=1.)
    negative = turn_exposure(dt, -gyro, time, previous_time=0., threshold_deg_s=1.)
    assert positive.sum() > 0.
    left = score.factors(time, previous_time=0., native_root=root, exposure=positive, law='increment')
    right = score.factors(time, previous_time=0., native_root=root, exposure=negative, law='increment')
    assert left['both'] == pytest.approx(right['both'])
    assert np.linalg.norm(left['turn']-left['native']) > 0.


def test_known_generated_errors_recover_joint_reference_distribution():
    time, _, _, root, exposure = fixture()
    rng = np.random.default_rng(37288)
    count = 4096
    age = time[None, :]
    base = rng.normal(size=(count, len(time), 3))*.04*np.sqrt(score.NATIVE_VARIANCE['point'])
    acceleration = rng.normal(size=(count, 3))*.001
    error = base + .5*age[:, :, None]**2*acceleration[:, None, :]
    for event_index in np.flatnonzero(exposure):
        elapsed = np.maximum(time-time[event_index], 0.)
        position = 15.*elapsed-225.*(1.-np.exp(-elapsed/15.))
        scale = .001*np.sqrt(exposure[event_index])
        error[:, :, :2] += rng.normal(size=(count, 1, 2))*scale*position[None, :, None]
    factors = score.factors(time, previous_time=0., native_root=root, exposure=exposure, law='point')
    result = {name: score.gaussian(factor, error.reshape(count, -1)) for name, factor in factors.items()}
    reference = result['both']['quadratic']
    dimension = len(time)*3
    assert np.mean(reference)/dimension == pytest.approx(1., abs=.015)
    assert .935 < np.mean(reference <= chi2.ppf(.95, dimension)) < .965
    assert all(np.mean(result['both']['negative_log_score']) < np.mean(result[name]['negative_log_score'])
               for name in ('native', 'steady', 'turn'))
