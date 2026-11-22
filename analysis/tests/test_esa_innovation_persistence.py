# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_innovation_persistence import PersistenceScore, select_memory, transitions
from lll.esa_motion_innovation_scale import InnovationScore


def test_causal_transition_uses_elapsed_time_and_current_motion():
    times = [0., .5, 2., 3.]
    expected = [0., np.exp(-1.5/4.), .5*np.exp(-1./4.)]
    actual = transitions(times, [0., 0., 1., .5], 0., 4.)
    np.testing.assert_allclose(actual, expected, rtol=1e-14)
    changed = transitions(times, [0., 0., 1., 0.], 0., 4.)
    np.testing.assert_array_equal(actual[:2], changed[:2])
    with pytest.raises(ValueError):
        transitions([0., 1., 1.], [0., 1., 1.], 0., 4.)


def test_temporal_innovation_score_matches_independent_dense_covariance():
    times = np.array([1., 1.4, 2.1, 4., 5.])
    response = np.array([0., .1, .8, 1., .6])
    rng = np.random.default_rng(15)
    y, root = rng.normal(size=15), rng.normal(size=(15, 4))*.25
    scales = np.array([.2, 2., .7, .8])
    native_log = .15
    baseline = InnovationScore(y, root, np.repeat(response, 3), native_log)
    scorer = PersistenceScore(baseline, times, np.log(scales))
    answer = scorer.score(2., 8.)
    d = np.diff(times)
    phi = (1-response[1:])*np.exp(-d/2.)+response[1:]*np.exp(-d/8.)
    correlation = np.eye(len(times))
    for i in range(len(times)):
        for j in range(i+1, len(times)):
            correlation[i, j] = correlation[j, i] = np.prod(phi[i:j])
    scale = np.sqrt((scales[:3]+scales[-1]*response[:, None]).ravel())
    covariance = np.kron(correlation, np.eye(3))*scale[:, None]*scale+root@root.T
    quadratic = y@np.linalg.solve(covariance, y)
    log_score = .5*(quadratic+np.linalg.slogdet(covariance)[1]+len(y)*np.log(2.*np.pi))+native_log
    assert answer['quadratic'] == pytest.approx(quadratic)
    assert answer['negative_log_score'] == pytest.approx(log_score)


def test_zero_memory_reproduces_the_saved_diagonal_correction():
    response = np.array([0., .4, 1., .8])
    baseline = InnovationScore(np.arange(12.)*.01, np.eye(12)[:, :3], np.repeat(response, 3), -.4)
    scales = np.array([.3, .5, .7, 2.])
    scorer = PersistenceScore(baseline, [1., 2., 3., 4.], np.log(scales))
    expected = baseline.score(np.tile(scales[:3], 4), scales[3])
    assert scorer.score(0., 0.) == pytest.approx(expected, rel=1e-12)


def test_memory_search_charges_each_setting_and_selects_only_on_donors():
    class Donor:
        def score(self, quiet, turning):
            return {'negative_log_score': (quiet-1.)**2+(turning-2.)**2}

    ledger = []
    choice = select_memory([Donor()]*6, reserve=lambda: ledger.append(1))
    assert len(ledger) == 100
    assert choice['common']['seconds'] == [1., 1.]
    assert choice['motion']['seconds'] == [1., 2.]
