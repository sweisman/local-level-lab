import numpy as np
import pytest

from lll import covariance_scale_fit


def _fit(groups):
    return covariance_scale_fit.fit(groups, log_bounds=(-5., 5.), max_evaluations=100)


def test_diagonal_known_answer_recovers_inside_scales():
    roots = {name: np.eye(3)[:, i:i + 1] for i, name in
             enumerate(('native', 'persistent', 'maneuver'))}
    # For disjoint components, the variance MLE is the mean square in each axis.
    draws = np.array([[1., 2., 3.], [-1., 2., -3.]])
    result = _fit([(roots, draws)])
    assert result['status'] == 'interior'
    assert result['variances'] == pytest.approx(dict(native=1., persistent=4., maneuver=9.), rel=1e-5)


@pytest.mark.parametrize('maneuver', [np.zeros((2, 1)), np.array([[0.], [2.]])])
def test_fit_abstains_when_maneuver_term_is_missing_or_confounded(maneuver):
    roots = dict(native=np.eye(2), persistent=np.array([[0.], [1.]]), maneuver=maneuver)
    result = _fit([(roots, np.array([[1., 3.]]))])
    assert result == dict(status='unidentifiable', rank=2, evaluations=0, variances=None)


def test_generated_correlated_control_improves_independent_log_score():
    quiet = dict(native=np.eye(3), persistent=np.array([[1.], [1.], [0.]]),
                 maneuver=np.zeros((3, 1)))
    active = dict(quiet, maneuver=np.array([[0.], [1.], [1.]]))
    truth = np.array([0.5, 2., 8.])
    rng = np.random.default_rng(17301)
    # Generate directly as the sum of separately sampled measurement errors.
    def draws(roots, count):
        return sum(rng.normal(size=(count, root.shape[1])) @ root.T * np.sqrt(var)
                   for root, var in zip(roots.values(), truth, strict=True))

    def score(group, sample, variances):
        covariance = sum(var * (root @ root.T)
                         for root, var in zip(group.values(), variances, strict=True))
        return (np.linalg.slogdet(covariance)[1]
                + np.sum(sample * np.linalg.solve(covariance, sample.T).T) / len(sample))

    groups = [quiet, active]
    estimate = _fit([(group, draws(group, 4000)) for group in groups])
    assert estimate['status'] == 'interior'
    variances = list(estimate['variances'].values())
    assert variances == pytest.approx(truth, rel=.10)
    for group in groups:
        sample = draws(group, 4000)
        assert score(group, sample, variances) < score(group, sample, np.repeat(truth.mean(), 3))


def test_reaching_bound_is_explicit():
    roots = dict(native=np.array([[1.], [0.]]), drift=np.array([[0.], [1.]]))
    result = _fit([(roots, np.array([[1., 100.]]))])
    assert result['status'] == 'bound'
    assert result['variances']['drift'] == pytest.approx(np.exp(5.))


def test_objective_calls_do_not_exceed_allowance():
    roots = dict(native=np.array([[1.], [0.]]), drift=np.array([[0.], [1.]]))
    result = covariance_scale_fit.fit([(roots, np.array([[1., 3.]]))],
                                      log_bounds=(-5., 5.), max_evaluations=1)
    assert result == dict(status='budget_exhausted', rank=2, evaluations=1, variances=None)
