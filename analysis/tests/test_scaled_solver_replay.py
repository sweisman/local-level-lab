# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.independent_bounded_solver import column_scale, solve
from lll.scaled_solver_replay import LinearControl


def test_diagonal_coordinate_change_preserves_original_box_and_target():
    charges = []
    material = dict(active_parameters=['x', 'y', 'z'], normalized_parameters=[.999, -.3, 0.],
                    jacobian=np.diag([100., .001, 0.]))
    control = LinearControl(material, lambda **kw: charges.append(kw))
    fit = solve(control, 'generated', start=[0., 0., 0.], method='centered_scaled_lbfgsb',
                maximum_calls=40, reserve=lambda **_: None, physical_step=lambda d: d.reshape(-1, 3))
    assert fit['original_gate_passed']
    assert fit['point'] == pytest.approx([1., -.3, 0.], abs=1e-6)
    assert len(charges) == fit['native_calls_actual']
    assert all(row == {'bound_calls': 1, 'bound_steps': 0} for row in charges)
    assert column_scale(control.jacobian)[-1] > 0


def test_scale_gradients_reflect_coordinate_change_without_reducing_rank():
    jacobian = np.diag([1000., .1, 2e-5])
    scale = column_scale(jacobian)
    np.testing.assert_allclose(jacobian/scale, np.eye(3))
    x = np.array([-.5, .7, .2])
    z = x * scale
    residual = jacobian @ x
    direction = np.array([.3, .02, .000001])
    value = lambda u: np.linalg.norm((jacobian/scale) @ u)**2
    central = (value(z+direction)-value(z-direction))/2
    np.testing.assert_allclose(central, (2*(jacobian.T @ residual)/scale) @ direction, rtol=1e-9)
