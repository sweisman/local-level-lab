# SPDX-License-Identifier: AGPL-3.0-or-later
"""A new local stopping candidate must not hide real descent or instability."""

import numpy as np

from lll.one_sided_stopping import verify


def check(function, derivative, *, scale=1e-6, repeat_shift=0., location=0.):
    calls = 0
    point = np.array([location])
    residual = np.array([function(location)])
    jacobian = np.array([[derivative(location)]])
    def evaluate(u, fresh=False):
        nonlocal calls
        calls += 1
        value = function(u[0]) + (repeat_shift if calls == 2 else 0.)
        return np.array([value]), np.array([[derivative(u[0])]]), 0
    physical = lambda delta:np.array([[scale*delta[0], 0., 0.]])
    return verify(point,residual,jacobian,evaluate,physical)


def test_known_exact_minimum_passes():
    result = check(lambda u:1.+u*u,lambda u:2*u)
    assert result['passed']
    assert result['baseline_repeat_equal']


def test_exact_boundary_minimum_passes():
    result = check(lambda u:u-1.,lambda u:1.,location=1.)
    assert result['passed']


def test_redundant_weak_coordinate_does_not_require_unique_parameters():
    point = np.array([.2,.2])
    residual = np.array([0.,0.])
    jacobian = np.array([[1.,1e-7],[0.,0.]])
    def evaluate(u,fresh=False):
        return np.array([u[0]+1e-7*u[1]-(.2+2e-8),0.]),jacobian.copy(),0
    result = verify(point,residual,jacobian,evaluate,
                    lambda delta:np.array([[delta[0],delta[1],0.]]))
    assert result['passed']


def test_small_linear_prediction_but_actual_cost_increase_can_pass():
    result = check(lambda u:1.+1e-6*u+.1*u*u,
                   lambda u:1e-6+.2*u)
    assert result['passed']
    assert not result['original_probe']['passed']
    assert all(row['relative_reduction'] <= 1e-8 for row in result['trials'])


def test_detectable_descent_is_rejected():
    result = check(lambda u:1.+1e-6*u-.1*u*u,
                   lambda u:1e-6-.2*u)
    assert not result['passed']
    assert result['reason'] == 'detectable_cost_decrease'


def test_physical_instability_is_rejected():
    result = check(lambda u:1.+1e-6*u+.1*u*u,
                   lambda u:1e-6+.2*u,scale=1.)
    assert not result['passed']
    assert result['reason'] == 'physical_position_unstable'


def test_changed_baseline_repeat_is_rejected():
    result = check(lambda u:1.+u*u,lambda u:2*u,repeat_shift=.01)
    assert not result['passed']
    assert result['reason'] == 'baseline_not_repeatable'


def test_nonstationary_point_is_rejected():
    result = check(lambda u:u-.2,lambda u:1.)
    assert not result['passed']
    assert result['reason'] == 'not_stationary'
