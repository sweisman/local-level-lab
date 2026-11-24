"""Known answers for a support bound with several norm constraints."""

import math

import numpy as np
import pytest

from lll.quadratic_support_bound import solve_support


def test_ellipsoid_matches_analytic_support_across_coordinate_scales():
    scales = np.array([1e-6, 4., 5e6])
    normalized_objective = np.array([1., .5, .3])
    solution = solve_support([np.diag(scales)], scales*normalized_objective, 1./scales)
    expected = np.linalg.norm(normalized_objective)
    assert solution['lower'] <= expected <= solution['upper']
    assert solution['upper']-solution['lower'] < 1e-10
    assert np.linalg.norm(scales*solution['point']) <= 1.


def test_two_ellipsoids_both_limit_the_known_answer():
    scales = np.array([1e-5, 1e5])
    matrices = [np.diag(scales*np.array([1., .5])), np.diag(scales*np.array([.5, 1.]))]
    objective = scales*np.array([1., 1.2])
    result = solve_support(matrices, objective, 1./scales)
    expected = 2.2*math.sqrt(.8)
    assert result['lower'] <= expected <= result['upper']
    assert result['upper']-result['lower'] < 1e-6
    np.testing.assert_allclose(scales*result['point'], [math.sqrt(.8)]*2, atol=3e-7)


def test_coordinate_limits_and_early_stop_still_bracket_the_optimum():
    boxes = [np.array([[1., 0.]]), np.array([[0., 1.]])]
    for cap in (1, 100):
        result = solve_support(boxes, [2., -1.], [1., 1.], max_iterations=cap)
        assert result['lower'] <= 3. <= result['upper']
        assert result['iterations'] <= cap
        assert np.max(abs(result['point'])) <= 1.
    assert result['upper']-result['lower'] < 1e-7


def test_missing_joint_direction_is_rejected_before_running_solver():
    with pytest.raises(ValueError, match='jointly constrain'):
        solve_support([np.array([[1., 0.]])], [0., 1.], [1., 1.])


def test_saved_multipliers_replay_without_optimizer(monkeypatch):
    from lll import quadratic_support_bound as support

    matrices = [np.diag([1., 2.]), np.array([[1., 0.]])]
    saved = solve_support(matrices, [2., -.3], [1., 1.])

    def unnecessary(*args, **kwargs):
        raise AssertionError('a saved decomposition must not optimize')

    monkeypatch.setattr(support, 'minimize', unnecessary)
    replay = solve_support(matrices, [2., -.3], [1., 1.], multipliers=saved['multipliers'])
    assert replay['upper'] == pytest.approx(saved['upper'], abs=1e-12)
    assert replay['upper'] == pytest.approx(sum(replay['norm_terms'])+sum(replay['residual_by_coordinate']))
    assert replay['iterations'] == 0
# A scalar directional check can be verified without the numerical optimizer.
def test_affine_support_certificate_includes_observed_residual_direction():
    from lll.quadratic_support_bound import affine_upper, solve_support

    result = solve_support(([[1.]],), [1.], 10., with_certificate=True)
    shifted = affine_upper(result, group=0, offset=[-.4], radius=.8)
    assert shifted == pytest.approx(.4)


def test_galileo_map_predicts_later_minus_earlier_ranges():
    from lll.esa_galileo_joint_bound import prediction_operator

    gradients = np.array([[1., 0., 0.], [-1., 0., 0.]])
    displacement = [1., 0., 0., 4., 0., 0.]
    operator = prediction_operator([(gradients, gradients)], 2)
    np.testing.assert_allclose(operator@displacement, [3., -3.])
